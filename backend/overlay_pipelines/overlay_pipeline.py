from typing import Dict, Any

import numpy as np

from api_models import Pipeline


class OverlayPipeline:
    """Base class for all overlay pipelines."""

    def __init__(self, name: str, display_name: str, description: str):
        self.name = name
        self.display_name = display_name
        self.description = description
        self.default_params: Dict[str, Any] = {}
        self.param_descriptions: Dict[str, str] = {}

    def process(self, frame: np.ndarray, params: Dict[str, Any]) -> tuple[np.ndarray, Dict[str, Any]]:
        """
        Process a frame with the pipeline.

        Args:
            frame: The input frame to process
            params: Parameters for the pipeline

        Returns:
            Tuple of (processed_frame, metrics)
        """
        raise NotImplementedError("Subclasses must implement process()")

    def to_api_model(self) -> Pipeline:
        """Convert to an API model."""
        return Pipeline(
            name=self.name,
            display_name=self.display_name,
            description=self.description,
            default_params=self.default_params,
            param_descriptions=self.param_descriptions
        )
