"""
API Models for PathoAssist

This module defines Pydantic models used for API request and response validation.
"""

from typing import Dict, List, Any
from pydantic import BaseModel, Field


class Pipeline(BaseModel):
    """Model representing an overlay pipeline."""
    name: str = Field(..., description="Unique identifier for the pipeline")
    display_name: str = Field(..., description="Human-readable name for the pipeline")
    description: str = Field(..., description="Description of what the pipeline does")
    default_params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Default parameters for the pipeline"
    )
    param_descriptions: Dict[str, str] = Field(
        default_factory=dict,
        description="Descriptions for each parameter"
    )


class PipelineList(BaseModel):
    """Model representing a list of available pipelines."""
    pipelines: List[Pipeline] = Field(
        default_factory=list,
        description="List of available overlay pipelines"
    )


class PipelineSettings(BaseModel):
    """Model representing pipeline settings."""
    name: str = Field(..., description="Name of the pipeline to use")
    params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters for the pipeline"
    )


class ProcessedFrameData(BaseModel):
    """Model representing data extracted from a processed frame."""
    timestamp: float = Field(..., description="Timestamp when the frame was processed")
    pipeline: str = Field(..., description="Name of the pipeline used")
    metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metrics extracted by the pipeline (e.g., cell count)"
    )