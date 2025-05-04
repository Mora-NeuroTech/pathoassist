/**
 * API functions for interacting with the pipeline endpoints
 */

import axios from 'axios';
import { Pipeline, PipelineSettings, ProcessedFrameData } from '../types/pipeline';

const API_BASE_URL = '/api';

/**
 * Fetch all available pipelines
 */
export const fetchPipelines = async (): Promise<Pipeline[]> => {
  try {
    const response = await axios.get(`${API_BASE_URL}/pipelines`);
    return response.data.pipelines;
  } catch (error) {
    console.error('Error fetching pipelines:', error);
    throw error;
  }
};

/**
 * Fetch the currently active pipeline
 */
export const fetchActivePipeline = async (): Promise<PipelineSettings> => {
  try {
    const response = await axios.get(`${API_BASE_URL}/pipelines/active`);
    return response.data;
  } catch (error) {
    console.error('Error fetching active pipeline:', error);
    throw error;
  }
};

/**
 * Set the active pipeline
 */
export const setActivePipeline = async (settings: PipelineSettings): Promise<PipelineSettings> => {
  try {
    const response = await axios.post(`${API_BASE_URL}/pipelines/active`, settings);
    return response.data;
  } catch (error) {
    console.error('Error setting active pipeline:', error);
    throw error;
  }
};

/**
 * Fetch the latest metrics from processed frames
 */
export const fetchFrameMetrics = async (): Promise<ProcessedFrameData> => {
  try {
    const response = await axios.get(`${API_BASE_URL}/metrics`);
    return response.data;
  } catch (error) {
    console.error('Error fetching frame metrics:', error);
    throw error;
  }
};
