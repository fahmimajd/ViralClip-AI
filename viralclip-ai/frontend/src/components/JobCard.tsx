'use client';

import { Job, Clip } from '@/lib/api';
import { formatDistanceToNow } from 'date-fns';

interface JobCardProps {
  job: Job;
  onViewDetails: (jobId: string) => void;
  onDelete: (jobId: string) => void;
}

export default function JobCard({ job, onViewDetails, onDelete }: JobCardProps) {
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

  const formatDuration = (ms: number) => {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes % 60}m`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    }
    return `${seconds}s`;
  };

  const timeSinceCreated = formatDistanceToNow(new Date(job.created_at), { addSuffix: true });

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-300">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between mb-2">
          <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(job.status)}`}>
            {job.status.toUpperCase()}
          </span>
          <span className="text-xs text-gray-500 dark:text-gray-400">
            {timeSinceCreated}
          </span>
        </div>
        
        <h3 className="text-sm font-medium text-gray-900 dark:text-white truncate">
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
            className="bg-primary-500 h-2 rounded-full transition-all duration-500"
            style={{ width: `${job.progress}%` }}
          />
        </div>
        {job.message && (
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">{job.message}</p>
        )}
        {job.error && (
          <p className="text-xs text-red-500 dark:text-red-400 mt-2">{job.error}</p>
        )}
      </div>

      {/* Clips Preview */}
      {job.clips.length > 0 && (
        <div className="px-4 pb-3">
          <div className="flex items-center gap-2 overflow-x-auto">
            {job.clips.slice(0, 5).map((clip) => (
              <div key={clip.clip_id} className="flex-shrink-0 w-20">
                <img
                  src={clip.thumbnail_url || '/placeholder-thumb.jpg'}
                  alt={clip.metadata.title}
                  className="w-20 h-36 object-cover rounded-lg"
                />
                <div className="mt-1 text-center">
                  <span className="text-xs font-medium text-gray-700 dark:text-gray-300">
                    {Math.round(clip.duration)}s
                  </span>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Score: {Math.round(clip.virality_score)}
                  </p>
                </div>
              </div>
            ))}
            {job.clips.length > 5 && (
              <div className="flex-shrink-0 w-20 h-36 flex items-center justify-center bg-gray-100 dark:bg-gray-700 rounded-lg">
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
          onClick={() => onViewDetails(job.job_id)}
          className="text-sm font-medium text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300"
        >
          View Details →
        </button>
        
        <button
          onClick={() => onDelete(job.job_id)}
          className="text-sm text-gray-500 dark:text-gray-400 hover:text-red-600 dark:hover:text-red-400"
        >
          Delete
        </button>
      </div>
    </div>
  );
}
