import React, {useState} from 'react';
import {PipelineSettings} from '../types/pipeline';

interface VideoDisplayProps {
    activePipeline: PipelineSettings | null;
}

const VideoDisplay: React.FC<VideoDisplayProps> = ({activePipeline}) => {
    const [error] = useState<string | null>(null);


    // Generate MJPEG stream URL
    const getMjpegUrl = () => {
        if (!activePipeline) return '';
        return `/api/stream`;
    };

    if (!activePipeline) {
        return (
            <div className="bg-gray-100 rounded-lg p-8 text-center">
                <p className="text-gray-600">Loading pipeline configuration...</p>
            </div>
        );
    }

    return (
        <div className="video-display">
            <div className="mb-4 flex justify-between items-center">
                <div className="text-sm text-gray-600">
                    <span>{activePipeline.name}</span>
                </div>
            </div>

            {error && (
                <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
                    {error}
                </div>
            )}

            <div className="bg-black rounded-lg overflow-hidden">
                <img
                    src={getMjpegUrl()}
                    alt="Microscope Feed"
                    className="w-full h-auto"
                />
            </div>
        </div>
    );
};

export default VideoDisplay;