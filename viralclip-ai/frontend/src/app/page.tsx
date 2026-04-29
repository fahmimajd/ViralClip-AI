'use client';

import { useState } from 'react';
import apiService, { Job } from '@/lib/api';
import FileUpload from '@/components/FileUpload';
import JobCard from '@/components/JobCard';
import toast, { Toaster } from 'react-hot-toast';

export default function HomePage() {
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [activeTab, setActiveTab] = useState<'youtube' | 'upload'>('youtube');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // Load jobs on mount
  useState(() => {
    loadJobs();
    // Poll for job updates every 5 seconds
    const interval = setInterval(loadJobs, 5000);
    return () => clearInterval(interval);
  });

  const loadJobs = async () => {
    try {
      const jobList = await apiService.listJobs({ limit: 20 });
      setJobs(jobList);
    } catch (error) {
      console.error('Failed to load jobs:', error);
    }
  };

  const handleYouTubeProcess = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!youtubeUrl.trim()) {
      toast.error('Please enter a YouTube URL');
      return;
    }

    setIsProcessing(true);
    try {
      await apiService.processYouTube(youtubeUrl, {
        top_clips: 10,
        add_captions: true,
      });
      toast.success('Processing started! Check the jobs list below.');
      setYoutubeUrl('');
      loadJobs();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to process video');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
  };

  const handleUploadProcess = async () => {
    if (!selectedFile) {
      toast.error('Please select a file');
      return;
    }

    setIsProcessing(true);
    try {
      // Upload file first
      const uploadResult = await apiService.uploadVideo(selectedFile);
      
      // Then start processing
      await apiService.processUpload(uploadResult.job_id, {
        top_clips: 10,
        add_captions: true,
      });
      
      toast.success('Processing started! Check the jobs list below.');
      setSelectedFile(null);
      loadJobs();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to process video');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleViewDetails = (jobId: string) => {
    // In a real app, navigate to a details page
    toast(`Viewing job ${jobId}`);
  };

  const handleDeleteJob = async (jobId: string) => {
    if (!confirm('Are you sure you want to delete this job?')) return;
    
    try {
      await apiService.deleteJob(jobId);
      toast.success('Job deleted');
      loadJobs();
    } catch (error) {
      toast.error('Failed to delete job');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Toaster position="top-right" />
      
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            🎬 ViralClip AI
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Transform long videos into viral-ready Shorts & Reels
          </p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Input Section */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 mb-8">
          {/* Tabs */}
          <div className="flex gap-4 mb-6 border-b border-gray-200 dark:border-gray-700">
            <button
              onClick={() => setActiveTab('youtube')}
              className={`pb-3 px-4 font-medium transition-colors ${
                activeTab === 'youtube'
                  ? 'text-primary-600 dark:text-primary-400 border-b-2 border-primary-600'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-700'
              }`}
            >
              YouTube URL
            </button>
            <button
              onClick={() => setActiveTab('upload')}
              className={`pb-3 px-4 font-medium transition-colors ${
                activeTab === 'upload'
                  ? 'text-primary-600 dark:text-primary-400 border-b-2 border-primary-600'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-700'
              }`}
            >
              Upload Video
            </button>
          </div>

          {/* YouTube Form */}
          {activeTab === 'youtube' && (
            <form onSubmit={handleYouTubeProcess} className="space-y-4">
              <div>
                <label htmlFor="youtube-url" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  YouTube Video URL
                </label>
                <input
                  id="youtube-url"
                  type="url"
                  value={youtubeUrl}
                  onChange={(e) => setYoutubeUrl(e.target.value)}
                  placeholder="https://www.youtube.com/watch?v=..."
                  className="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  disabled={isProcessing}
                />
              </div>
              <button
                type="submit"
                disabled={isProcessing || !youtubeUrl.trim()}
                className="w-full sm:w-auto px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {isProcessing ? (
                  <>
                    <div className="spinner" />
                    Processing...
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Generate Clips
                  </>
                )}
              </button>
            </form>
          )}

          {/* Upload Form */}
          {activeTab === 'upload' && (
            <div className="space-y-4">
              <FileUpload onFileSelect={handleFileSelect} />
              
              {selectedFile && (
                <div className="p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                  <p className="text-sm font-medium text-green-800 dark:text-green-400">
                    Selected: {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
                  </p>
                </div>
              )}
              
              <button
                onClick={handleUploadProcess}
                disabled={isProcessing || !selectedFile}
                className="w-full sm:w-auto px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {isProcessing ? (
                  <>
                    <div className="spinner" />
                    Processing...
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    Upload & Process
                  </>
                )}
              </button>
            </div>
          )}
        </div>

        {/* Jobs List */}
        <div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            Recent Jobs
          </h2>
          
          {jobs.length === 0 ? (
            <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-xl">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">No jobs yet</h3>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                Get started by processing a YouTube video or uploading a file.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {jobs.map((job) => (
                <JobCard
                  key={job.job_id}
                  job={job}
                  onViewDetails={handleViewDetails}
                  onDelete={handleDeleteJob}
                />
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
