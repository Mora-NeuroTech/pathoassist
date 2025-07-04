from typing import Dict, Any

import cv2
import numpy as np
from skimage import color, morphology, measure
from skimage.filters import threshold_otsu
from skimage.segmentation import watershed
from scipy import ndimage as ndi  # type: ignore
from skimage.feature import peak_local_max

from .overlay_pipeline import OverlayPipeline

class EstrogenReceptorPipeline(OverlayPipeline):
    """Pipeline for detecting estrogen receptor (ER) staining in microscope images."""

    def __init__(self):
        super().__init__(
            name="estrogen_receptor",
            display_name="Estrogen Receptor Overlay",
            description="Detects and scores estrogen receptor (ER) staining in microscope images."
        )
        self.default_params = {
            "min_size": 50,
            "max_eccentricity": 0.9,
            "show_contours": True,
            "contour_color_blue": [0, 0, 255],  # Blue
            "contour_color_brown": [255, 255, 255],  # White
        }
        self.param_descriptions = {
            "min_size": "Minimum object size in pixels",
            "max_eccentricity": "Maximum eccentricity for round objects",
            "show_contours": "Whether to draw contours around detected cells",
            "contour_color_blue": "RGB color for blue cell contours",
            "contour_color_brown": "RGB color for brown cell contours",
        }

    def process(self, frame: np.ndarray, params: Dict[str, Any]) -> tuple[np.ndarray, Dict[str, Any]]:
        p = {**self.default_params, **params}
        image = frame.astype(np.float32) / 255.0 if frame.dtype == np.uint8 else frame.copy()

        # --- Color Masking ---
        lab = color.rgb2lab(image)
        L = lab[:, :, 0]
        thresh = threshold_otsu(L) * 1.0
        binary = L < thresh
        distance = ndi.distance_transform_edt(binary)
        distance = np.asarray(distance)
        coords = peak_local_max(
            distance,
            footprint=np.ones((3, 3)),
            labels=binary,
            min_distance=4,
            exclude_border=True,
        )
        mask = np.zeros(distance.shape, dtype=bool)
        mask[tuple(coords.T)] = True
        label_result = ndi.label(mask)
        markers = label_result[0] if isinstance(label_result, tuple) else label_result
        label_brown = watershed(-distance, markers, mask=binary)
        brown_mask = morphology.remove_small_objects(label_brown, min_size=p["min_size"])
        rgb_image = (image * 255).astype("uint8")
        lower_blue = np.array([165, 154, 130])
        upper_blue = np.array([190, 170, 170])
        label_blue = cv2.inRange(rgb_image, lower_blue, upper_blue) > 0
        blue_mask = self.clean_mask(label_blue, p["min_size"])
        blue_mask = self.remove_elongated_objects(blue_mask, p["max_eccentricity"])
        blue_mask = blue_mask > 0
        brown_mask = brown_mask > 0

        # --- Statistics ---
        total_pixels = image.shape[0] * image.shape[1]
        blue_pixels = np.sum(blue_mask)
        brown_pixels = np.sum(brown_mask)
        blue_area_percent: float = (blue_pixels / total_pixels) * 100
        brown_area_percent: float = (brown_pixels / total_pixels) * 100
        blue_labels = measure.label(blue_mask)
        brown_labels = measure.label(brown_mask)
        if isinstance(blue_labels, tuple):
            blue_labels = blue_labels[0]
        if isinstance(brown_labels, tuple):
            brown_labels = brown_labels[0]
        blue_cell_count = len(np.unique(blue_labels)) - 1
        brown_cell_count = len(np.unique(brown_labels)) - 1
        Total_area = blue_area_percent + brown_area_percent
        brown_cell_percent = (brown_area_percent / Total_area) * 100 if Total_area > 0 else 0
        if brown_cell_percent < 1:
            status = 1
        elif brown_cell_percent < 10:
            status = 2
        elif brown_cell_percent < 33:
            status = 3
        elif brown_cell_percent < 66:
            status = 4
        else:
            status = 5

        # --- Intensity ---
        gray_image = color.rgb2gray(image) if len(image.shape) == 3 else image
        intensity_values = gray_image[brown_mask]
        if len(intensity_values) == 0:
            intensity_status = 1
            median = 0
        else:
            median = np.median(intensity_values)
            if median < 0.3:
                intensity_status = 3
            elif median < 0.6:
                intensity_status = 2
            else:
                intensity_status = 1
        total_marks = status + intensity_status
        if total_marks <= 2:
            outcome = "Negative"
        elif total_marks == 3:
            outcome = "Low Positive"
        else:
            outcome = "Positive"

        # --- Visualization ---
        result = frame.copy()
        if p["show_contours"]:
            self.draw_contours(result, blue_mask.astype(np.uint8), p["contour_color_blue"])
            self.draw_contours(result, brown_mask.astype(np.uint8), p["contour_color_brown"])
        # Draw score
        cv2.putText(
            result,
            f"ER Score: {total_marks} ({outcome})",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            [255, 255, 255],
            2
        )
        metrics = {
            "blue_cell_count": blue_cell_count,
            "brown_cell_count": brown_cell_count,
            "blue_area_percent": blue_area_percent,
            "brown_area_percent": brown_area_percent,
            "staining_score": status,
            "stain_intensity": float(median),
            "intensity_score": intensity_status,
            "total_score": total_marks,
            "outcome": outcome,
        }
        return result, metrics

    @staticmethod
    def clean_mask(mask, min_size):
        mask = morphology.remove_small_holes(mask, area_threshold=50)
        mask = morphology.remove_small_objects(mask, min_size=min_size)
        return mask

    @staticmethod
    def remove_elongated_objects(mask, max_eccentricity=0.9):
        labeled = measure.label(mask)
        props = measure.regionprops(labeled)
        clean_mask = np.zeros_like(mask)
        for prop in props:
            if prop.eccentricity < max_eccentricity:
                clean_mask[labeled == prop.label] = 1
        return clean_mask

    @staticmethod
    def draw_contours(image, mask, color, thickness=1):
        contours, _ = cv2.findContours(
            mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        cv2.drawContours(image, contours, -1, color, thickness)
        return image
