from typing import Dict, Any

import cv2
import numpy as np

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
            "threshold": 128,
            "min_size": 50,
            "max_size": 1000,
            "show_contours": True,
            "contour_color": [0, 255, 0],  # Green
            "show_count": True,
            "count_position": [10, 30],
            "font_scale": 1.0,
            "font_color": [255, 255, 255]  # White
        }
        self.param_descriptions = {
            "threshold": "Threshold value for binary conversion (0-255)",
            "min_size": "Minimum cell size in pixels",
            "max_size": "Maximum cell size in pixels",
            "show_contours": "Whether to draw contours around detected cells",
            "contour_color": "RGB color for contours",
            "show_count": "Whether to show the cell count on the image",
            "count_position": "Position [x, y] to display the count",
            "font_scale": "Scale of the font for the count",
            "font_color": "RGB color for the count text"
        }

    def process(self, frame: np.ndarray, params: Dict[str, Any]) -> tuple[np.ndarray, Dict[str, Any]]:
        """
        Process a frame to detect and count cells.

        Args:
            frame: The input frame to process
            params: Parameters for cell detection

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

        # Apply a threshold to create a binary image
        _, binary = cv2.threshold(gray, p["threshold"], 255, cv2.THRESH_BINARY)

        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Filter contours by size
        valid_contours = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if p["min_size"] <= area <= p["max_size"]:
                valid_contours.append(contour)

        # Create a copy of the original frame for drawing
        result = frame.copy()

        # Draw contours if enabled
        if p["show_contours"]:
            cv2.drawContours(
                result,
                valid_contours,
                -1,
                p["contour_color"],
                2
            )

        # Draw cell count if enabled
        cell_count = len(valid_contours)
        if p["show_count"]:
            cv2.putText(
                result,
                f"Cell Count: {cell_count}",
                tuple(p["count_position"]),
                cv2.FONT_HERSHEY_SIMPLEX,
                p["font_scale"],
                p["font_color"],
                2
            )

        # Calculate size statistics
        sizes = [cv2.contourArea(contour) for contour in valid_contours]
        size_metrics = {}
        if sizes:
            size_metrics = {
                "min_size": min(sizes),
                "max_size": max(sizes),
                "avg_size": sum(sizes) / len(sizes)
            }

        # Return the processed frame and metrics
        metrics = {
            "cell_count": cell_count,
            "sizes": size_metrics
        }

        return result, metrics
