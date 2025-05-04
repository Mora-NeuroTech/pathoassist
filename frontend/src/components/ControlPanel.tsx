import React, { useState, useEffect } from 'react';
import { Pipeline, PipelineSettings } from '../types/pipeline';

interface ControlPanelProps {
  pipelines: Pipeline[];
  activePipeline: PipelineSettings | null;
  onPipelineChange: (settings: PipelineSettings) => void;
  loading: boolean;
}

const ControlPanel: React.FC<ControlPanelProps> = ({
  pipelines,
  activePipeline,
  onPipelineChange,
  loading
}) => {
  const [selectedPipeline, setSelectedPipeline] = useState<string>('');
  const [params, setParams] = useState<Record<string, any>>({});
  const [currentPipeline, setCurrentPipeline] = useState<Pipeline | null>(null);
  const [initialParams, setInitialParams] = useState<Record<string, any>>({});
  const [initialPipeline, setInitialPipeline] = useState<string>('');

  // Update the selected pipeline and params when the active pipeline changes
  useEffect(() => {
    if (activePipeline) {
      setSelectedPipeline(activePipeline.name);
      setParams(activePipeline.params);
      setInitialParams(activePipeline.params);
      setInitialPipeline(activePipeline.name);

      // Find the current pipeline details
      const pipeline = pipelines.find(p => p.name === activePipeline.name) || null;
      setCurrentPipeline(pipeline);
    }
  }, [activePipeline, pipelines]);
  
  // Handle pipeline selection change
  const handlePipelineChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const pipelineName = e.target.value;
    setSelectedPipeline(pipelineName);
    
    // Find the selected pipeline
    const pipeline = pipelines.find(p => p.name === pipelineName);
    if (pipeline) {
      setCurrentPipeline(pipeline);
      setParams(pipeline.default_params);
    }
  };
  
  // Handle parameter change
  const handleParamChange = (paramName: string, value: any) => {
    setParams(prevParams => ({
      ...prevParams,
      [paramName]: value
    }));
  };
  
  // Handle form submission
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (selectedPipeline) {
      onPipelineChange({
        name: selectedPipeline,
        params
      });
    }
  };
  
  // Render parameter input based on type
  const renderParamInput = (paramName: string, value: any, description: string) => {
    // Determine the type of the parameter
    const type = typeof value;
    
    if (type === 'boolean') {
      return (
        <div key={paramName} className="mb-4">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={params[paramName] || false}
              onChange={e => handleParamChange(paramName, e.target.checked)}
              className="mr-2"
              disabled={loading}
            />
            <span className="label">{paramName}</span>
          </label>
          <p className="text-xs text-gray-500 mt-1">{description}</p>
        </div>
      );
    } else if (type === 'number') {
      return (
        <div key={paramName} className="mb-4">
          <label className="label" htmlFor={paramName}>
            {paramName}
          </label>
          <input
            type="number"
            id={paramName}
            value={params[paramName] || 0}
            onChange={e => handleParamChange(paramName, Number(e.target.value))}
            className="input w-full"
            disabled={loading}
          />
          <p className="text-xs text-gray-500 mt-1">{description}</p>
        </div>
      );
    } else if (Array.isArray(value)) {
      // Handle array parameters (like colors or positions)
      return (
        <div key={paramName} className="mb-4">
          <label className="label" htmlFor={paramName}>
            {paramName}
          </label>
          <div className="flex space-x-2">
            {value.map((_item, index) => (
              <input
                key={index}
                type="number"
                value={(params[paramName] || value)[index] || 0}
                onChange={e => {
                    const newArray = [...(params[paramName] || value)];
                    newArray[index] = Number(e.target.value);
                  handleParamChange(paramName, newArray);
                }}
                className="input w-full"
                disabled={loading}
              />
            ))}
          </div>
          <p className="text-xs text-gray-500 mt-1">{description}</p>
        </div>
      );
    } else {
      // Default to text input for other types
      return (
        <div key={paramName} className="mb-4">
          <label className="label" htmlFor={paramName}>
            {paramName}
          </label>
          <input
            type="text"
            id={paramName}
            value={params[paramName] || ''}
            onChange={e => handleParamChange(paramName, e.target.value)}
            className="input w-full"
            disabled={loading}
          />
          <p className="text-xs text-gray-500 mt-1">{description}</p>
        </div>
      );
    }
  };
  
  return (
    <div className="control-panel">
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label className="label" htmlFor="pipeline-select">
            Select Pipeline
          </label>
          <select
            id="pipeline-select"
            value={selectedPipeline}
            onChange={handlePipelineChange}
            className="input w-full"
            disabled={loading}
          >
            {pipelines.map(pipeline => (
              <option key={pipeline.name} value={pipeline.name}>
                {pipeline.display_name}
              </option>
            ))}
          </select>
        </div>
        
        {currentPipeline && (
          <div className="mb-4">
            <h3 className="text-sm font-medium text-gray-700 mb-2">Description</h3>
            <p className="text-sm text-gray-600 mb-4">{currentPipeline.description}</p>
            
            <h3 className="text-sm font-medium text-gray-700 mb-2">Parameters</h3>
            {Object.entries(currentPipeline.default_params).map(([paramName, value]) => 
              renderParamInput(
                paramName, 
                value, 
                currentPipeline.param_descriptions[paramName] || ''
              )
            )}
          </div>
        )}

        <div className="flex gap-2">
          <button
              type="button"
              className="btn btn-secondary flex-1"
              onClick={() => {
                setSelectedPipeline(initialPipeline);
                setParams(initialParams);
                const pipeline = pipelines.find(p => p.name === initialPipeline);
                if (pipeline) {
                  setCurrentPipeline(pipeline);
                }
              }}
              disabled={loading || !selectedPipeline || (JSON.stringify(params) === JSON.stringify(initialParams) && selectedPipeline === initialPipeline)}
          >
            Reset
          </button>
          <button
              type="submit"
              className="btn btn-primary flex-1"
              disabled={loading || !selectedPipeline || (JSON.stringify(params) === JSON.stringify(initialParams) && selectedPipeline === initialPipeline)}
          >
            {loading ? 'Applying...' : 'Apply Settings'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default ControlPanel;