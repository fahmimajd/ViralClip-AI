'use client';

import { Job } from '@/lib/api';
import { formatDistanceToNow } from 'date-fns';

interface JobDetailModalProps {
  job: Job;
  onClose: () => void;
  onDownload: (url: string, filename: string) => void;
}

export default function JobDetailModal({ job, onClose, onDownload }: JobDetailModalProps) {
  const getStatusColor = (status: Job['status']) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400';
      case 'failed':
        return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400';
      case 'rendering':
        return 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400';
      case 'analyzing':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
    }
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getScoreBadge = (score: number) => {
    if (score >= 80) return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400';
    if (score >= 60) return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400';
    if (score >= 40) return 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400';
    return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400';
  };

  const downloadAllClips = () => {
    job.clips.forEach((clip, index) => {
      setTimeout(() => {
        const filename = `${clip.metadata.title.replace(/[^a-z0-9]/gi, '_').substring(0, 50)}.mp4`;
        onDownload(clip.file_url, filename);
      }, index * 300);
    });
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
              Job Details
            </h2>
            <div className="flex items-center gap-3">
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(job.status)}`}>
                {job.status.toUpperCase()}
              </span>
              <span className="text-sm text-gray-500 dark:text-gray-400">
                {formatDistanceToNow(new Date(job.created_at), { addSuffix: true })}
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <svg className="w-6 h-6 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Job Info */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Source</h3>
            <div className="p-4 bg-gray-50 dark:bg-gray-900/50 rounded-xl">
              <p className="text-sm font-medium text-gray-900 dark:text-white break-all">
                {job.input_source}
              </p>
            </div>
          </div>

          {/* Progress */}
          {job.status !== 'completed' && job.status !== 'failed' && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Progress</h3>
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600 dark:text-gray-400">{job.message || 'Processing...'}</span>
                  <span className="font-medium text-gray-900 dark:text-white">{job.progress}%</span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                  <div
                    className="bg-primary-500 h-3 rounded-full transition-all duration-500"
                    style={{ width: `${job.progress}%` }}
                  />
                </div>
              </div>
            </div>
          )}

          {/* Error Message */}
          {job.error && (
            <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl">
              <p className="text-sm text-red-600 dark:text-red-400">{job.error}</p>
            </div>
          )}

          {/* Clips Grid */}
          {job.clips.length > 0 && (
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Generated Clips ({job.clips.length})
                </h3>
                <button
                  onClick={downloadAllClips}
                  className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white text-sm font-medium rounded-lg transition-colors flex items-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  Download All
                </button>
              </div>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {job.clips.map((clip) => (
                  <div
                    key={clip.clip_id}
                    className="bg-white dark:bg-gray-800 rounded-xl shadow-md overflow-hidden hover:shadow-lg transition-shadow"
                  >
                    {/* Thumbnail */}
                    <div className="relative aspect-[9/16] overflow-hidden bg-gray-100 dark:bg-gray-900">
                      <img
                        src={clip.thumbnail_url || '/placeholder-thumb.jpg'}
                        alt={clip.metadata.title}
                        className="w-full h-full object-cover"
                      />
                      
                      {/* Duration Badge */}
                      <div className="absolute bottom-2 right-2 px-2 py-1 bg-black/70 text-white text-xs font-medium rounded">
                        {formatDuration(clip.duration)}
                      </div>
                      
                      {/* Score Badge */}
                      <div className={`absolute top-2 left-2 px-2 py-1 rounded-full text-xs font-bold ${getScoreBadge(clip.virality_score)}`}>
                        ⚡ {Math.round(clip.virality_score)}
                      </div>
                      
                      {/* Video Preview */}
                      <div className="absolute inset-0 bg-black/40 opacity-0 hover:opacity-100 transition-opacity flex items-center justify-center">
                        <video
                          src={clip.file_url}
                          className="w-full h-full object-contain"
                          controls
                          preload="metadata"
                        />
                      </div>
                    </div>

                    {/* Info */}
                    <div className="p-3">
                      <h4 className="font-medium text-gray-900 dark:text-white text-sm mb-2 line-clamp-2">
                        {clip.metadata.title}
                      </h4>
                      
                      {/* Hashtags */}
                      <div className="flex flex-wrap gap-1 mb-2">
                        {clip.metadata.hashtags.slice(0, 2).map((tag, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-0.5 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-400 text-xs rounded-full"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                      
                      {/* Quotable Line */}
                      {clip.metadata.quotable_lines.length > 0 && (
                        <p className="text-xs italic text-gray-600 dark:text-gray-400 mb-2 line-clamp-1">
                          "{clip.metadata.quotable_lines[0]}"
                        </p>
                      )}
                      
                      {/* Download Button */}
                      <button
                        onClick={() => {
                          const filename = `${clip.metadata.title.replace(/[^a-z0-9]/gi, '_').substring(0, 50)}.mp4`;
                          onDownload(clip.file_url, filename);
                        }}
                        className="w-full px-3 py-2 bg-primary-600 hover:bg-primary-700 text-white text-xs font-medium rounded-lg transition-colors flex items-center justify-center gap-1"
                      >
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                        </svg>
                        Download
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
