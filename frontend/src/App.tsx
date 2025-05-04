import { useState, useEffect } from 'react';
import Header from './components/Header';
import VideoDisplay from './components/VideoDisplay';
import ControlPanel from './components/ControlPanel';
import DataPanel from './components/DataPanel';
import { fetchPipelines, fetchActivePipeline, setActivePipeline } from './api/pipelineApi';
import { Pipeline, PipelineSettings } from './types/pipeline';

function App() {
  const [pipelines, setPipelines] = useState<Pipeline[]>([]);
  const [activePipeline, setActivePipelineState] = useState<PipelineSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch available pipelines on component mount
  useEffect(() => {
      setLoading(true);
      fetchPipelines().then(pipelinesData => {
        setPipelines(pipelinesData);
        return fetchActivePipeline();
      })
        .then(activePipelineData => {
          setActivePipelineState(activePipelineData);
          setLoading(false);
        })
          .catch(err => {
        setError('Failed to load pipelines. Please check if the backend server is running.');
        setLoading(false);
        console.error(err);
      });
  }, []);

  // Handle pipeline change
  const handlePipelineChange = async (settings: PipelineSettings) => {
    try {
      setLoading(true);
      const updatedSettings = await setActivePipeline(settings);
      setActivePipelineState(updatedSettings);
      setLoading(false);
    } catch (err) {
      setError('Failed to update pipeline settings.');
      setLoading(false);
      console.error(err);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <Header />
      
      <main className="container mx-auto px-4 py-8">
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <div className="card mb-6">
              <h2 className="mb-4">Live Microscope Feed</h2>
              <VideoDisplay 
                activePipeline={activePipeline}
              />
            </div>
            
            <div className="card">
              <h2 className="mb-4">Data Analysis</h2>
              <DataPanel activePipeline={activePipeline} />
            </div>
          </div>
          
          <div className="lg:col-span-1">
            <div className="card sticky top-4">
              <h2 className="mb-4">Controls</h2>
              <ControlPanel 
                pipelines={pipelines}
                activePipeline={activePipeline}
                onPipelineChange={handlePipelineChange}
                loading={loading}
              />
            </div>
          </div>
        </div>
      </main>
      
      <footer className="bg-white py-4 shadow">
        <div className="container mx-auto px-4 text-center text-gray-600">
          <p>PathoAssist &copy; {new Date().getFullYear()}</p>
        </div>
      </footer>
    </div>
  );
}

export default App;