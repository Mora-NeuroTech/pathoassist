# PathoAssist

PathoAssist is a full-stack application for real-time microscope image analysis with customizable overlay pipelines.

## Features

- Live video capture from microscope cameras using OpenCV
- Real-time image processing with customizable overlay pipelines
- Cell detection and counting
- Fluorescence detection and measurement
- Interactive UI for configuring overlay parameters
- Real-time data visualization

## Architecture

### Backend

- **FastAPI**: REST API and WebSocket server
- **OpenCV**: Video capture and image processing
- **Overlay Pipelines**: Modular image processing pipelines

### Frontend

- **React**: UI components
- **TypeScript**: Type safety
- **Vite**: Build tool
- **Tailwind CSS**: Styling
- **Recharts**: Data visualization

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn
- A webcam or microscope camera (optional, test patterns are provided)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/pathoassist.git
   cd pathoassist
   ```

2. Set up the backend:
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Set up the frontend:
   ```bash
   cd ../frontend
   npm install  # or yarn install
   ```

### Running the Application

1. Start the backend server:
   ```bash
   cd backend
   source .venv/bin/activate  # On Windows: venv\Scripts\activate
   uvicorn main:app --reload
   ```

2. Start the frontend development server:
   ```bash
   cd ../frontend
   npm run dev  # or yarn dev
   ```

3. Open your browser and navigate to http://localhost:5173

## Usage

1. Select an overlay pipeline from the dropdown menu
2. Adjust the parameters as needed
3. Click "Apply Settings" to update the pipeline
4. View the processed video feed and real-time data visualization

## Available Pipelines

### Cell Count Overlay

Detects and counts cells in microscope images.

Parameters:

- **threshold**: Threshold value for binary conversion (0-255)
- **min_size**: Minimum cell size in pixels
- **max_size**: Maximum cell size in pixels
- **show_contours**: Whether to draw contours around detected cells
- **contour_color**: RGB color for contours
- **show_count**: Whether to show the cell count on the image
- **count_position**: Position [x, y] to display the count
- **font_scale**: Scale of the font for the count
- **font_color**: RGB color for the count text

### Fluorescence Detection

Detects and measures fluorescence intensity in microscope images.

Parameters:

- **threshold**: Threshold value for fluorescence detection (0-255)
- **color_map**: OpenCV colormap to apply (0-21)
- **alpha**: Transparency of the overlay (0.0-1.0)
- **show_intensity**: Whether to show the intensity value on the image
- **intensity_position**: Position [x, y] to display the intensity
- **font_scale**: Scale of the font for the intensity
- **font_color**: RGB color for the intensity text

## Adding New Pipelines

To add a new pipeline:

1. Create a new class that inherits from `OverlayPipeline` in `backend/overlay_pipelines.py`
2. Implement the `process` method to process frames and extract metrics
3. Register the pipeline using `register_pipeline(YourPipeline())`
