import React, {useEffect, useState} from 'react';
import {PipelineSettings} from '../types/pipeline';
import {fetchFrameMetrics} from '../api/pipelineApi';
import {
    Bar,
    BarChart,
    CartesianGrid,
    Cell,
    Legend,
    Pie,
    PieChart,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis
} from 'recharts';

interface DataPanelProps {
    activePipeline: PipelineSettings | null;
}

const DataPanel: React.FC<DataPanelProps> = ({activePipeline}) => {
    const [metrics, setMetrics] = useState<Record<string, any> | null>(null);

    useEffect(() => {
        // Function to fetch metrics
        const getMetrics = () => {
            fetchFrameMetrics()
                .then((data) => {
                    setMetrics(data.metrics);
                })
                .catch((error) => {
                    console.error('Error fetching metrics:', error);
                });
        };

        // Fetch metrics immediately
        getMetrics();

        // Set up interval to fetch metrics periodically
        const intervalId = setInterval(getMetrics, 1000); // Fetch every second

        // Cleanup interval on component unmount
        return () => clearInterval(intervalId);
    }, []);

    if (!activePipeline) {
        return (
            <div className="p-4 bg-gray-100 rounded-lg text-center">
                <p className="text-gray-600">No active pipeline</p>
            </div>
        );
    }

    if (metrics === null) {
        return (
            <div className="p-4 bg-gray-100 rounded-lg text-center">
                <p className="text-gray-600">Waiting for data...</p>
            </div>
        );
    }

    if (Object.keys(metrics).length === 0) {
        return (
            <div className="p-4 bg-gray-100 rounded-lg text-center">
                <p className="text-gray-600">No metrics available</p>
            </div>
        );
    }

    // Render different visualizations based on the active pipeline
    const renderVisualization = () => {
        switch (activePipeline.name) {
            case 'cell_count':
                return renderCellCountVisualization();
            case 'fluorescence':
                return renderFluorescenceVisualization();
            default:
                return (
                    <div className="p-4 bg-gray-100 rounded-lg text-center">
                        <p className="text-gray-600">No visualization available for this pipeline</p>
                    </div>
                );
        }
    };

    // Render cell count visualization
    const renderCellCountVisualization = () => {
        const cellCount = metrics.cell_count || 0;
        const sizes = metrics.sizes || {};

        // Prepare data for a size distribution chart
        const sizeData = [];
        if (sizes.min_size !== undefined && sizes.max_size !== undefined && sizes.avg_size !== undefined) {
            sizeData.push({name: 'Min', value: Math.round(sizes.min_size)});
            sizeData.push({name: 'Avg', value: Math.round(sizes.avg_size)});
            sizeData.push({name: 'Max', value: Math.round(sizes.max_size)});
        }

        return (
            <div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                    <div className="bg-white p-4 rounded-lg shadow-sm">
                        <h3 className="text-lg font-semibold text-gray-700 mb-2">Cell Count</h3>
                        <p className="text-3xl font-bold text-primary-600">{cellCount}</p>
                    </div>

                    {sizes.min_size !== undefined && (
                        <div className="bg-white p-4 rounded-lg shadow-sm">
                            <h3 className="text-lg font-semibold text-gray-700 mb-2">Min Size</h3>
                            <p className="text-3xl font-bold text-primary-600">{Math.round(sizes.min_size)} px²</p>
                        </div>
                    )}

                    {sizes.avg_size !== undefined && (
                        <div className="bg-white p-4 rounded-lg shadow-sm">
                            <h3 className="text-lg font-semibold text-gray-700 mb-2">Avg Size</h3>
                            <p className="text-3xl font-bold text-primary-600">{Math.round(sizes.avg_size)} px²</p>
                        </div>
                    )}
                </div>

                {sizeData.length > 0 && (
                    <div className="bg-white p-4 rounded-lg shadow-sm">
                        <h3 className="text-lg font-semibold text-gray-700 mb-4">Size Distribution</h3>
                        <div className="h-64">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart
                                    data={sizeData}
                                    margin={{top: 5, right: 30, left: 20, bottom: 5}}
                                >
                                    <CartesianGrid strokeDasharray="3 3"/>
                                    <XAxis dataKey="name"/>
                                    <YAxis/>
                                    <Tooltip/>
                                    <Legend/>
                                    <Bar dataKey="value" name="Size (px²)" fill="#0ea5e9"/>
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                )}
            </div>
        );
    };

    // Render fluorescence visualization
    const renderFluorescenceVisualization = () => {
        const intensity = metrics.intensity || {};
        const areaPercentage = metrics.area_percentage || 0;

        // Prepare data for pie chart
        const pieData = [
            {name: 'Fluorescent', value: areaPercentage},
            {name: 'Non-fluorescent', value: 100 - areaPercentage}
        ];

        const COLORS = ['#00C49F', '#DDDDDD'];

        return (
            <div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                    {intensity.avg_intensity !== undefined && (
                        <div className="bg-white p-4 rounded-lg shadow-sm">
                            <h3 className="text-lg font-semibold text-gray-700 mb-2">Avg Intensity</h3>
                            <p className="text-3xl font-bold text-primary-600">{intensity.avg_intensity}</p>
                        </div>
                    )}

                    {intensity.min_intensity !== undefined && (
                        <div className="bg-white p-4 rounded-lg shadow-sm">
                            <h3 className="text-lg font-semibold text-gray-700 mb-2">Min Intensity</h3>
                            <p className="text-3xl font-bold text-primary-600">{intensity.min_intensity}</p>
                        </div>
                    )}

                    {intensity.max_intensity !== undefined && (
                        <div className="bg-white p-4 rounded-lg shadow-sm">
                            <h3 className="text-lg font-semibold text-gray-700 mb-2">Max Intensity</h3>
                            <p className="text-3xl font-bold text-primary-600">{intensity.max_intensity}</p>
                        </div>
                    )}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-white p-4 rounded-lg shadow-sm">
                        <h3 className="text-lg font-semibold text-gray-700 mb-2">Area Coverage</h3>
                        <p className="text-3xl font-bold text-primary-600">{areaPercentage.toFixed(2)}%</p>
                    </div>

                    <div className="bg-white p-4 rounded-lg shadow-sm">
                        <h3 className="text-lg font-semibold text-gray-700 mb-4">Area Distribution</h3>
                        <div className="h-48">
                            <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                    <Pie
                                        data={pieData}
                                        cx="50%"
                                        cy="50%"
                                        labelLine={false}
                                        outerRadius={80}
                                        fill="#8884d8"
                                        dataKey="value"
                                        label={({name, percent}) => `${name} ${(percent * 100).toFixed(0)}%`}
                                    >
                                        {pieData.map((_entry, index) => (
                                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]}/>
                                        ))}
                                    </Pie>
                                    <Tooltip/>
                                </PieChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                </div>
            </div>
        );
    };

    return (
        <div className="data-panel">
            {renderVisualization()}
        </div>
    );
};

export default DataPanel;
