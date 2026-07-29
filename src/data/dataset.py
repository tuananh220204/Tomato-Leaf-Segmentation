import os
import cv2
import torch
from torch.utils.data import Dataset
import numpy as np

class TomatoLeafDataset(Dataset):
    def __init__(self, images_dir, masks_dir, transform=None):
        self.images_dir = images_dir
        self.masks_dir = masks_dir
        self.transform = transform
        self.images = [f for f in os.listdir(images_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        img_name = self.images[idx]
        img_path = os.path.join(self.images_dir, img_name)
        mask_path = os.path.join(self.masks_dir, img_name) # Assuming mask has same name

        # Read image and mask supporting unicode paths
        image = cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), cv2.IMREAD_COLOR)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        mask = cv2.imdecode(np.fromfile(mask_path, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
        # Binarize mask
        _, mask = cv2.threshold(mask, 127, 1, cv2.THRESH_BINARY)
        mask = mask.astype(np.float32)

        if self.transform:
            # Albumentations expects uint8 mask for clean resize/interpolation semantics
            mask_u8 = (mask * 255.0).clip(0, 255).astype(np.uint8)
            augmented = self.transform(image=image, mask=mask_u8)
            image = augmented["image"]
            mask = augmented["mask"]

        if not isinstance(image, torch.Tensor):
            image = torch.from_numpy(image.transpose(2, 0, 1)).float() / 255.0

        if not isinstance(mask, torch.Tensor):
            mask = torch.from_numpy(mask).unsqueeze(0).float()
        else:
            mask = mask.float()
            if mask.ndim == 2:
                mask = mask.unsqueeze(0)
            elif mask.ndim == 3 and mask.shape[0] != 1:
                mask = mask[:1]

        mask = (mask > 0.5).float()

        return image, mask
