import os
import sys

import torch
import torch.optim as optim
from torch.cuda.amp import GradScaler
from torch.utils.data import DataLoader

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src import config
from src.data.dataset import TomatoLeafDataset
from src.data.transforms import get_train_augmentation, get_val_augmentation
from src.models.segnet import SegNet
from src.utils.metrics import BCEDiceLoss, TverskyLoss, FocalTverskyLoss, calculate_dice, calculate_iou
from src.utils.train_helpers import dataloader_kwargs, train_one_epoch, validate_epoch


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    use_amp = bool(config.USE_AMP and device.type == "cuda")
    print(f"Using device: {device}, AMP={use_amp}")

    model = SegNet(in_channels=3, out_channels=1).to(device)
    
    # Loss function selection (can switch based on data characteristics):
    # - BCEDiceLoss: default, good for balanced foreground/background
    # - TverskyLoss: better for imbalanced data (lesions << background)
    # - FocalTverskyLoss: best for very small lesions (<5% of image), hard boundaries
    criterion = BCEDiceLoss(pos_weight=config.BCE_POS_WEIGHT)
    # Alternative (uncomment to use):
    # criterion = TverskyLoss(alpha=0.5, beta=0.5)
    # criterion = FocalTverskyLoss(alpha=0.5, beta=0.5, gamma=2.0)
    optimizer = optim.Adam(model.parameters(), lr=config.LEARNING_RATE)
    scaler = GradScaler(enabled=use_amp)

    train_transform = get_train_augmentation()
    val_transform = get_val_augmentation()

    dl_kw = dataloader_kwargs()
    train_dataset = TomatoLeafDataset(
        str(config.TRAIN_IMAGES_DIR),
        str(config.TRAIN_MASKS_DIR),
        transform=train_transform,
    )
    val_dataset = TomatoLeafDataset(
        str(config.VAL_IMAGES_DIR),
        str(config.VAL_MASKS_DIR),
        transform=val_transform,
    )
    train_loader = DataLoader(
        train_dataset,
        batch_size=config.BATCH_SIZE,
        shuffle=True,
        **dl_kw,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=config.BATCH_SIZE,
        shuffle=False,
        **dl_kw,
    )

    os.makedirs(config.MODEL_SAVE_DIR, exist_ok=True)
    ckpt_path = config.MODEL_SAVE_DIR / config.CHECKPOINT_SEGNET

    best_val_iou = 0.0
    grad_accum_steps = 1  # SegNet: standard batch (no accumulation)
    print(f"Starting SegNet training (batch_size={config.BATCH_SIZE}, grad_accum={grad_accum_steps})...")
    for epoch in range(1, config.EPOCHS + 1):
        train_loss = train_one_epoch(
            model, train_loader, criterion, optimizer, device, scaler, use_amp, grad_accum_steps
        )
        val_loss, val_iou, val_dice = validate_epoch(
            model,
            val_loader,
            criterion,
            device,
            use_amp,
            calculate_iou,
            calculate_dice,
        )
        print(
            f"SegNet Epoch {epoch}: Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | "
            f"Val IoU: {val_iou:.4f} | Val Dice: {val_dice:.4f}"
        )
        if val_iou > best_val_iou:
            best_val_iou = val_iou
            torch.save(model.state_dict(), ckpt_path)
            print(f"Saved best model -> {ckpt_path}")


if __name__ == "__main__":
    main()
