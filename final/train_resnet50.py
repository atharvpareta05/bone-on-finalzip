"""Train an ImageNet-pretrained ResNet-50 on the CSV-described dataset."""

import argparse
import copy
import json
import random
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from PIL import Image
from torch import nn
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms


class CsvImageDataset(Dataset):
    def __init__(self, split_dir, train=False):
        self.split_dir = Path(split_dir)
        self.frame = pd.read_csv(self.split_dir / "metadata.csv")
        self.image_dir = self.split_dir / "images"
        self.transform = self._make_transform(train)

    @staticmethod
    def _make_transform(train):
        if train:
            return transforms.Compose([
                transforms.RandomResizedCrop(224, scale=(0.8, 1.0)),
                transforms.RandomHorizontalFlip(),
                transforms.RandomRotation(10),
                transforms.ColorJitter(brightness=0.15, contrast=0.15),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
            ])
        return transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ])

    def __len__(self):
        return len(self.frame)

    def __getitem__(self, index):
        row = self.frame.iloc[index]
        image = Image.open(self.image_dir / row["filename"]).convert("RGB")
        return self.transform(image), int(row["cancer"]), row["filename"]


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


def make_loader(dataset, batch_size, workers, shuffle):
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=workers,
        pin_memory=torch.cuda.is_available(),
        persistent_workers=workers > 0,
    )


def run_epoch(model, loader, criterion, device, optimizer=None, scaler=None):
    training = optimizer is not None
    model.train(training)
    total_loss = 0.0
    predictions = []
    targets = []

    for images, labels, _ in loader:
        images, labels = images.to(device), labels.to(device)
        if training:
            optimizer.zero_grad(set_to_none=True)
        with torch.set_grad_enabled(training):
            with torch.autocast(device_type=device.type, enabled=device.type == "cuda"):
                logits = model(images)
                loss = criterion(logits, labels)
            if training:
                if scaler is not None:
                    scaler.scale(loss).backward()
                    scaler.step(optimizer)
                    scaler.update()
                else:
                    loss.backward()
                    optimizer.step()
        total_loss += loss.item() * labels.size(0)
        predictions.extend(logits.argmax(1).detach().cpu().tolist())
        targets.extend(labels.cpu().tolist())

    predictions = np.asarray(predictions)
    targets = np.asarray(targets)
    accuracy = float((predictions == targets).mean())
    recalls = []
    for class_id in (0, 1):
        actual = targets == class_id
        recalls.append(float((predictions[actual] == class_id).mean()) if actual.any() else 0.0)
    return {
        "loss": total_loss / len(loader.dataset),
        "accuracy": accuracy,
        "balanced_accuracy": sum(recalls) / 2,
        "sensitivity": recalls[1],
        "specificity": recalls[0],
    }


def main(args):
    set_seed(args.seed)
    data_root = Path(args.data_root)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    train_set = CsvImageDataset(data_root / "train", train=True)
    valid_set = CsvImageDataset(data_root / "valid")
    test_set = CsvImageDataset(data_root / "test")
    train_loader = make_loader(train_set, args.batch_size, args.workers, True)
    valid_loader = make_loader(valid_set, args.batch_size, args.workers, False)
    test_loader = make_loader(test_set, args.batch_size, args.workers, False)

    class_counts = np.bincount(train_set.frame["cancer"].astype(int), minlength=2)
    class_weights = torch.tensor(class_counts.sum() / (2 * class_counts), dtype=torch.float32, device=device)

    weights = models.ResNet50_Weights.IMAGENET1K_V2
    model = models.resnet50(weights=weights)
    model.fc = nn.Linear(model.fc.in_features, 2)
    model.to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="max", factor=0.3, patience=2
    )
    scaler = torch.amp.GradScaler("cuda", enabled=device.type == "cuda")

    best_score = -1.0
    best_state = None
    stale_epochs = 0
    for epoch in range(1, args.epochs + 1):
        train_metrics = run_epoch(model, train_loader, criterion, device, optimizer, scaler)
        valid_metrics = run_epoch(model, valid_loader, criterion, device)
        scheduler.step(valid_metrics["balanced_accuracy"])
        score = valid_metrics["balanced_accuracy"]
        print(
            f"Epoch {epoch:02d}/{args.epochs} | "
            f"train loss {train_metrics['loss']:.4f} | "
            f"valid loss {valid_metrics['loss']:.4f} | "
            f"valid balanced accuracy {score:.4f} | "
            f"sensitivity {valid_metrics['sensitivity']:.4f} | "
            f"specificity {valid_metrics['specificity']:.4f}"
        )
        if score > best_score:
            best_score = score
            stale_epochs = 0
            best_state = copy.deepcopy(model.state_dict())
            torch.save(
                {"model": best_state, "class_names": ["no_cancer", "cancer"], "epoch": epoch},
                output_dir / "best_resnet50.pt",
            )
        else:
            stale_epochs += 1
            if stale_epochs >= args.patience:
                print("Early stopping.")
                break

    if best_state is not None:
        model.load_state_dict(best_state)
    else:
        print("Warning: No best state was saved during training. Keeping final epoch weights.")
    test_metrics = run_epoch(model, test_loader, criterion, device)
    print(f"Test metrics: {json.dumps(test_metrics)}")
    with (output_dir / "metrics.json").open("w", encoding="utf-8") as file:
        json.dump({"best_validation": best_score, "test": test_metrics}, file, indent=2)

    model.eval()
    rows = []
    with torch.no_grad():
        for images, _, filenames in test_loader:
            probabilities = model(images.to(device)).softmax(1)[:, 1].cpu().tolist()
            rows.extend({"filename": name, "cancer_probability": probability, "prediction": int(probability >= 0.5)}
                        for name, probability in zip(filenames, probabilities))
    pd.DataFrame(rows).to_csv(output_dir / "test_predictions.csv", index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", default="final/final", help="Folder containing train, valid, and test")
    parser.add_argument("--output-dir", default="outputs/resnet50")
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--patience", type=int, default=5)
    parser.add_argument("--workers", type=int, default=0, help="Use 0 on Windows if multiprocessing causes issues")
    parser.add_argument("--seed", type=int, default=42)
    main(parser.parse_args())