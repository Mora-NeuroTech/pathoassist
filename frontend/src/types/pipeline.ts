/**
 * Types for pipeline-related data structures
 */

export interface Pipeline {
  name: string;
  display_name: string;
  description: string;
  default_params: Record<string, any>;
  param_descriptions: Record<string, string>;
}

export interface PipelineSettings {
  name: string;
  params: Record<string, any>;
}

export interface ProcessedFrameData {
  timestamp: number;
  pipeline: string;
  metrics: Record<string, any>;
}