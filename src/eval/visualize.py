import json
import os
import random
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import torch

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


def _viz_image_mask_dirs():
    if _dir_has_images(config.TEST_IMAGES_DIR):
        return config.TEST_IMAGES_DIR, config.TEST_MASKS_DIR
    return config.VAL_IMAGES_DIR, config.VAL_MASKS_DIR


def plot_bar_charts():
    results_path = config.PROJECT_ROOT / "docs" / "visualizations" / "evaluation_results.json"
    if not results_path.is_file():
        print("evaluation_results.json not found, skipping bar charts.")
        return

    with open(results_path, "r", encoding="utf-8") as f:
        results = json.load(f)

    models = list(results.keys())
    ious = [results[m]["IoU"] for m in models]
    dices = [results[m]["Dice"] for m in models]

    x = np.arange(len(models))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))
    rects1 = ax.bar(x - width / 2, ious, width, label="IoU")
    rects2 = ax.bar(x + width / 2, dices, width, label="Dice")

    ax.set_ylabel("Scores")
    ax.set_title("IoU and Dice Comparison by Model")
    ax.set_xticks(x)
    ax.set_xticklabels(models)
    ax.legend()

    ax.bar_label(rects1, padding=3, fmt="%.3f")
    ax.bar_label(rects2, padding=3, fmt="%.3f")

    fig.tight_layout()
    out = config.PROJECT_ROOT / "docs" / "visualizations" / "metrics_comparison_bar.png"
    plt.savefig(out)
    print(f"Saved {out}")


def plot_predictions():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    test_images_dir, test_masks_dir = _viz_image_mask_dirs()
    val_transform = get_val_augmentation()
    test_dataset = TomatoLeafDataset(
        str(test_images_dir), str(test_masks_dir), transform=val_transform
    )

    enc = config.BACKBONE
    models = {
        "UNet": build_unet_model(encoder_name=enc, encoder_weights=None).to(device),
        "SegNet": SegNet().to(device),
        "UNet++": build_unetplusplus_model(encoder_name=enc, encoder_weights=None).to(device),
    }
    ckpt_files = {
        "UNet": config.CHECKPOINT_UNET,
        "SegNet": config.CHECKPOINT_SEGNET,
        "UNet++": config.CHECKPOINT_UNETPP,
    }

    for name, model in models.items():
        wp = config.MODEL_SAVE_DIR / ckpt_files[name]
        if wp.is_file():
            model.load_state_dict(torch.load(wp, map_location=device))
        model.eval()

    n = len(test_dataset)
    if n == 0:
        print("Dataset trống, bỏ qua plot_predictions.")
        return
    k = min(2, n)
    indices = random.sample(range(n), k)

    fig, axes = plt.subplots(k, 5, figsize=(20, 4 * k))
    if k == 1:
        axes = np.expand_dims(axes, axis=0)
    fig.suptitle("Tomato Leaf Segmentation Predictions", fontsize=16)

    mean = np.array(config.IMAGENET_MEAN)
    std = np.array(config.IMAGENET_STD)

    for idx, sample_idx in enumerate(indices):
        img_tensor, mask_tensor = test_dataset[sample_idx]
        img_tensor = img_tensor.unsqueeze(0).to(device, non_blocking=True)

        orig_img = img_tensor.squeeze().cpu().numpy().transpose(1, 2, 0)
        orig_img = std * orig_img + mean
        orig_img = np.clip(orig_img, 0, 1)

        axes[idx, 0].imshow(orig_img)
        axes[idx, 0].set_title("Input (denorm)")
        axes[idx, 0].axis("off")

        axes[idx, 1].imshow(mask_tensor.numpy().squeeze(), cmap="gray")
        axes[idx, 1].set_title("Ground Truth")
        axes[idx, 1].axis("off")

        col = 2
        for name, model in models.items():
            with torch.no_grad():
                output = model(img_tensor)
                output = torch.sigmoid(output).squeeze()
                pred_mask = (output > 0.5).cpu().numpy()

            axes[idx, col].imshow(pred_mask, cmap="gray")
            axes[idx, col].set_title(f"{name} Pred")
            axes[idx, col].axis("off")
            col += 1

    plt.tight_layout()
    out = config.PROJECT_ROOT / "docs" / "visualizations" / "prediction_samples.png"
    plt.savefig(out)
    print(f"Saved {out}")


if __name__ == "__main__":
    plot_bar_charts()
    plot_predictions()
