import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API types
export interface Job {
  job_id: string;
  status: 'pending' | 'downloading' | 'transcribing' | 'analyzing' | 'rendering' | 'completed' | 'failed';
  progress: number;
  message?: string;
  error?: string;
  input_source: string;
  clips: Clip[];
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

export interface Clip {
  clip_id: string;
  index: number;
  file_path: string;
  file_url: string;
  thumbnail_path: string;
  thumbnail_url: string;
  metadata: ClipMetadata;
  duration: number;
  resolution: string;
  file_size: number;
  virality_score: number;
}

export interface ClipMetadata {
  clip_id: string;
  title: string;
  description: string;
  hashtags: string[];
  start_time: number;
  end_time: number;
  duration: number;
  original_timestamp: string;
  virality_score: number;
  emotional_peaks: string[];
  quotable_lines: string[];
  created_at: string;
}

// API functions
export const apiService = {
  // Health check
  async healthCheck() {
    const response = await api.get('/api/v1/health');
    return response.data;
  },

  // Upload video file
  async uploadVideo(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/api/v1/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Process YouTube URL
  async processYouTube(
    url: string,
    options?: {
      clip_duration_min?: number;
      clip_duration_max?: number;
      top_clips?: number;
      add_captions?: boolean;
      add_music?: boolean;
      search_query?: string;
    }
  ) {
    const response = await api.post('/api/v1/process/youtube', {
      url,
      ...options,
    });
    return response.data;
  },

  // Process uploaded file
  async processUpload(jobId: string, options?: { top_clips?: number; add_captions?: boolean }) {
    const response = await api.post(`/api/v1/process/upload/${jobId}`, null, {
      params: options,
    });
    return response.data;
  },

  // Get job status
  async getJob(jobId: string) {
    const response = await api.get(`/api/v1/jobs/${jobId}`);
    return response.data;
  },

  // List all jobs
  async listJobs(params?: { status?: string; limit?: number; offset?: number }) {
    const response = await api.get('/api/v1/jobs', { params });
    return response.data;
  },

  // Delete job
  async deleteJob(jobId: string) {
    const response = await api.delete(`/api/v1/jobs/${jobId}`);
    return response.data;
  },

  // Search clips
  async searchClips(query: string, jobId?: string, limit?: number) {
    const response = await api.post('/api/v1/search', {
      query,
      job_id: jobId,
      limit: limit || 10,
    });
    return response.data;
  },

  // Download clip
  getClipDownloadUrl(jobId: string, clipIndex: number) {
    return `${API_URL}/api/v1/clips/${jobId}/download/${clipIndex}`;
  },
};

export default apiService;
