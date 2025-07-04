from typing import Dict, Any
import cv2
import numpy as np
from skimage import morphology
import os
from .overlay_pipeline import OverlayPipeline


class NottinghamTubulePipeline(OverlayPipeline):
    """Pipeline for Nottingham - Tubular Formation scoring."""

    def __init__(self):
        super().__init__(
            name="nottingham_tubule",
            display_name="Nottingham Tubular Formation",
            description="Segments tubule regions and computes Nottingham tubule score.",
        )
        self.default_params = {"min_size": 500, "hole_size": 500, "threshold": 0.5}
        self.param_descriptions = {
            "min_size": "Minimum object size in pixels for cleaning mask.",
            "hole_size": "Maximum hole size to fill in mask.",
            "threshold": "Threshold for mask binarization (0-1).",
        }
        self.model = None
        self.device = None
        self._model_loaded = False

    def _load_model(self, model_path):
        import torch
        import segmentation_models_pytorch as smp  # type: ignore

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = smp.Unet(
            encoder_name="resnet34",
            encoder_weights=None,
            in_channels=3,
            classes=1,
            decoder_use_norm=True,
        ).to(self.device)
        state_dict = torch.load(model_path, map_location=self.device)
        self.model.load_state_dict(state_dict)
        self.model.eval()
        self._model_loaded = True

    def _min_max_norm(self, img, axis=(1, 2)):
        inp_shape = img.shape
        img_min = np.broadcast_to(img.min(axis=axis, keepdims=True), inp_shape)
        img_max = np.broadcast_to(img.max(axis=axis, keepdims=True), inp_shape)
        return (img - img_min) / (img_max - img_min + 1e-18)

    def _predict_mask(self, img, thresh):
        import torch

        if self.model is None or not self._model_loaded:
            raise RuntimeError(
                "Model is not loaded. Call _load_model() before predicting."
            )
        orig = img
        patch = cv2.resize(orig, (512, 512))
        x = patch.astype(np.float32) / 255.0
        x = np.transpose(x, (2, 0, 1))[None]
        x = self._min_max_norm(x)
        x = torch.from_numpy(x).to(self.device)
        with torch.no_grad():
            logits = self.model(x)
            probs = torch.sigmoid(logits)[0, 0].cpu().numpy()
        raw_mask = (probs > thresh).astype(np.uint8)
        return raw_mask, probs

    def process(
        self, frame: np.ndarray, params: Dict[str, Any]
    ) -> tuple[np.ndarray, Dict[str, Any]]:
        p = {**self.default_params, **params}
        if not self._model_loaded or self.model is None:
            model_path = os.path.join(
                os.path.dirname(__file__), "models", "nottingham_tubule.pth"
            )
            self._load_model(model_path)
        # Predict mask
        raw_mask, _ = self._predict_mask(frame, p["threshold"])
        # Clean mask
        clean = morphology.remove_small_objects(
            raw_mask.astype(bool), min_size=p["min_size"]
        )
        clean = morphology.remove_small_holes(clean, area_threshold=p["hole_size"])
        clean = clean.astype(np.uint8)
        # Tubule fraction and score
        tubule_area = clean.sum()
        patch_area = clean.size
        tubule_frac = tubule_area / patch_area
        if tubule_frac > 0.75:
            tubule_score = 1
        elif tubule_frac > 0.10:
            tubule_score = 2
        else:
            tubule_score = 3
        # Overlay mask on input
        clean_resized = cv2.resize(
            clean, (frame.shape[1], frame.shape[0]), interpolation=cv2.INTER_NEAREST
        )
        overlay = frame.copy()
        mask_rgb = np.zeros_like(overlay)
        mask_rgb[clean_resized == 0] = [0, 0, 0]
        alpha = 0.9
        blended = cv2.addWeighted(overlay, 1 - alpha, mask_rgb, alpha, 0)
        blended[clean_resized == 1] = overlay[clean_resized == 1]
        metrics = {
            "tubule_fraction": tubule_frac,
            "nottingham_tubule_score": tubule_score,
        }
        return blended, metrics
