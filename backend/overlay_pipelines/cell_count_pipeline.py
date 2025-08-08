from typing import Dict, Any

import cv2
import numpy as np
from skimage import color, morphology, measure
from skimage.filters import threshold_otsu
from skimage.segmentation import watershed
from scipy import ndimage as ndi  # type: ignore
from skimage.feature import peak_local_max

from .overlay_pipeline import OverlayPipeline


class CellCountPipeline(OverlayPipeline):
    """Pipeline for detecting and counting cells in microscope images."""

    def __init__(self):
        super().__init__(
            name="cell_count",
            display_name="Cell Count Overlay",
            description="Detects and counts cells in microscope images"
        )
        self.default_params = {
            "threshold": 0.9,
            "min_size": 50,
            "max_size": 1000,
            "show_contours": True,
        }
        self.param_descriptions = {
            "threshold": "Threshold value for binary conversion (0-1)",
            "min_size": "Minimum cell size in pixels",
            "max_size": "Maximum cell size in pixels",
            "show_contours": "Whether to draw contours around detected cells",
        }

    def process(self, frame: np.ndarray, params: Dict[str, Any]) -> tuple[np.ndarray, Dict[str, Any]]:
        """
        Process a frame to detect and count brown-stained cells using LAB color, Otsu threshold, and watershed.

        Args:
            frame: The input frame to process
            params: Parameters for cell detection

        Returns:
            Tuple of (processed_frame, metrics)
        """
        # Merge default params with provided params
        p = {**self.default_params, **params}

        # Convert to RGB if needed
        if len(frame.shape) == 2:
            rgb = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
        elif frame.shape[2] == 4:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        else:
            rgb = frame.copy()
        image = rgb.astype('float32') / 255.0 if rgb.dtype == np.uint8 else rgb

        # Convert to LAB and threshold on L channel
        lab = color.rgb2lab(image)
        L = lab[:, :, 0]
        thresh = threshold_otsu(L) * p["threshold"]
        binary = L < thresh

        # Distance transform and peak local max for markers
        distance = ndi.distance_transform_edt(binary)
        if not isinstance(distance, np.ndarray):
            distance = np.array(distance)
        coords = peak_local_max(distance, footprint=np.ones((3, 3)), labels=binary, min_distance=4, exclude_border=True)
        mask = np.zeros(distance.shape, dtype=bool)
        if coords is not None and len(coords) > 0:
            mask[tuple(coords.T)] = True
        label_result = ndi.label(mask)
        if isinstance(label_result, tuple) and len(label_result) == 2:
            markers, _ = label_result
        else:
            markers = label_result
        label = watershed(-distance, markers, mask=binary)
        brown_mask = morphology.remove_small_objects(label > 0, min_size=p["min_size"])
        # Clean mask
        brown_mask = morphology.remove_small_holes(brown_mask, area_threshold=p["min_size"])
        brown_mask = morphology.remove_small_objects(brown_mask, min_size=p["min_size"])

        # Calculate stats
        total_pixels = image.shape[0] * image.shape[1]
        brown_pixels = np.sum(brown_mask)
        area_percent = (brown_pixels / total_pixels) * 100
        label_result = measure.label(brown_mask, return_num=True)
        if isinstance(label_result, tuple) and len(label_result) == 2:
            _, cell_count = label_result
        else:
            cell_count = 0

        # Draw contours if enabled
        result = frame.copy()
        if p["show_contours"]:
            # Find contours using OpenCV
            mask_uint8 = (brown_mask * 255).astype(np.uint8)
            contours, _ = cv2.findContours(mask_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(result, contours, -1, [255, 0, 0], 1)

        # Return processed frame and metrics
        metrics = {
            "cell_count": cell_count,
            "area_percent": area_percent
        }
        return result, metrics
