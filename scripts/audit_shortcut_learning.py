"""
CareLens - Shortcut Learning & Dataset Leakage Audit Script
Phase 1 - Step 2:
1. Subgroup test performance breakdown by dataset source (BTXRD vs Dataset2)
2. Throwaway Domain Classifier (predicting source dataset A vs B)
3. Grad-CAM visual & quantitative audit for border/artifact shortcut learning
"""

import json
import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms


# ---------------------------------------------------------
# Dataset for Domain Classification & Evaluation
# ---------------------------------------------------------
class BoneDatasetSource(Dataset):
    def __init__(self, split_dir, transform=None, domain_task=False):
        self.split_dir = Path(split_dir)
        self.frame = pd.read_csv(self.split_dir / "metadata.csv")
        self.image_dir = self.split_dir / "images"
        self.domain_task = domain_task
        if transform is None:
            self.transform = transforms.Compose([
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
            ])
        else:
            self.transform = transform

    def __len__(self):
        return len(self.frame)

    def __getitem__(self, idx):
        row = self.frame.iloc[idx]
        img_path = self.image_dir / row["filename"]
        image = Image.open(img_path).convert("RGB")
        img_tensor = self.transform(image)

        cancer_label = int(row["cancer"])
        # Domain target: 0 for BTXRD, 1 for Dataset2
        domain_label = 1 if row["dataset"] == "Dataset2" else 0
        target = domain_label if self.domain_task else cancer_label

        return img_tensor, target, str(row["filename"]), str(row["dataset"]), cancer_label, domain_label


# ---------------------------------------------------------
# Subgroup Performance Breakdown of Champion ResNet-50
# ---------------------------------------------------------
def run_champion_subgroup_analysis(champion_path, test_dir, device):
    print("\n" + "="*60)
    print("STEP 1: Champion ResNet-50 Subgroup Test Breakdown (BTXRD vs Dataset2)")
    print("="*60)

    checkpoint = torch.load(champion_path, map_location=device, weights_only=True)
    model = models.resnet50(weights=None)
    model.fc = nn.Linear(model.fc.in_features, 2)
    model.load_state_dict(checkpoint["model"])
    model.to(device)
    model.eval()

    test_ds = BoneDatasetSource(test_dir, domain_task=False)
    loader = DataLoader(test_ds, batch_size=32, shuffle=False, num_workers=0)

    rows = []
    with torch.no_grad():
        for images, targets, filenames, datasets, cancer_labels, _ in loader:
            images = images.to(device)
            with torch.autocast(device_type=device.type, enabled=(device.type == "cuda")):
                logits = model(images)
            probs = torch.softmax(logits, dim=1)[:, 1].cpu().numpy()
            preds = (probs >= 0.5).astype(int)

            for fn, ds, true_c, pred, prob in zip(filenames, datasets, cancer_labels.numpy(), preds, probs):
                rows.append({
                    "filename": fn,
                    "dataset": ds,
                    "cancer_true": int(true_c),
                    "prediction": int(pred),
                    "cancer_prob": float(prob),
                })

    df = pd.DataFrame(rows)
    os.makedirs("audit_artifacts", exist_ok=True)
    df.to_csv("audit_artifacts/champion_test_subgroup_predictions.csv", index=False)

    subgroup_metrics = {}
    for ds_name in ["ALL", "BTXRD", "Dataset2"]:
        sub_df = df if ds_name == "ALL" else df[df["dataset"] == ds_name]
        y_true = sub_df["cancer_true"].values
        y_pred = sub_df["prediction"].values
        total = len(y_true)
        pos = (y_true == 1).sum()
        neg = (y_true == 0).sum()

        acc = (y_true == y_pred).mean() if total > 0 else 0.0
        sens = ((y_true == 1) & (y_pred == 1)).sum() / pos if pos > 0 else 0.0
        spec = ((y_true == 0) & (y_pred == 0)).sum() / neg if neg > 0 else 0.0
        bal_acc = (sens + spec) / 2.0

        tp = int(((y_true == 1) & (y_pred == 1)).sum())
        fp = int(((y_true == 0) & (y_pred == 1)).sum())
        tn = int(((y_true == 0) & (y_pred == 0)).sum())
        fn = int(((y_true == 1) & (y_pred == 0)).sum())

        subgroup_metrics[ds_name] = {
            "total": int(total),
            "cancer_pos": int(pos),
            "cancer_neg": int(neg),
            "accuracy": float(acc),
            "balanced_accuracy": float(bal_acc),
            "sensitivity": float(sens),
            "specificity": float(spec),
            "confusion_matrix": {"TP": tp, "FP": fp, "TN": tn, "FN": fn},
        }

        print(f"\n--- Subgroup: {ds_name} (N={total}, Pos={pos}, Neg={neg}) ---")
        print(f"Accuracy:          {acc:.4%} ({acc:.6f})")
        print(f"Balanced Accuracy: {bal_acc:.4%} ({bal_acc:.6f})")
        print(f"Sensitivity:       {sens:.4%} ({sens:.6f}) [TP={tp}, FN={fn}]")
        print(f"Specificity:       {spec:.4%} ({spec:.6f}) [TN={tn}, FP={fp}]")

    return subgroup_metrics, df


# ---------------------------------------------------------
# Throwaway Domain Classifier: Predict Dataset Source
# ---------------------------------------------------------
def train_domain_classifier(train_dir, test_dir, device, epochs=3):
    print("\n" + "="*60)
    print("STEP 2: Throwaway Domain Classifier (BTXRD vs Dataset2)")
    print("="*60)

    train_ds = BoneDatasetSource(train_dir, domain_task=True)
    test_ds = BoneDatasetSource(test_dir, domain_task=True)

    train_loader = DataLoader(train_ds, batch_size=32, shuffle=True, num_workers=0)
    test_loader = DataLoader(test_ds, batch_size=32, shuffle=False, num_workers=0)

    # Fast ResNet-18 classifier for domain signature detection
    model = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
    model.fc = nn.Linear(model.fc.in_features, 2)
    model.to(device)

    # Class balance weights for domain
    train_domain_targets = [1 if d == "Dataset2" else 0 for d in train_ds.frame["dataset"]]
    counts = np.bincount(train_domain_targets, minlength=2)
    weights = torch.tensor(counts.sum() / (2 * counts), dtype=torch.float32, device=device)
    criterion = nn.CrossEntropyLoss(weight=weights)
    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=1e-4)
    scaler = torch.amp.GradScaler("cuda", enabled=(device.type == "cuda"))

    print(f"Training Domain Classifier on {len(train_ds)} images for {epochs} epochs...")
    print(f"Train domain balance: BTXRD={counts[0]}, Dataset2={counts[1]}")

    for epoch in range(1, epochs + 1):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0

        for images, targets, _, _, _, _ in train_loader:
            images, targets = images.to(device), targets.to(device)
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast(device_type=device.type, enabled=(device.type == "cuda")):
                logits = model(images)
                loss = criterion(logits, targets)
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()

            running_loss += loss.item() * targets.size(0)
            preds = logits.argmax(dim=1)
            correct += (preds == targets).sum().item()
            total += targets.size(0)

        epoch_acc = correct / total
        epoch_loss = running_loss / total
        print(f"Epoch {epoch}/{epochs} | Domain Train Loss: {epoch_loss:.4f} | Train Acc: {epoch_acc:.4%}")

    # Evaluate on Test Set
    model.eval()
    all_preds, all_targets, all_probs = [], [], []
    with torch.no_grad():
        for images, targets, _, _, _, _ in test_loader:
            images, targets = images.to(device), targets.to(device)
            with torch.autocast(device_type=device.type, enabled=(device.type == "cuda")):
                logits = model(images)
            probs = torch.softmax(logits, dim=1)[:, 1].cpu().numpy()
            preds = logits.argmax(dim=1).cpu().numpy()
            all_preds.extend(preds)
            all_targets.extend(targets.cpu().numpy())
            all_probs.extend(probs)

    t_arr = np.array(all_targets)
    p_arr = np.array(all_preds)
    test_acc = float((t_arr == p_arr).mean())

    btxrd_rec = float(((t_arr == 0) & (p_arr == 0)).sum() / (t_arr == 0).sum())
    d2_rec = float(((t_arr == 1) & (p_arr == 1)).sum() / (t_arr == 1).sum())

    print("\nDomain Classifier Test Evaluation:")
    print(f"Overall Domain Test Accuracy: {test_acc:.4%} ({test_acc:.6f})")
    print(f"BTXRD Source Recall:         {btxrd_rec:.4%} ({(t_arr == 0).sum()} test images)")
    print(f"Dataset2 Source Recall:      {d2_rec:.4%} ({(t_arr == 1).sum()} test images)")

    return {
        "domain_test_accuracy": test_acc,
        "btxrd_source_recall": btxrd_rec,
        "dataset2_source_recall": d2_rec,
    }


# ---------------------------------------------------------
# Grad-CAM Visual & Quantitative Border Audit
# ---------------------------------------------------------
def run_gradcam_audit(champion_path, test_dir, predictions_df, device, num_samples_per_category=4):
    print("\n" + "="*60)
    print("STEP 3: Grad-CAM Visual & Peripheral Saliency Audit")
    print("="*60)

    checkpoint = torch.load(champion_path, map_location=device, weights_only=True)
    model = models.resnet50(weights=None)
    model.fc = nn.Linear(model.fc.in_features, 2)
    model.load_state_dict(checkpoint["model"])
    model.to(device)
    model.eval()

    target_layer = model.layer4[-1]

    transform_norm = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    transform_display = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
    ])

    audit_dir = Path("audit_artifacts/gradcam_audit")
    audit_dir.mkdir(parents=True, exist_ok=True)

    # Categories to audit
    df = predictions_df.copy()
    df["result"] = "Unknown"
    df.loc[(df["cancer_true"] == 1) & (df["prediction"] == 1), "result"] = "TP"
    df.loc[(df["cancer_true"] == 0) & (df["prediction"] == 0), "result"] = "TN"
    df.loc[(df["cancer_true"] == 0) & (df["prediction"] == 1), "result"] = "FP"
    df.loc[(df["cancer_true"] == 1) & (df["prediction"] == 0), "result"] = "FN"

    test_image_dir = Path(test_dir) / "images"

    audit_records = []

    # Sample cases: for each dataset and result category
    for ds in ["BTXRD", "Dataset2"]:
        for res in ["TP", "TN", "FP", "FN"]:
            sub = df[(df["dataset"] == ds) & (df["result"] == res)]
            sample_n = min(num_samples_per_category, len(sub))
            samples = sub.sample(n=sample_n, random_state=42) if sample_n > 0 else sub

            for _, row in samples.iterrows():
                fn = row["filename"]
                img_path = test_image_dir / fn
                raw_img = Image.open(img_path).convert("RGB")
                display_img = transform_display(raw_img)
                inp = transform_norm(raw_img).unsqueeze(0).to(device)

                activations = []
                gradients = []

                def fwd_hook(m, i, o):
                    activations.append(o)

                def bwd_hook(m, gi, go):
                    gradients.append(go[0])

                h_fwd = target_layer.register_forward_hook(fwd_hook)
                h_bwd = target_layer.register_full_backward_hook(bwd_hook)

                model.zero_grad()
                logits = model(inp)
                # Compute gradient with respect to predicted class (or class 1)
                target_class = int(logits.argmax(1).item())
                score = logits[0, target_class]
                score.backward()

                h_fwd.remove()
                h_bwd.remove()

                act = activations[0].detach()  # [1, 2048, 7, 7]
                grad = gradients[0].detach()   # [1, 2048, 7, 7]

                weights = grad.mean(dim=(2, 3), keepdim=True)
                cam = torch.clamp((weights * act).sum(dim=1), min=0).squeeze().cpu().numpy()
                cam = (cam - cam.min()) / (cam.max() - cam.min() + 1e-8)

                # Resize cam to 224x224
                cam_img = Image.fromarray((cam * 255).astype(np.uint8)).resize((224, 224), Image.Resampling.BILINEAR)
                cam_arr = np.array(cam_img) / 255.0

                # Peripheral mass ratio: outer 15% margin
                margin = int(224 * 0.15)  # ~33 pixels
                total_mass = cam_arr.sum()
                center_mass = cam_arr[margin:-margin, margin:-margin].sum()
                peripheral_mass = total_mass - center_mass
                peripheral_ratio = float(peripheral_mass / (total_mass + 1e-8))

                # Create audit figure
                fig, axes = plt.subplots(1, 3, figsize=(12, 4))
                axes[0].imshow(display_img)
                axes[0].set_title(f"X-ray: {fn}\nTrue:{row['cancer_true']} ({ds})")
                axes[0].axis("off")

                axes[1].imshow(cam_arr, cmap="jet")
                axes[1].set_title(f"Grad-CAM Heatmap\nPeriphery Ratio: {peripheral_ratio:.1%}")
                axes[1].axis("off")

                # Overlay
                colormap = plt.get_cmap("jet")
                heatmap_rgb = colormap(cam_arr)[:, :, :3]
                display_np = np.array(display_img) / 255.0
                overlay = (display_np * 0.55 + heatmap_rgb * 0.45)
                overlay = np.clip(overlay, 0, 1)

                axes[2].imshow(overlay)
                axes[2].set_title(f"Overlay | Pred:{row['prediction']} (P={row['cancer_prob']:.2f})\nResult: {res}")
                axes[2].axis("off")

                out_filename = f"{ds}_{res}_{fn}"
                plt.tight_layout()
                plt.savefig(audit_dir / out_filename, dpi=120)
                plt.close()

                audit_records.append({
                    "filename": fn,
                    "dataset": ds,
                    "category": res,
                    "true_cancer": int(row["cancer_true"]),
                    "pred_cancer": int(row["prediction"]),
                    "prob": float(row["cancer_prob"]),
                    "peripheral_ratio": peripheral_ratio,
                    "suspected_shortcut": bool(peripheral_ratio > 0.45),
                    "saved_plot": out_filename,
                })

    audit_summary_df = pd.DataFrame(audit_records)
    audit_summary_df.to_csv("audit_artifacts/gradcam_audit_summary.csv", index=False)

    print(f"Generated {len(audit_records)} Grad-CAM visual audits into {audit_dir}")
    print(f"Mean Peripheral Saliency Ratio: {audit_summary_df['peripheral_ratio'].mean():.2%}")
    print(f"Suspected Shortcut Activations (Ratio > 45%): {audit_summary_df['suspected_shortcut'].sum()} / {len(audit_records)}")

    return audit_summary_df


# ---------------------------------------------------------
# Main Execution
# ---------------------------------------------------------
def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Audit running on: {device}")

    champion_path = Path("outputs/resnet50_augmented/best_resnet50.pt")
    train_dir = Path("final/final/train")
    test_dir = Path("final/final/test")

    # Step 1: Subgroup performance
    subgroup_metrics, test_preds_df = run_champion_subgroup_analysis(champion_path, test_dir, device)

    # Step 2: Throwaway domain classifier
    domain_results = train_domain_classifier(train_dir, test_dir, device, epochs=3)

    # Step 3: Grad-CAM visual audit
    gradcam_audit_df = run_gradcam_audit(champion_path, test_dir, test_preds_df, device)

    # Compile complete audit data
    audit_results = {
        "subgroup_metrics": subgroup_metrics,
        "domain_classifier": domain_results,
        "gradcam_audit": {
            "total_cases_audited": len(gradcam_audit_df),
            "mean_peripheral_ratio": float(gradcam_audit_df["peripheral_ratio"].mean()),
            "suspected_shortcuts_count": int(gradcam_audit_df["suspected_shortcut"].sum()),
        },
    }

    with open("audit_artifacts/shortcut_audit_results.json", "w", encoding="utf-8") as f:
        json.dump(audit_results, f, indent=2)

    print("\nShortcut learning audit completed successfully!")
    print("Full results written to audit_artifacts/shortcut_audit_results.json")


if __name__ == "__main__":
    main()
