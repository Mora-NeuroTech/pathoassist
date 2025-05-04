"""
Overlay Pipelines for PathoAssist

This module defines the overlay pipeline framework and implements
various overlay pipelines for microscope image processing.
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional

from api_models import Pipeline
from .cell_count_pipeline import CellCountPipeline
from .fluorescence_pipeline import FluorescencePipeline
from .overlay_pipeline import OverlayPipeline


@dataclass
class PipelineConfig:
    """Configuration for a pipeline."""
    name: str
    params: Dict[str, Any]


# Registry of available pipelines
_PIPELINES: Dict[str, OverlayPipeline] = {}


def register_pipeline(pipeline: OverlayPipeline) -> None:
    """Register a pipeline in the registry."""
    _PIPELINES[pipeline.name] = pipeline


def get_pipeline_by_name(name: str) -> Optional[OverlayPipeline]:
    """Get a pipeline by name."""
    return _PIPELINES.get(name)


def list_available_pipelines() -> List[Pipeline]:
    """List all available pipelines."""
    return [pipeline.to_api_model() for pipeline in _PIPELINES.values()]


# Register default pipelines
register_pipeline(CellCountPipeline())
register_pipeline(FluorescencePipeline())
