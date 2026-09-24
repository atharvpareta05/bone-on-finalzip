"""Create an expanded image dataset with augmented training copies."""

import argparse
import random
import shutil
from pathlib import Path

import pandas as pd
from PIL import Image, ImageEnhance, ImageOps


def augment_image(image, rng):
    if rng.random() < 0.5:
        image = ImageOps.mirror(image)
    if rng.random() < 0.25:
        image = ImageOps.flip(image)
    if rng.random() < 0.8:
        image = ImageEnhance.Brightness(image).enhance(rng.uniform(0.85, 1.15))
        image = ImageEnhance.Contrast(image).enhance(rng.uniform(0.85, 1.15))
    if rng.random() < 0.5:
        image = image.rotate(rng.uniform(-12, 12), resample=Image.Resampling.BILINEAR, fillcolor=(0, 0, 0))
    return image


def copy_split(source_root, output_root, split):
    source_split = source_root / split
    output_split = output_root / split
    output_images = output_split / "images"
    output_images.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_split / "metadata.csv", output_split / "metadata.csv")
    for image_path in (source_split / "images").iterdir():
        if image_path.is_file():
            shutil.copy2(image_path, output_images / image_path.name)


def augment_train(source_root, output_root, copies, seed):
    source_split = source_root / "train"
    output_split = output_root / "train"
    output_images = output_split / "images"
    frame = pd.read_csv(source_split / "metadata.csv")
    augmented_rows = []
    rng = random.Random(seed)

    for row in frame.itertuples(index=False):
        source_path = source_split / "images" / row.filename
        with Image.open(source_path).convert("RGB") as image:
            for copy_index in range(1, copies + 1):
                filename = f"aug_{copy_index}_{row.filename}"
                augment_image(image.copy(), rng).save(output_images / filename)
                augmented_rows.append(
                    {"filename": filename, "cancer": int(row.cancer), "dataset": row.dataset, "split": row.split}
                )

    if augmented_rows:
        output_frame = pd.concat([frame, pd.DataFrame(augmented_rows)], ignore_index=True)
        output_frame.to_csv(output_split / "metadata.csv", index=False)
    print(f"Created {len(frame)} original and {len(augmented_rows)} augmented training rows.")


def main(args):
    source_root = Path(args.data_root)
    output_root = Path(args.output_root)
    if output_root.exists():
        raise FileExistsError(f"Output already exists: {output_root}")
    output_root.mkdir(parents=True)
    for split in ("valid", "test"):
        copy_split(source_root, output_root, split)
    copy_split(source_root, output_root, "train")
    augment_train(source_root, output_root, args.copies, args.seed)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", default="final/final")
    parser.add_argument("--output-root", default="final/final_augmented")
    parser.add_argument("--copies", type=int, default=1, help="Augmented copies per original training image")
    parser.add_argument("--seed", type=int, default=42)
    main(parser.parse_args())
