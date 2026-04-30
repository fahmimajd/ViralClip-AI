'use client';

import { Job, Clip } from '@/lib/api';
import { formatDistanceToNow } from 'date-fns';

interface ClipCardProps {
  clip: Clip;
  jobId: string;
  onDownload: (url: string, filename: string) => void;
}

export default function ClipCard({ clip, jobId, onDownload }: ClipCardProps) {
  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600 dark:text-green-400';
    if (score >= 60) return 'text-yellow-600 dark:text-yellow-400';
    if (score >= 40) return 'text-orange-600 dark:text-orange-400';
    return 'text-red-600 dark:text-red-400';
  };

  const getScoreBadge = (score: number) => {
    if (score >= 80) return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400';
    if (score >= 60) return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400';
    if (score >= 40) return 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400';
    return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400';
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const downloadFilename = `${clip.metadata.title.replace(/[^a-z0-9]/gi, '_').substring(0, 50)}.mp4`;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md overflow-hidden hover:shadow-xl transition-all duration-300 group">
      {/* Thumbnail */}
      <div className="relative aspect-[9/16] overflow-hidden">
        <img
          src={clip.thumbnail_url || '/placeholder-thumb.jpg'}
          alt={clip.metadata.title}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
        />
        
        {/* Duration Badge */}
        <div className="absolute bottom-2 right-2 px-2 py-1 bg-black/70 text-white text-xs font-medium rounded">
          {formatDuration(clip.duration)}
        </div>
        
        {/* Virality Score Badge */}
        <div className={`absolute top-2 left-2 px-2 py-1 rounded-full text-xs font-bold ${getScoreBadge(clip.virality_score)}`}>
          ⚡ {Math.round(clip.virality_score)}
        </div>
        
        {/* Play Overlay */}
        <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center justify-center">
          <video
            src={clip.file_url}
            className="w-full h-full object-contain"
            controls
            preload="metadata"
          />
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {/* Title */}
        <h3 className="font-semibold text-gray-900 dark:text-white mb-2 line-clamp-2 min-h-[3rem]">
          {clip.metadata.title}
        </h3>
        
        {/* Description */}
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">
          {clip.metadata.description}
        </p>
        
        {/* Hashtags */}
        <div className="flex flex-wrap gap-1 mb-3">
          {clip.metadata.hashtags.slice(0, 3).map((tag, idx) => (
            <span
              key={idx}
              className="px-2 py-0.5 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-400 text-xs rounded-full"
            >
              {tag}
            </span>
          ))}
          {clip.metadata.hashtags.length > 3 && (
            <span className="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 text-xs rounded-full">
              +{clip.metadata.hashtags.length - 3}
            </span>
          )}
        </div>
        
        {/* Emotional Peaks */}
        {clip.metadata.emotional_peaks.length > 0 && (
          <div className="mb-3">
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Emotional Moments:</p>
            <div className="flex flex-wrap gap-1">
              {clip.metadata.emotional_peaks.slice(0, 3).map((peak, idx) => (
                <span
                  key={idx}
                  className="px-2 py-0.5 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400 text-xs rounded"
                >
                  {peak}
                </span>
              ))}
            </div>
          </div>
        )}
        
        {/* Quotable Lines */}
        {clip.metadata.quotable_lines.length > 0 && (
          <div className="mb-3 p-2 bg-gray-50 dark:bg-gray-900/50 rounded-lg">
            <p className="text-xs italic text-gray-600 dark:text-gray-400 line-clamp-2">
              "{clip.metadata.quotable_lines[0]}"
            </p>
          </div>
        )}
        
        {/* Stats Row */}
        <div className="flex items-center justify-between pt-3 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2">
            <span className={`text-sm font-bold ${getScoreColor(clip.virality_score)}`}>
              Score: {Math.round(clip.virality_score)}
            </span>
          </div>
          <span className="text-xs text-gray-500 dark:text-gray-400">
            {formatDistanceToNow(new Date(clip.metadata.created_at), { addSuffix: true })}
          </span>
        </div>
        
        {/* Actions */}
        <div className="mt-3 flex gap-2">
          <button
            onClick={() => onDownload(clip.file_url, downloadFilename)}
            className="flex-1 px-3 py-2 bg-primary-600 hover:bg-primary-700 text-white text-sm font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Download
          </button>
        </div>
      </div>
    </div>
  );
}
