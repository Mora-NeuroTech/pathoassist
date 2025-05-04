from typing import Dict, Any

import cv2
import numpy as np

from .overlay_pipeline import OverlayPipeline


class FluorescencePipeline(OverlayPipeline):
    """Pipeline for detecting and measuring fluorescence in microscope images."""

    def __init__(self):
        super().__init__(
            name="fluorescence",
            display_name="Fluorescence Detection",
            description="Detects and measures fluorescence intensity in microscope images"
        )
        self.default_params = {
            "threshold": 50,
            "color_map": cv2.COLORMAP_JET,
            "alpha": 0.5,
            "show_intensity": True,
            "intensity_position": [10, 30],
            "font_scale": 1.0,
            "font_color": [255, 255, 255]  # White
        }
        self.param_descriptions = {
            "threshold": "Threshold value for fluorescence detection (0-255)",
            "color_map": "OpenCV colormap to apply (0-21)",
            "alpha": "Transparency of the overlay (0.0-1.0)",
            "show_intensity": "Whether to show the intensity value on the image",
            "intensity_position": "Position [x, y] to display the intensity",
            "font_scale": "Scale of the font for the intensity",
            "font_color": "RGB color for the intensity text"
        }

    def process(self, frame: np.ndarray, params: Dict[str, Any]) -> tuple[np.ndarray, Dict[str, Any]]:
        """
        Process a frame to detect and measure fluorescence.

        Args:
            frame: The input frame to process
            params: Parameters for fluorescence detection

        Returns:
            Tuple of (processed_frame, metrics)
        """
        # Merge default params with provided params
        p = {**self.default_params, **params}

        # Convert to grayscale if the image is color
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame.copy()

        # Create a mask for areas above the threshold
        _, mask = cv2.threshold(gray, p["threshold"], 255, cv2.THRESH_BINARY)

        # Apply colormap to the grayscale image
        colored = cv2.applyColorMap(gray, p["color_map"])

        # Create a copy of the original frame
        result = frame.copy()

        # Apply the colored overlay only to areas above the threshold
        mask_3channel = cv2.merge([mask, mask, mask])
        mask_3channel = mask_3channel.astype(bool)

        # Blend the original and colored images
        cv2.addWeighted(
            src1=colored,
            alpha=p["alpha"],
            src2=result,
            beta=1 - p["alpha"],
            gamma=0,
            dst=result,
        )

        # Calculate intensity metrics
        intensity_metrics = {}
        if np.any(mask):
            fluorescent_pixels = gray[mask > 0]
            intensity_metrics = {
                "min_intensity": int(np.min(fluorescent_pixels)),
                "max_intensity": int(np.max(fluorescent_pixels)),
                "avg_intensity": int(np.mean(fluorescent_pixels)),
                "area_percentage": float(np.sum(mask > 0) / mask.size * 100)
            }

            # Draw intensity information if enabled
            if p["show_intensity"]:
                cv2.putText(
                    result,
                    f"Avg Intensity: {intensity_metrics['avg_intensity']}",
                    tuple(p["intensity_position"]),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    p["font_scale"],
                    p["font_color"],
                    2
                )

        # Return the processed frame and metrics
        metrics = {
            "intensity": intensity_metrics,
            "area_percentage": float(np.sum(mask > 0) / mask.size * 100)
        }

        return result, metrics
