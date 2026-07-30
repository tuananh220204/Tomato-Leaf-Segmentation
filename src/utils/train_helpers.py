"""Shared training utilities: AMP, DataLoader kwargs."""
from __future__ import annotations

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from tqdm import tqdm

from src import config


def dataloader_kwargs() -> dict:
    return {
        "num_workers": config.NUM_WORKERS,
        "pin_memory": torch.cuda.is_available(),
        "persistent_workers": config.NUM_WORKERS > 0,
    }


def train_one_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    scaler: torch.cuda.amp.GradScaler,
    use_amp: bool,
    grad_accum_steps: int = 1,
) -> float:
    """
    Train one epoch with optional gradient accumulation.
    
    Args:
        grad_accum_steps: Accumulation steps. Effective batch = micro_batch * grad_accum_steps.
                         E.g., batch_size=2, grad_accum_steps=4 → effective batch=8.
    """
    model.train()
    total = 0.0
    n = 0
    device_type = "cuda" if device.type == "cuda" else "cpu"
    amp_dtype = torch.float16 if device.type == "cuda" else torch.bfloat16

    pbar = tqdm(loader, desc="Train")
    for batch_idx, (images, masks) in enumerate(pbar):
        images = images.to(device, non_blocking=True)
        masks = masks.to(device, non_blocking=True)

        with torch.autocast(device_type=device_type, dtype=amp_dtype, enabled=use_amp):
            outputs = model(images)
            loss = criterion(outputs, masks)
            # Scale loss by accumulation steps for proper averaging
            loss = loss / grad_accum_steps

        scaler.scale(loss).backward()

        # Step optimizer only after accumulating enough gradients
        if (batch_idx + 1) % grad_accum_steps == 0:
            scaler.step(optimizer)
            scaler.update()
            optimizer.zero_grad(set_to_none=True)

        total += loss.item() * grad_accum_steps  # Un-scale for logging
        n += 1
        pbar.set_postfix({"loss": loss.item() * grad_accum_steps})

    return total / max(n, 1)


@torch.no_grad()
def validate_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
    use_amp: bool,
    iou_fn,
    dice_fn,
) -> tuple[float, float, float]:
    model.eval()
    total_loss = 0.0
    total_iou = 0.0
    total_dice = 0.0
    device_type = "cuda" if device.type == "cuda" else "cpu"
    amp_dtype = torch.float16 if device.type == "cuda" else torch.bfloat16

    for images, masks in tqdm(loader, desc="Val"):
        images = images.to(device, non_blocking=True)
        masks = masks.to(device, non_blocking=True)

        with torch.autocast(device_type=device_type, dtype=amp_dtype, enabled=use_amp):
            outputs = model(images)
            loss = criterion(outputs, masks)

        total_loss += loss.item()
        total_iou += iou_fn(outputs, masks)
        total_dice += dice_fn(outputs, masks)

    m = max(len(loader), 1)
    return total_loss / m, total_iou / m, total_dice / m
