"""
CareLens - Baseline Reproduction & Evaluation Script
Evaluates outputs/resnet50_augmented/best_resnet50.pt on train, valid, and test sets.
Computes overall metrics and subgroup metrics (by dataset source).
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd
from PIL import Image
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms


class CsvImageDataset(Dataset):
    def __init__(self, split_dir, transform=None):
        self.split_dir = Path(split_dir)
        self.frame = pd.read_csv(self.split_dir / "metadata.csv")
        self.image_dir = self.split_dir / "images"
        if transform is None:
            self.transform = transforms.Compose([
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor],
            )
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

    def __getitem__(self, index):
        row = self.frame.iloc[index]
        image_path = self.image_dir / row["filename"]
        image = Image.open(image_path).convert("RGB")
        return (
            self.transform(image),
            int(row["cancer"]),
            str(row["filename"]),
            str(row.get("dataset", "unknown")),
        )


def evaluate_split(model, loader, criterion, device):
    model.eval()
    total_loss = 0.0
    all_preds = []
    all_targets = []
    all_probs = []
    all_datasets = []
    all_filenames = []

    with torch.no_grad():
        for images, labels, filenames, datasets in loader:
            images = images.to(device)
            labels = labels.to(device)
            with torch.autocast(device_type=device.type, enabled=(device.type == "cuda")):
                logits = model(images)
                loss = criterion(logits, labels)
            probs = torch.softmax(logits, dim=1)[:, 1]
            preds = logits.argmax(dim=1)

            total_loss += loss.item() * labels.size(0)
            all_preds.extend(preds.cpu().tolist())
            all_targets.extend(labels.cpu().tolist())
            all_probs.extend(probs.cpu().tolist())
            all_datasets.extend(datasets)
            all_filenames.extend(filenames)

    preds_arr = np.array(all_preds)
    targets_arr = np.array(all_targets)
    probs_arr = np.array(all_probs)
    datasets_arr = np.array(all_datasets)

    def calc_metrics(p, t):
        acc = float((p == t).mean()) if len(t) > 0 else 0.0
        recalls = []
        for class_id in (0, 1):
            actual = (t == class_id)
            if actual.any():
                recalls.append(float((p[actual] == class_id).mean()))
            else:
                recalls.append(0.0)
        return {
            "count": int(len(t)),
            "accuracy": acc,
            "balanced_accuracy": float(sum(recalls) / 2),
            "sensitivity": float(recalls[1]),
            "specificity": float(recalls[0]),
        }

    overall = calc_metrics(preds_arr, targets_arr)
    overall["loss"] = float(total_loss / len(loader.dataset))

    # Subgroup breakdown by dataset
    subgroups = {}
    for d in np.unique(datasets_arr):
        mask = (datasets_arr == d)
        subgroups[d] = calc_metrics(preds_arr[mask], targets_arr[mask])

    return {
        "overall": overall,
        "subgroups": subgroups,
        "dataframe": pd.DataFrame({
            "filename": all_filenames,
            "dataset": all_datasets,
            "cancer_true": targets_arr,
            "prediction": preds_arr,
            "cancer_prob": probs_arr,
        }),
    }


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device} ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'})")

    checkpoint_path = Path("outputs/resnet50_augmented/best_resnet50.pt")
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")

    print(f"Loading checkpoint from: {checkpoint_path}")
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=True)
    epoch = checkpoint.get("epoch", "unknown")
    print(f"Checkpoint epoch: {epoch}")

    model = models.resnet50(weights=None)
    model.fc = nn.Linear(model.fc.in_features, 2)
    model.load_state_dict(checkpoint["model"])
    model.to(device)

    # Class weights from original training set (final/final_augmented/train or final/final/train)
    # Train set class counts: 6697 (class 0), 3355 (class 1)
    train_counts = np.array([6697, 3355])
    class_weights = torch.tensor(train_counts.sum() / (2 * train_counts), dtype=torch.float32, device=device)
    criterion = nn.CrossEntropyLoss(weight=class_weights)

    splits_to_eval = [
        ("test", Path("final/final/test")),
        ("valid", Path("final/final/valid")),
        ("train_augmented", Path("final/final_augmented/train")),
        ("train_original", Path("final/final/train")),
    ]

    all_results = {}
    for split_name, split_path in splits_to_eval:
        print(f"\n================ Evaluating: {split_name} ({split_path}) ================")
        dataset = CsvImageDataset(split_path)
        loader = DataLoader(dataset, batch_size=32, shuffle=False, num_workers=0)
        res = evaluate_split(model, loader, criterion, device)
        ov = res["overall"]
        print(f"Count: {ov['count']}")
        print(f"Loss: {ov['loss']:.6f}")
        print(f"Accuracy: {ov['accuracy']:.4%} ({ov['accuracy']:.6f})")
        print(f"Balanced Accuracy: {ov['balanced_accuracy']:.4%} ({ov['balanced_accuracy']:.6f})")
        print(f"Sensitivity (Cancer): {ov['sensitivity']:.4%} ({ov['sensitivity']:.6f})")
        print(f"Specificity (Benign): {ov['specificity']:.4%} ({ov['specificity']:.6f})")

        print("--- Subgroup Breakdown ---")
        for dname, dmetrics in res["subgroups"].items():
            print(f"  [{dname}] N={dmetrics['count']} | Acc={dmetrics['accuracy']:.4%} | Sens={dmetrics['sensitivity']:.4%} | Spec={dmetrics['specificity']:.4%} | BalAcc={dmetrics['balanced_accuracy']:.4%}")

        all_results[split_name] = {
            "overall": res["overall"],
            "subgroups": res["subgroups"],
        }

        # Save test detailed predictions
        if split_name == "test":
            res["dataframe"].to_csv("outputs/resnet50_augmented/eval_reproduced_test_predictions.csv", index=False)

    with open("outputs/resnet50_augmented/eval_reproduced_summary.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)

    print("\nSaved summary to outputs/resnet50_augmented/eval_reproduced_summary.json")


if __name__ == "__main__":
    main()
