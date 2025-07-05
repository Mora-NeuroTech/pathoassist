import os
from typing import Dict, Any
import cv2
import numpy as np
from skimage import morphology, measure
import torch
import pandas as pd
from .overlay_pipeline import OverlayPipeline

class NuclearPleomorphismPipeline(OverlayPipeline):
    """Pipeline for Nottingham - Nuclear Pleomorphism scoring."""

    def __init__(self):
        super().__init__(
            name="nuclear_pleomorphism",
            display_name="Nottingham Nuclear Pleomorphism",
            description="Segments nuclei and outputs the segmentation mask for nuclear pleomorphism scoring.",
        )
        self.default_params = {"min_size": 50, "threshold": 0.3}
        self.param_descriptions = {
            "min_size": "Minimum object size in pixels for cleaning mask.",
            "threshold": "Threshold for mask binarization (0-1).",
        }
        self.model = None
        self.device = None
        self._model_loaded = False

    def _load_model(self, model_path):
        import torch
        from torch import nn
        # Define a simple U-Net (structure as in your scratch)
        class DoubleConv(nn.Module):
            def __init__(self, in_channels, out_channels, mid_channels=None):
                super().__init__()
                if not mid_channels:
                    mid_channels = out_channels
                self.double_conv = nn.Sequential(
                    nn.Conv2d(in_channels, mid_channels, 3, padding=1, bias=False),
                    nn.BatchNorm2d(mid_channels),
                    nn.ReLU(inplace=True),
                    nn.Conv2d(mid_channels, out_channels, 3, padding=1, bias=False),
                    nn.BatchNorm2d(out_channels),
                    nn.ReLU(inplace=True)
                )
            def forward(self, x):
                return self.double_conv(x)
        class Down(nn.Module):
            def __init__(self, in_channels, out_channels):
                super().__init__()
                self.maxpool_conv = nn.Sequential(
                    nn.MaxPool2d(2),
                    DoubleConv(in_channels, out_channels)
                )
            def forward(self, x):
                return self.maxpool_conv(x)
        class Up(nn.Module):
            def __init__(self, in_channels, out_channels, bilinear=True):
                super().__init__()
                if bilinear:
                    self.up = nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True)
                    self.conv = DoubleConv(in_channels, out_channels, in_channels // 2)
                else:
                    self.up = nn.ConvTranspose2d(in_channels, in_channels // 2, 2, stride=2)
                    self.conv = DoubleConv(in_channels, out_channels)
            def forward(self, x1, x2):
                x1 = self.up(x1)
                diffY = x2.size()[2] - x1.size()[2]
                diffX = x2.size()[3] - x1.size()[3]
                x1 = torch.nn.functional.pad(x1, [diffX // 2, diffX - diffX // 2,
                                                  diffY // 2, diffY - diffY // 2])
                x = torch.cat([x2, x1], dim=1)
                return self.conv(x)
        class OutConv(nn.Module):
            def __init__(self, in_channels, out_channels):
                super().__init__()
                self.conv = nn.Conv2d(in_channels, out_channels, 1)
            def forward(self, x):
                return self.conv(x)
        class UNet(nn.Module):
            def __init__(self, n_channels, n_classes, bilinear=False):
                super().__init__()
                self.n_channels = n_channels
                self.n_classes = n_classes
                self.bilinear = bilinear
                self.inc = DoubleConv(n_channels, 64)
                self.down1 = Down(64, 128)
                self.down2 = Down(128, 256)
                self.down3 = Down(256, 512)
                factor = 2 if bilinear else 1
                self.down4 = Down(512, 1024 // factor)
                self.up1 = Up(1024, 512 // factor, bilinear)
                self.up2 = Up(512, 256 // factor, bilinear)
                self.up3 = Up(256, 128 // factor, bilinear)
                self.up4 = Up(128, 64, bilinear)
                self.outc = OutConv(64, n_classes)
            def forward(self, x):
                x1 = self.inc(x)
                x2 = self.down1(x1)
                x3 = self.down2(x2)
                x4 = self.down3(x3)
                x5 = self.down4(x4)
                x = self.up1(x5, x4)
                x = self.up2(x, x3)
                x = self.up3(x, x2)
                x = self.up4(x, x1)
                logits = self.outc(x)
                return logits
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = UNet(n_channels=3, n_classes=1, bilinear=False).to(self.device)
        state_dict = torch.load(model_path, map_location=self.device)

        if 'mask_values' in state_dict:
            mask_values = state_dict['mask_values']
            print(f"\n\n\n\n\n\n\nMask values found in state dict: {mask_values}\n\n\n\n\n\n\n")
            model_state = {k: v for k, v in state_dict.items() if k != 'mask_values'}
            self.model.load_state_dict(model_state)
        else:
            # Direct state dict
            self.model.load_state_dict(state_dict)
        self.model.eval()
        self._model_loaded = True

    def _predict_mask(self, img, thresh):
        if self.model is None or not self._model_loaded:
            raise RuntimeError("Model is not loaded. Call _load_model() before predicting.")
        patch = cv2.resize(img, (256, 256))
        x = patch.astype(np.float32) / 255.0
        x = np.transpose(x, (2, 0, 1))[None]
        x = torch.from_numpy(x).to(self.device)
        with torch.no_grad():
            logits = self.model(x)
            probs = torch.sigmoid(logits)[0, 0].cpu().numpy()
        mask = (probs > thresh).astype(np.uint8)
        mask = cv2.resize(mask, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_NEAREST)
        probs_resized = cv2.resize(probs, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_LINEAR)
        return mask, probs_resized

    def _extract_features(self, mask, image, min_area=100):
        # Convert to grayscale for intensity features
        if image.ndim == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        labeled = measure.label(mask)
        regions = measure.regionprops(labeled, intensity_image=gray)
        features = []
        for region in regions:
            if region.area >= min_area:
                area = region.area
                perimeter = region.perimeter
                circularity = 4 * np.pi * area / (perimeter ** 2) if perimeter > 0 else 0
                solidity = region.solidity
                eccentricity = region.eccentricity
                major_axis = region.major_axis_length
                minor_axis = region.minor_axis_length
                aspect_ratio = major_axis / minor_axis if minor_axis > 0 else 0
                mean_intensity = region.mean_intensity
                max_intensity = region.max_intensity
                min_intensity = region.min_intensity
                intensity_std = np.std(region.intensity_image[region.image])
                equiv_diameter = region.equivalent_diameter
                features.append({
                    'area': area,
                    'perimeter': perimeter,
                    'circularity': circularity,
                    'solidity': solidity,
                    'eccentricity': eccentricity,
                    'aspect_ratio': aspect_ratio,
                    'major_axis': major_axis,
                    'minor_axis': minor_axis,
                    'mean_intensity': mean_intensity,
                    'max_intensity': max_intensity,
                    'min_intensity': min_intensity,
                    'intensity_std': intensity_std,
                    'equiv_diameter': equiv_diameter,
                    'centroid': region.centroid
                })
        return features

    def _pleomorphism_score(self, features):
        if not features:
            return {'score': 0, 'grade': 'No nuclei detected', 'metrics': {}}
        df = pd.DataFrame(features)
        area_cv = df['area'].std() / df['area'].mean() if df['area'].mean() > 0 else 0
        diameter_cv = df['equiv_diameter'].std() / df['equiv_diameter'].mean() if df['equiv_diameter'].mean() > 0 else 0
        mean_circularity = df['circularity'].mean()
        circularity_std = df['circularity'].std()
        mean_solidity = df['solidity'].mean()
        mean_eccentricity = df['eccentricity'].mean()
        aspect_ratio_cv = df['aspect_ratio'].std() / df['aspect_ratio'].mean() if df['aspect_ratio'].mean() > 0 else 0
        intensity_variation = df['intensity_std'].mean()
        size_score = min(area_cv * 3, 1.0)
        shape_score = min((1 - mean_circularity) + circularity_std + mean_eccentricity, 1.0)
        texture_score = min(intensity_variation / 50.0, 1.0)
        composite_score = (size_score * 0.4 + shape_score * 0.4 + texture_score * 0.2) * 3
        if composite_score < 1.0:
            grade = "Grade 1 (Low pleomorphism)"
        elif composite_score < 2.0:
            grade = "Grade 2 (Moderate pleomorphism)"
        else:
            grade = "Grade 3 (High pleomorphism)"
        metrics = {
            'total_nuclei': len(features),
            'mean_area': df['area'].mean(),
            'area_cv': area_cv,
            'diameter_cv': diameter_cv,
            'mean_circularity': mean_circularity,
            'circularity_std': circularity_std,
            'mean_solidity': mean_solidity,
            'mean_eccentricity': mean_eccentricity,
            'aspect_ratio_cv': aspect_ratio_cv,
            'intensity_variation': intensity_variation,
            'size_score': size_score,
            'shape_score': shape_score,
            'texture_score': texture_score
        }
        return {
            'score': composite_score,
            'grade': grade,
            'metrics': metrics
        }

    def process(self, frame: np.ndarray, params: Dict[str, Any]) -> tuple[np.ndarray, Dict[str, Any]]:
        p = {**self.default_params, **params}
        if not self._model_loaded or self.model is None:
            model_path = os.path.join(
                os.path.dirname(__file__), "models", "nottingham_nuc_pleo.pth"
            )
            self._load_model(model_path)
        mask, prob_map = self._predict_mask(frame, p["threshold"])
        mask = morphology.remove_small_objects(mask.astype(bool), min_size=p["min_size"])
        mask = mask.astype(np.uint8)
        # Feature extraction
        features = self._extract_features(mask, frame, min_area=p["min_size"])
        pleo_result = self._pleomorphism_score(features)
        # Draw contours and centroids
        result = frame.copy()
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(result, contours, -1, (0, 255, 0), 2)
        for f in features:
            y, x = f['centroid']
            cv2.circle(result, (int(x), int(y)), 3, (255, 0, 0), -1)
        metrics = {
            "nuclei_count": len(contours),
            "mask_area": int(np.sum(mask)),
            "pleomorphism_score": pleo_result['score'],
            "pleomorphism_grade": pleo_result['grade'],
            "pleomorphism_metrics": pleo_result['metrics'],
            # "features": features,
            # "probability_map": prob_map,
            # "segmentation_mask": mask
        }
        return result, metrics
