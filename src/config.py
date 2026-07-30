"""
Configuration file for Tomato Disease Segmentation Project
"""
import os
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
TRAIN_DIR = PROCESSED_DATA_DIR / "train"
VAL_DIR = PROCESSED_DATA_DIR / "val"
TEST_DIR = PROCESSED_DATA_DIR / "test"

# Model directories
MODELS_DIR = PROJECT_ROOT / "src" / "models"
CHECKPOINT_DIR = PROJECT_ROOT / "checkpoints"
LOG_DIR = PROJECT_ROOT / "logs"

# Create directories if they don't exist
for directory in [TRAIN_DIR, VAL_DIR, TEST_DIR, CHECKPOINT_DIR, LOG_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Image settings
IMAGE_SIZE = 512  # Image size for model input
CHANNELS = 3  # RGB channels

# ImageNet normalization (match encoder weights from timm/torch)
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)

# Data split ratios
TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15

# Training parameters
BATCH_SIZE = 8
# U-Net++ uses more VRAM; smaller micro-batch + gradient accumulation keeps effective batch size
BATCH_SIZE_UNETPP = 2
GRAD_ACCUM_STEPS_UNETPP = 4  # 2 (micro-batch) × 4 (accum) = 8 (effective batch); requires drop_last=True
LEARNING_RATE = 1e-3
EPOCHS = 50
EARLY_STOPPING_PATIENCE = 10
WEIGHT_DECAY = 1e-5
USE_AMP = True  # mixed precision (recommended on T4 / Colab)
NUM_WORKERS = 2

# Model parameters
NUM_CLASSES = 2  # Background and foreground (leaf)
# Encoder for smp U-Net / U-Net++ (SegNet is custom CNN — this does not apply)
BACKBONE = "resnet50"  # e.g. resnet34, resnet50, mobilenet_v2

# Data augmentation parameters
AUGMENTATION_PROBABILITY = 0.5
ROTATION_LIMIT = 90
SCALE_LIMIT = 0.2
SHIFT_LIMIT = 0.1
BRIGHTNESS_LIMIT = 0.2
CONTRAST_LIMIT = 0.2

# Device
DEVICE = "cuda"  # or "cpu"

# Seeds for reproducibility
SEED = 42

# Loss function (Binary segmentation losses; not used by default, can override in train scripts)
# Options:
#   "bce_dice"         - BCEDiceLoss (default, recommended for balanced data)
#   "tversky"          - TverskyLoss (better for imbalanced foreground/background)
#   "focal_tversky"    - FocalTverskyLoss (best for very small lesions, <5% of image)
LOSS_FUNCTION = "bce_dice"  # Can be overridden in individual train scripts

# Metrics
EVAL_METRICS = ["iou", "dice", "precision", "recall", "f1"]

# Supported file extensions
SUPPORTED_IMAGE_FORMATS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}
SUPPORTED_MASK_FORMATS = {".png", ".bmp", ".tiff"}  # Lossless only for segmentation masks (avoid JPEG artifacts)

# Tomato disease classes
# NOTE: This is METADATA ONLY for documentation. 
# The pipeline is currently BINARY SEGMENTATION (disease vs background).
# Masks are binarized to 0/1 in the dataset; pixel-level multi-class is NOT supported yet.
# To enable multi-class, must: (1) remove binarize in dataset.py, (2) set NUM_CLASSES=12, 
# (3) use multi-class loss (CrossEntropyLoss), (4) modify model head.
DISEASE_CLASSES = {
    0: "Background",
    1: "Healthy",
    2: "Bacterial Spot",
    3: "Early Blight",
    4: "Late Blight",
    5: "Leaf Mold",
    6: "Septoria Leaf Spot",
    7: "Spider Mites",
    8: "Target Spot",
    9: "Tomato Yellow Leaf Curl Virus",
    10: "Tomato Mosaic Virus",
    11: "Two Spotted Spider Mite",
}

# Processed data layout: train/images, train/masks, ...
TRAIN_IMAGES_DIR = TRAIN_DIR / "images"
TRAIN_MASKS_DIR = TRAIN_DIR / "masks"
VAL_IMAGES_DIR = VAL_DIR / "images"
VAL_MASKS_DIR = VAL_DIR / "masks"
TEST_IMAGES_DIR = TEST_DIR / "images"
TEST_MASKS_DIR = TEST_DIR / "masks"

# Saved weights (must match evaluate / visualize loaders)
MODEL_SAVE_DIR = PROJECT_ROOT / "models" / "saved"
MODEL_SAVE_DIR.mkdir(parents=True, exist_ok=True)
CHECKPOINT_UNET = "best_unet_model.pth"
CHECKPOINT_SEGNET = "best_segnet_model.pth"
CHECKPOINT_UNETPP = "best_unetpp_model.pth"

# Optional: BCE pos_weight for rare foreground (None = disabled). Typical ~ neg/pos ratio.
BCE_POS_WEIGHT = None

# Default configuration for model training
DEFAULT_CONFIG = {
    "model_name": "unet",  # "unet", "segnet", "unet++"
    "encoder": BACKBONE,
    "encoder_weights": "imagenet",
    "activation": "sigmoid",
    "preprocessing_function": "torch",
}

# Inference settings
CONFIDENCE_THRESHOLD = 0.1
NMS_THRESHOLD = 0.3

# Logging
LOG_LEVEL = "INFO"
VERBOSE = True

if __name__ == "__main__":
    print("Configuration loaded successfully!")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Data directory: {DATA_DIR}")
    print(f"Image size: {IMAGE_SIZE}x{IMAGE_SIZE}")
    print(f"Batch size: {BATCH_SIZE}")
    print(f"Learning rate: {LEARNING_RATE}")
    print(f"Epochs: {EPOCHS}")
