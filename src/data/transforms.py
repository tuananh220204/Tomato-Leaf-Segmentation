"""
Albumentations pipelines for image + mask (segmentation).
CustomCLAHE runs on the image only; geometric transforms stay synced with the mask.
"""
import cv2
import numpy as np
from PIL import Image
import albumentations as A
from albumentations.pytorch import ToTensorV2

from src import config


def _clahe_rgb_numpy(image: np.ndarray, **kwargs) -> np.ndarray:
    """Apply CLAHE on L channel in LAB space. image: uint8 HWC RGB."""
    if image.dtype != np.uint8:
        image = np.clip(image, 0, 255).astype(np.uint8)
    if image.ndim == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    elif image.shape[2] == 4:
        image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)

    lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
    l_ch, a_ch, b_ch = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_eq = clahe.apply(l_ch)
    lab_eq = cv2.merge([l_eq, a_ch, b_ch])
    return cv2.cvtColor(lab_eq, cv2.COLOR_LAB2RGB)


class CustomCLAHE:
    """Torchvision-style callable for PIL/numpy image (single image, no mask)."""

    def __init__(self, clip_limit: float = 2.0, tile_grid_size: tuple = (8, 8)):
        self.clip_limit = clip_limit
        self.tile_grid_size = tile_grid_size

    def __call__(self, img) -> Image.Image:
        if isinstance(img, Image.Image):
            arr = np.array(img)
        else:
            arr = np.asarray(img)
        clahe = cv2.createCLAHE(clipLimit=self.clip_limit, tileGridSize=self.tile_grid_size)
        if arr.dtype != np.uint8:
            arr = np.clip(arr, 0, 255).astype(np.uint8)
        if arr.ndim == 2:
            arr = cv2.cvtColor(arr, cv2.COLOR_GRAY2RGB)
        elif arr.shape[2] == 4:
            arr = cv2.cvtColor(arr, cv2.COLOR_RGBA2RGB)
        lab = cv2.cvtColor(arr, cv2.COLOR_RGB2LAB)
        l_ch, a_ch, b_ch = cv2.split(lab)
        l_eq = clahe.apply(l_ch)
        lab_eq = cv2.merge([l_eq, a_ch, b_ch])
        out = cv2.cvtColor(lab_eq, cv2.COLOR_LAB2RGB)
        return Image.fromarray(out)


def get_train_augmentation(
    image_size: int | None = None,
    *,
    use_clahe: bool = True,
    clahe_prob: float = 0.3,
) -> A.Compose:
    """Train: spatial aug on image+mask, color only on image, ImageNet normalize, tensors."""
    h = image_size or config.IMAGE_SIZE
    transforms_list = []
    if use_clahe:
        transforms_list.append(A.Lambda(image=_clahe_rgb_numpy, p=clahe_prob))
    transforms_list.extend(
        [
            A.Resize(h, h),
            A.HorizontalFlip(p=0.5),
            A.VerticalFlip(p=0.5),
            A.RandomRotate90(p=0.5),
            A.ColorJitter(brightness=0.1, contrast=0.1, saturation=0.1, hue=0.05, p=0.3),
            A.Normalize(mean=config.IMAGENET_MEAN, std=config.IMAGENET_STD),
            ToTensorV2(),
        ]
    )
    return A.Compose(transforms_list)


def get_val_augmentation(image_size: int | None = None) -> A.Compose:
    h = image_size or config.IMAGE_SIZE
    return A.Compose(
        [
            A.Resize(h, h),
            A.Normalize(mean=config.IMAGENET_MEAN, std=config.IMAGENET_STD),
            ToTensorV2(),
        ]
    )


def get_train_transforms():
    """
    Backward-compatible name: returns Albumentations Compose (image+mask API),
    not torchvision.Compose.
    """
    return get_train_augmentation()
