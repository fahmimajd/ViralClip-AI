'use client';

import { useState, useEffect } from 'react';
import apiService, { Job } from '@/lib/api';
import FileUpload from '@/components/FileUpload';
import DashboardStats from '@/components/DashboardStats';
import JobDetailModal from '@/components/JobDetailModal';
import toast, { Toaster } from 'react-hot-toast';

export default function HomePage() {
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [activeTab, setActiveTab] = useState<'youtube' | 'upload'>('youtube');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('all');

  // Load jobs on mount
  useEffect(() => {
    loadJobs();
    // Poll for job updates every 3 seconds for better real-time feel
    const interval = setInterval(loadJobs, 3000);
    return () => clearInterval(interval);
  }, []);

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
      toast.success('Job deleted successfully');
      loadJobs();
    } catch (error) {
      toast.error('Failed to delete job');
    }
  };

  const handleDownload = (url: string, filename: string) => {
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    toast.success(`📥 Downloading: ${filename}`);
  };

  // Filter and search jobs
  const filteredJobs = jobs.filter(job => {
    const matchesStatus = filterStatus === 'all' || job.status === filterStatus;
    const matchesSearch = !searchQuery || 
      job.input_source.toLowerCase().includes(searchQuery.toLowerCase()) ||
      job.clips.some(clip => 
        clip.metadata.title.toLowerCase().includes(searchQuery.toLowerCase())
      );
    return matchesStatus && matchesSearch;
  });

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      <Toaster position="top-right" />
      
      {/* Header */}
      <header className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-lg shadow-sm sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
                <span className="text-4xl">🎬</span>
                <span>ViralClip AI</span>
              </h1>
              <p className="mt-2 text-gray-600 dark:text-gray-400">
                Transform long videos into viral-ready Shorts & Reels with AI
              </p>
            </div>
            <div className="hidden sm:flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                AI Powered
              </span>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Dashboard Stats */}
        <DashboardStats jobs={jobs} />
        
        {/* Input Section */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 mb-8">
          {/* Tabs */}
          <div className="flex gap-4 mb-6 border-b border-gray-200 dark:border-gray-700">
            <button
              onClick={() => setActiveTab('youtube')}
              className={`pb-3 px-4 font-medium transition-colors flex items-center gap-2 ${
                activeTab === 'youtube'
                  ? 'text-primary-600 dark:text-primary-400 border-b-2 border-primary-600'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-700'
              }`}
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
              </svg>
              YouTube URL
            </button>
            <button
              onClick={() => setActiveTab('upload')}
              className={`pb-3 px-4 font-medium transition-colors flex items-center gap-2 ${
                activeTab === 'upload'
                  ? 'text-primary-600 dark:text-primary-400 border-b-2 border-primary-600'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-700'
              }`}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
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
                  className="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
                  disabled={isProcessing}
                />
              </div>
              <button
                type="submit"
                disabled={isProcessing || !youtubeUrl.trim()}
                className="w-full sm:w-auto px-6 py-3 bg-gradient-to-r from-primary-600 to-primary-700 hover:from-primary-700 hover:to-primary-800 text-white font-medium rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-lg hover:shadow-xl"
              >
                {isProcessing ? (
                  <>
                    <div className="spinner" />
                    Processing...
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                    Generate Viral Clips
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
                <div className="p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg flex items-center gap-3">
                  <svg className="w-6 h-6 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div>
                    <p className="text-sm font-medium text-green-800 dark:text-green-400">
                      Selected: {selectedFile.name}
                    </p>
                    <p className="text-xs text-green-600 dark:text-green-500">
                      {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                </div>
              )}
              
              <button
                onClick={handleUploadProcess}
                disabled={isProcessing || !selectedFile}
                className="w-full sm:w-auto px-6 py-3 bg-gradient-to-r from-primary-600 to-primary-700 hover:from-primary-700 hover:to-primary-800 text-white font-medium rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-lg hover:shadow-xl"
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

        {/* Jobs List with Filters */}
        <div>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <svg className="w-6 h-6 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
              Generated Clips
              {filteredJobs.length > 0 && (
                <span className="text-sm font-normal text-gray-500 dark:text-gray-400">
                  ({filteredJobs.length} {filteredJobs.length === 1 ? 'job' : 'jobs'})
                </span>
              )}
            </h2>
            
            {/* Search and Filter */}
            <div className="flex flex-col sm:flex-row gap-3">
              <input
                type="text"
                placeholder="Search clips..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              >
                <option value="all">All Status</option>
                <option value="completed">Completed</option>
                <option value="processing">Processing</option>
                <option value="failed">Failed</option>
              </select>
            </div>
          </div>
          
          {filteredJobs.length === 0 ? (
            jobs.length === 0 ? (
              <div className="text-center py-16 bg-white dark:bg-gray-800 rounded-xl">
                <div className="w-20 h-20 mx-auto bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center mb-4">
                  <svg className="w-10 h-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No jobs yet</h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 max-w-md mx-auto">
                  Get started by processing a YouTube video or uploading a file to generate viral clips.
                </p>
              </div>
            ) : (
              <div className="text-center py-16 bg-white dark:bg-gray-800 rounded-xl">
                <div className="w-20 h-20 mx-auto bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center mb-4">
                  <svg className="w-10 h-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No matching results</h3>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Try adjusting your search or filter criteria.
                </p>
              </div>
            )
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredJobs.map((job) => (
                <div
                  key={job.job_id}
                  className="bg-white dark:bg-gray-800 rounded-xl shadow-md overflow-hidden hover:shadow-xl transition-all duration-300 group animate-fade-in"
                >
                  {/* Header */}
                  <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                    <div className="flex items-center justify-between mb-2">
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                        job.status === 'completed' ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' :
                        job.status === 'failed' ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400' :
                        job.status === 'rendering' ? 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400' :
                        job.status === 'analyzing' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400' :
                        'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                      }`}>
                        {job.status.toUpperCase()}
                      </span>
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {new Date(job.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    
                    <h3 className="text-sm font-medium text-gray-900 dark:text-white truncate" title={job.input_source}>
                      {job.input_source}
                    </h3>
                  </div>

                  {/* Progress Bar */}
                  <div className="px-4 py-3">
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="text-gray-600 dark:text-gray-400">Progress</span>
                      <span className="font-medium text-gray-900 dark:text-white">{job.progress}%</span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                      <div
                        className="bg-gradient-to-r from-primary-500 to-primary-600 h-2 rounded-full transition-all duration-500"
                        style={{ width: `${job.progress}%` }}
                      />
                    </div>
                    {job.message && (
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-2 truncate">{job.message}</p>
                    )}
                    {job.error && (
                      <p className="text-xs text-red-500 dark:text-red-400 mt-2">{job.error}</p>
                    )}
                  </div>

                  {/* Clips Preview */}
                  {job.clips.length > 0 && (
                    <div className="px-4 pb-3">
                      <div className="flex items-center gap-2 overflow-x-auto pb-2">
                        {job.clips.slice(0, 5).map((clip, idx) => (
                          <div key={clip.clip_id} className="flex-shrink-0 relative">
                            <img
                              src={clip.thumbnail_url || '/placeholder-thumb.jpg'}
                              alt={clip.metadata.title}
                              className="w-16 h-28 object-cover rounded-lg"
                            />
                            <div className="absolute top-1 left-1 px-1.5 py-0.5 bg-black/70 text-white text-xs rounded">
                              ⚡{Math.round(clip.virality_score)}
                            </div>
                          </div>
                        ))}
                        {job.clips.length > 5 && (
                          <div className="flex-shrink-0 w-16 h-28 flex items-center justify-center bg-gray-100 dark:bg-gray-700 rounded-lg">
                            <span className="text-sm font-medium text-gray-500 dark:text-gray-400">
                              +{job.clips.length - 5}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Actions */}
                  <div className="px-4 py-3 bg-gray-50 dark:bg-gray-900/50 flex items-center justify-between">
                    <button
                      onClick={() => handleViewDetails(job.job_id)}
                      className="text-sm font-medium text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 flex items-center gap-1"
                    >
                      View Details
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </button>
                    
                    <button
                      onClick={() => handleDeleteJob(job.job_id)}
                      className="text-sm text-gray-500 dark:text-gray-400 hover:text-red-600 dark:hover:text-red-400 p-2 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                      title="Delete job"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>

      {/* Job Detail Modal */}
      {selectedJob && (
        <JobDetailModal
          job={selectedJob}
          onClose={handleCloseModal}
          onDownload={handleDownload}
        />
      )}
    </div>
  );
}
