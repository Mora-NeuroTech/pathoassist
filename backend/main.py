"""
PathoAssist Backend

This is the main entry point for the PathoAssist backend application.
It provides a FastAPI application that captures video from a microscope camera,
processes it with various overlay pipelines, and streams it to clients.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from api_models import PipelineSettings, PipelineList, ProcessedFrameData
from overlay_pipelines import list_available_pipelines, PipelineConfig
from video_capture import VideoCapture

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize video capture
video_capture = VideoCapture()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Manage the lifespan of the application."""
    logger.info("Starting video capture")
    await video_capture.start()
    yield
    logger.info("Stopping video capture")
    await video_capture.stop()


# Create FastAPI application
app = FastAPI(
    title="PathoAssist API",
    description="API for microscope video processing with overlay pipelines",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware to allow cross-origin requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the actual origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active pipeline configuration
active_pipeline_config = PipelineConfig(
    name="cell_count",
    params={"threshold": 0.9, "min_size": 50, "max_size": 1000}
)


@app.get("/api/pipelines", response_model=PipelineList)
async def get_available_pipelines():
    """Get a list of available overlay pipelines."""
    pipelines = list_available_pipelines()
    return {"pipelines": pipelines}


@app.get("/api/pipelines/active", response_model=PipelineSettings)
async def get_active_pipeline():
    """Get the currently active pipeline and its settings."""
    return {
        "name": active_pipeline_config.name,
        "params": active_pipeline_config.params
    }


@app.post("/api/pipelines/active", response_model=PipelineSettings)
async def set_active_pipeline(settings: PipelineSettings):
    """Set the active pipeline and its parameters."""
    # Validate that the pipeline exists
    if settings.name not in [p.name for p in list_available_pipelines()]:
        raise HTTPException(status_code=404, detail=f"Pipeline '{settings.name}' not found")

    # Update the active pipeline configuration
    active_pipeline_config.name = settings.name
    active_pipeline_config.params = settings.params

    logger.info(f"Active pipeline set to {settings.name} with params {settings.params}")
    return settings


@app.get("/api/stream")
async def stream_mjpeg():
    """Stream processed video as MJPEG."""
    return StreamingResponse(
        video_capture.generate_mjpeg(active_pipeline_config),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@app.get("/api/metrics", response_model=ProcessedFrameData)
async def get_frame_metrics():
    """Get metrics from the most recently processed frame."""
    metrics = await video_capture.get_latest_metrics()
    if not metrics:
        return {"timestamp": 0, "pipeline": "", "metrics": {}}
    return metrics


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
