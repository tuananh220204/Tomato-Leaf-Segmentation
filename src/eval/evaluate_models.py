import json
import os
from pathlib import Path

import torch
from torch.utils.data import DataLoader
from tqdm import tqdm

import sys

sys.path.append(str(Path(__file__).parent.parent.parent))

from src import config
from src.data.dataset import TomatoLeafDataset
from src.data.transforms import get_val_augmentation
from src.models.unet import build_unet_model
from src.models.segnet import SegNet
from src.models.unetplusplus import build_unetplusplus_model

def _dir_has_images(d: Path) -> bool:
    if not d.is_dir():
        return False
    for pat in ("*.png", "*.jpg", "*.jpeg"):
        if any(d.glob(pat)):
            return True
    return False


def _eval_image_mask_dirs():
    if _dir_has_images(config.TEST_IMAGES_DIR):
        return config.TEST_IMAGES_DIR, config.TEST_MASKS_DIR, "test"
    print(
        "Cảnh báo: không thấy ảnh trong tập test; dùng tập val để đánh giá. "
        "Hãy chạy split_data / chuẩn bị thư mục data/processed/test."
    )
    return config.VAL_IMAGES_DIR, config.VAL_MASKS_DIR, "val"


def calculate_metrics(preds, targets, threshold=0.5, smooth=1e-6):
    preds = torch.sigmoid(preds)
    preds = (preds > threshold).float()

    tp = (preds * targets).sum()
    fp = (preds * (1 - targets)).sum()
    fn = ((1 - preds) * targets).sum()
    tn = ((1 - preds) * (1 - targets)).sum()

    accuracy = (tp + tn + smooth) / (tp + fp + fn + tn + smooth)
    precision = (tp + smooth) / (tp + fp + smooth)
    recall = (tp + smooth) / (tp + fn + smooth)

    iou = (tp + smooth) / (tp + fp + fn + smooth)
    dice = (2.0 * tp + smooth) / (2.0 * tp + fp + fn + smooth)

    return {
        "IoU": iou.item(),
        "Dice": dice.item(),
        "Accuracy": accuracy.item(),
        "Precision": precision.item(),
        "Recall": recall.item(),
    }


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    images_dir, masks_dir, split_name = _eval_image_mask_dirs()
    print(f"Đánh giá trên: {split_name} ({images_dir})")

    val_transform = get_val_augmentation()
    test_dataset = TomatoLeafDataset(str(images_dir), str(masks_dir), transform=val_transform)
    test_loader = DataLoader(
        test_dataset,
        batch_size=config.BATCH_SIZE,
        shuffle=False,
        num_workers=config.NUM_WORKERS,
        pin_memory=torch.cuda.is_available(),
        persistent_workers=config.NUM_WORKERS > 0,
    )
    if len(test_loader) == 0:
        print("Không có batch nào để đánh giá (dataset trống).")
        return

    enc = config.BACKBONE
    models = {
        "UNet": build_unet_model(encoder_name=enc, encoder_weights=None),
        "SegNet": SegNet(),
        "UNet++": build_unetplusplus_model(encoder_name=enc, encoder_weights=None),
    }
    ckpt_files = {
        "UNet": config.CHECKPOINT_UNET,
        "SegNet": config.CHECKPOINT_SEGNET,
        "UNet++": config.CHECKPOINT_UNETPP,
    }

    results = {}
    best_iou = -1.0
    best_model_name = ""

    for name, model in models.items():
        model = model.to(device)
        weight_path = config.MODEL_SAVE_DIR / ckpt_files[name]
        if weight_path.is_file():
            model.load_state_dict(torch.load(weight_path, map_location=device))
            print(f"Loaded weights for {name} from {weight_path}")
        else:
            print(f"WARNING: No weights at {weight_path}. Using random initialization!")

        model.eval()
        epoch_metrics = {"IoU": 0.0, "Dice": 0.0, "Accuracy": 0.0, "Precision": 0.0, "Recall": 0.0}

        with torch.no_grad():
            for images, masks in tqdm(test_loader, desc=f"Evaluating {name}"):
                images = images.to(device, non_blocking=True)
                masks = masks.to(device, non_blocking=True)

                outputs = model(images)
                batch_metrics = calculate_metrics(outputs, masks)
                for k in epoch_metrics:
                    epoch_metrics[k] += batch_metrics[k]

        for k in epoch_metrics:
            epoch_metrics[k] /= len(test_loader)

        results[name] = epoch_metrics
        print(f"Results for {name}:")
        for k, v in epoch_metrics.items():
            print(f"  {k}: {v:.4f}")

        if epoch_metrics["IoU"] > best_iou:
            best_iou = epoch_metrics["IoU"]
            best_model_name = name

    print(f"\nBest Model by IoU: {best_model_name} with {best_iou:.4f}")

    best_ckpt = config.MODEL_SAVE_DIR / ckpt_files.get(best_model_name, "")
    if best_model_name and best_ckpt.is_file():
        import shutil

        shutil.copy(best_ckpt, config.PROJECT_ROOT / "best_model.pth")
        print(f"Copied weights to {config.PROJECT_ROOT / 'best_model.pth'}")

    os.makedirs(config.PROJECT_ROOT / "docs" / "visualizations", exist_ok=True)
    out_json = config.PROJECT_ROOT / "docs" / "visualizations" / "evaluation_results.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)


if __name__ == "__main__":
    main()
