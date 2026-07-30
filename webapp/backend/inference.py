import os
import io
import sys
import time
import base64
from pathlib import Path
from typing import Dict, Any, List

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import cv2
from PIL import Image
import torch
import torchvision.transforms as T

from src import config
from src.models.unet import build_unet_model
from src.models.unetplusplus import build_unetplusplus_model
from src.models.segnet import SegNet


def _pil_to_base64(img: Image.Image, fmt: str = "PNG") -> str:
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    b = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/{fmt.lower()};base64,{b}"


class TomatoDiseaseSegmenter:
    """Inference manager that loads three segmentation models and runs them on a single preprocessed image.
    """

    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Paths: use project config CHECKPOINT_DIR / MODEL_SAVE_DIR
        project_root = config.PROJECT_ROOT
        saved_dir = config.MODEL_SAVE_DIR

        self.checkpoints = {
            "unet": saved_dir / config.CHECKPOINT_UNET,
            "segnet": saved_dir / config.CHECKPOINT_SEGNET,
            "unetpp": saved_dir / config.CHECKPOINT_UNETPP,
        }

        # Build models
        try:
            self.models: Dict[str, torch.nn.Module] = {}

            self.models["unet"] = build_unet_model(in_channels=3, classes=1)
            self.models["unetpp"] = build_unetplusplus_model(in_channels=3, classes=1)
            self.models["segnet"] = SegNet(in_channels=3, out_channels=1)

            # Load weights if present
            for name, model in self.models.items():
                ckpt_path = self.checkpoints.get(name)
                if ckpt_path and ckpt_path.exists():
                    try:
                        state = torch.load(str(ckpt_path), map_location=self.device)
                        if isinstance(state, dict) and "model_state_dict" in state:
                            model.load_state_dict(state["model_state_dict"])
                        else:
                            model.load_state_dict(state)
                        print(f"[INFO] Loaded checkpoint for {name} from {ckpt_path}")
                    except Exception as e:
                        print(f"[WARN] Failed loading checkpoint for {name}: {e}")
                else:
                    print(f"[WARN] Checkpoint not found for {name}: {ckpt_path}")

                model.to(self.device)
                model.eval()

        except Exception as e:
            print("[ERROR] Failed to initialize models:", e)

        # Preprocessing transform
        self.preprocess = T.Compose([
            T.Resize((config.IMAGE_SIZE, config.IMAGE_SIZE)),
            T.ToTensor(),
            T.Normalize(mean=config.IMAGENET_MEAN, std=config.IMAGENET_STD)
        ])

    def _prepare(self, image_bytes: bytes) -> Dict[str, Any]:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        original_b64 = _pil_to_base64(img, fmt="PNG")
        resized = img.resize((config.IMAGE_SIZE, config.IMAGE_SIZE), resample=Image.BILINEAR)
        tensor = self.preprocess(img).unsqueeze(0).to(self.device)

        return {
            "pil_original": img,
            "original_base64": original_b64,
            "resized_pil": resized,
            "tensor": tensor
        }

    def _postprocess_mask(self, prob_map: np.ndarray, resized_pil: Image.Image, threshold: float) -> Dict[str, Any]:
        mask_bin = (prob_map >= threshold).astype(np.uint8)

        try:
            img_cv = cv2.cvtColor(np.array(resized_pil), cv2.COLOR_RGB2BGR)
            h, w = img_cv.shape[:2]
            mask = np.zeros((h, w), np.uint8)
            rect = (int(w * 0.05), int(h * 0.05), int(w * 0.90), int(h * 0.90))
            bgdModel = np.zeros((1, 65), np.float64)
            fgdModel = np.zeros((1, 65), np.float64)

            cv2.grabCut(img_cv, mask, rect, bgdModel, fgdModel, 3, cv2.GC_INIT_WITH_RECT)
            leaf_mask = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 1, 0).astype(np.uint8)
            
            if leaf_mask.sum() < (h * w * 0.05):
                leaf_mask = np.ones_like(mask_bin)
        except Exception as e:
            print(f"[WARN] GrabCut background removal failed: {e}. Falling back to full image.")
            leaf_mask = np.ones_like(mask_bin)

        leaf_pixel_count = int(leaf_mask.sum())
        if leaf_pixel_count == 0:
            leaf_pixel_count = mask_bin.size
            leaf_mask = np.ones_like(mask_bin)

        refined_disease_mask = mask_bin & leaf_mask
        disease_pixel_count = int(refined_disease_mask.sum())
        pct = float((disease_pixel_count / leaf_pixel_count) * 100.0)

        # Tính độ tin cậy thay thế cho IoU tĩnh
        confidence_score = float(prob_map[refined_disease_mask == 1].mean()) if disease_pixel_count > 0 else float(prob_map.mean())

        mask_display = (refined_disease_mask * 255).astype(np.uint8)
        mask_img = Image.fromarray(mask_display)

        bg = np.array(resized_pil).astype(np.uint8)
        overlay = bg.copy()
        alpha = 0.5
        red = np.array([255, 0, 0], dtype=np.uint8)
        
        disease_idx = refined_disease_mask.astype(bool)
        overlay[disease_idx] = (overlay[disease_idx].astype(float) * (1 - alpha) + red * alpha).astype(np.uint8)
        overlay_img = Image.fromarray(overlay)

        return {
            "mask_b64": _pil_to_base64(mask_img, fmt="PNG"),
            "overlay_b64": _pil_to_base64(overlay_img, fmt="PNG"),
            "infection_percent": round(pct, 2),
            "confidence_score": round(confidence_score, 4)
        }

    def predict_all(self, image_bytes: bytes, preferred_model: str = "unet", threshold: float | None = None) -> Dict[str, Any]:
        """Run all three models on the input image bytes and return structured results."""
        threshold = threshold if threshold is not None else config.CONFIDENCE_THRESHOLD

        start = time.time()
        prep = self._prepare(image_bytes)
        tensor = prep["tensor"]
        resized_pil = prep["resized_pil"]

        model_results: List[Dict[str, Any]] = []

        for name, model in self.models.items():
            t0 = time.time()
            try:
                with torch.no_grad():
                    out = model(tensor)
                    if isinstance(out, (tuple, list)):
                        out = out[0]
                    out = out.squeeze(0).squeeze(0)
                    probs = torch.sigmoid(out).cpu().numpy()
            except Exception:
                probs = np.zeros((config.IMAGE_SIZE, config.IMAGE_SIZE), dtype=float)

            meta = self._postprocess_mask(probs, resized_pil, threshold)
            elapsed_ms = int((time.time() - t0) * 1000)

            model_results.append({
                "model_name": name,
                "model_type": name,
                "model_label": {"unet": "U-Net", "unetpp": "U-Net++", "segnet": "SegNet"}.get(name, name.upper()),
                "image_mask_base64": meta["mask_b64"],
                "image_overlay_base64": meta["overlay_b64"],
                "inference_time_ms": elapsed_ms,
                "infection_area_percent": meta["infection_percent"],
                "benchmark_iou": meta["confidence_score"]
            })

        total_ms = int((time.time() - start) * 1000)

        best_res = next((m for m in model_results if m["model_name"] == preferred_model), model_results[0])
        
        labels_map = {"unet": "U-Net", "unetpp": "U-Net++", "segnet": "SegNet"}
        best_model_label = labels_map.get(best_res["model_name"], best_res["model_name"].upper())

        return {
            "infection_area_percent": best_res["infection_area_percent"],
            "image_original_base64": prep["original_base64"],
            "image_mask_base64": best_res["image_mask_base64"],
            "image_overlay_base64": best_res["image_overlay_base64"],
            "best_model": best_res["model_name"],
            "best_model_label": best_model_label,
            "selection_basis": "User selected" if preferred_model else "Default",
            "model_results": model_results,
            "best_model_inference_time_ms": best_res["inference_time_ms"],
            "total_inference_time_ms": total_ms
        }