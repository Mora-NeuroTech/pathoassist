"""
Video Capture for PathoAssist

This module handles video capture from a microscope camera and provides
methods for streaming the processed video to clients.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, AsyncGenerator, List

import cv2
import numpy as np

from overlay_pipelines import PipelineConfig, get_pipeline_by_name

logger = logging.getLogger(__name__)


class VideoCapture:
    """
    Handles video capture from a microscope camera and processes frames
    with overlay pipelines.
    """

    def __init__(self, camera_id: int = 0, width: int = 640, height: int = 480, fps: int = 30):
        """
        Initialize the video capture.

        Args:
            camera_id: ID of the camera to use
            width: Width of the captured frames
            height: Height of the captured frames
            fps: Frames per second to capture
        """
        self.camera_id = camera_id
        self.width = width
        self.height = height
        self.fps = fps
        self.cap = None
        self.is_running = False
        self.current_frame = None
        self.frame_lock = asyncio.Lock()
        self.last_frame_time = 0
        self.latest_metrics = {}
        self.metrics_lock = asyncio.Lock()

        # For testing without a camera
        self.use_test_pattern = False
        self.test_pattern_index = 0
        self.test_patterns = self._create_test_patterns()

    def _create_test_patterns(self) -> List[np.ndarray]:
        """Create test patterns for use when no camera is available."""
        patterns = []

        # Pattern 1: Grid with circles (simulating cells)
        grid = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        for y in range(50, self.height, 100):
            for x in range(50, self.width, 100):
                cv2.circle(grid, (x, y), 20, (200, 200, 200), -1)
                cv2.circle(grid, (x, y), 20, (100, 100, 100), 2)
        patterns.append(grid)

        # Pattern 2: Fluorescence-like pattern
        fluorescence = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        for y in range(50, self.height, 100):
            for x in range(50, self.width, 100):
                brightness = np.random.randint(100, 255)
                cv2.circle(fluorescence, (x, y), 30, (0, brightness, 0), -1)
        patterns.append(fluorescence)

        # Pattern 3: Cell cluster pattern
        clusters = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        for _ in range(5):
            center_x = np.random.randint(100, self.width - 100)
            center_y = np.random.randint(100, self.height - 100)
            for _ in range(20):
                offset_x = np.random.randint(-80, 80)
                offset_y = np.random.randint(-80, 80)
                x = center_x + offset_x
                y = center_y + offset_y
                size = np.random.randint(10, 25)
                cv2.circle(clusters, (x, y), size, (200, 200, 200), -1)
                cv2.circle(clusters, (x, y), size, (100, 100, 100), 1)
        patterns.append(clusters)

        return patterns

    async def start(self):
        """Start the video capture."""
        if self.is_running:
            return

        try:
            self.cap = cv2.VideoCapture(self.camera_id)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)

            if not self.cap.isOpened():
                logger.warning("Failed to open camera, using test patterns instead")
                self.use_test_pattern = True

            self.is_running = True
            asyncio.create_task(self._capture_loop())
            logger.info("Video capture started")
        except Exception as e:
            logger.error(f"Error starting video capture: {e}")
            self.use_test_pattern = True
            self.is_running = True
            asyncio.create_task(self._capture_loop())
            logger.info("Using test patterns instead of camera")

    async def stop(self):
        """Stop the video capture."""
        self.is_running = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        logger.info("Video capture stopped")

    async def _capture_loop(self):
        """Continuously capture frames from the camera."""
        while self.is_running:
            try:
                if self.use_test_pattern:
                    # Use a test pattern if no camera is available
                    frame = self.test_patterns[self.test_pattern_index].copy()
                    self.test_pattern_index = (self.test_pattern_index + 1) % len(self.test_patterns)
                    success = True
                else:
                    # Capture frame from camera
                    success, frame = self.cap.read()

                if success:
                    async with self.frame_lock:
                        self.current_frame = frame
                        self.last_frame_time = time.time()
                else:
                    logger.warning("Failed to capture frame")
                    self.use_test_pattern = True

                # Sleep to maintain the desired frame rate
                await asyncio.sleep(1 / self.fps)
            except Exception as e:
                logger.error(f"Error in capture loop: {e}")
                await asyncio.sleep(1)

    async def get_frame(self) -> Optional[np.ndarray]:
        """Get the most recent frame."""
        async with self.frame_lock:
            if self.current_frame is None:
                return None
            return self.current_frame.copy()

    async def get_latest_metrics(self) -> Dict[str, Any]:
        """Get the latest metrics from processed frames."""
        async with self.metrics_lock:
            return self.latest_metrics.copy()

    @staticmethod
    async def process_frame(frame: np.ndarray, pipeline_config: PipelineConfig) -> tuple[np.ndarray, Dict[str, Any]]:
        """
        Process a frame with the specified pipeline.

        Args:
            frame: The frame to process
            pipeline_config: Configuration for the pipeline to use

        Returns:
            Tuple of (processed_frame, metrics)
        """
        pipeline = get_pipeline_by_name(pipeline_config.name)
        if pipeline is None:
            logger.warning(f"Pipeline '{pipeline_config.name}' not found")
            return frame, {}

        try:
            processed_frame, metrics = pipeline.process(frame, pipeline_config.params)
            return processed_frame, metrics
        except Exception as e:
            logger.error(f"Error processing frame with pipeline '{pipeline_config.name}': {e}")
            return frame, {}

    async def generate_mjpeg(self, pipeline_config: PipelineConfig) -> AsyncGenerator[bytes, None]:
        """
        Generate an MJPEG stream with processed frames.

        Args:
            pipeline_config: Configuration for the pipeline to use

        Yields:
            JPEG-encoded frames with multipart/x-mixed-replace boundary
        """
        while self.is_running:
            frame = await self.get_frame()
            if frame is None:
                await asyncio.sleep(0.1)
                continue

            processed_frame, metrics = await self.process_frame(frame, pipeline_config)

            # Store the latest metrics
            async with self.metrics_lock:
                self.latest_metrics = {
                    "timestamp": time.time(),
                    "pipeline": pipeline_config.name,
                    "metrics": metrics
                }

            # Encode the frame as JPEG
            _, jpeg = cv2.imencode('.jpg', processed_frame)
            jpeg_bytes = jpeg.tobytes()

            # Yield the frame with multipart boundary
            yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + jpeg_bytes + b'\r\n'

            # Sleep to maintain the desired frame rate
            await asyncio.sleep(1 / self.fps)
