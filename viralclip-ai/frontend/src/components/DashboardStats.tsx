'use client';

import { Job, Clip } from '@/lib/api';
import { formatDistanceToNow } from 'date-fns';

interface DashboardStatsProps {
  jobs: Job[];
}

export default function DashboardStats({ jobs }: DashboardStatsProps) {
  const stats = {
    total: jobs.length,
    completed: jobs.filter(j => j.status === 'completed').length,
    processing: jobs.filter(j => ['pending', 'downloading', 'transcribing', 'analyzing', 'rendering'].includes(j.status)).length,
    failed: jobs.filter(j => j.status === 'failed').length,
    totalClips: jobs.reduce((acc, job) => acc + job.clips.length, 0),
  };

  const statCards = [
    {
      title: 'Total Jobs',
      value: stats.total,
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
        </svg>
      ),
      color: 'bg-blue-500',
      trend: null,
    },
    {
      title: 'Completed',
      value: stats.completed,
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      color: 'bg-green-500',
      trend: stats.completed > 0 ? `+${stats.completed}` : null,
    },
    {
      title: 'Processing',
      value: stats.processing,
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      color: 'bg-yellow-500',
      trend: stats.processing > 0 ? 'Active' : null,
    },
    {
      title: 'Total Clips',
      value: stats.totalClips,
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
        </svg>
      ),
      color: 'bg-purple-500',
      trend: stats.totalClips > 0 ? `${stats.totalClips} clips` : null,
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      {statCards.map((stat, index) => (
        <div
          key={stat.title}
          className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 hover:shadow-lg transition-all duration-300 animate-fade-in"
          style={{ animationDelay: `${index * 100}ms` }}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">{stat.title}</p>
              <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">{stat.value}</p>
              {stat.trend && (
                <p className="text-xs text-green-600 dark:text-green-400 mt-1">{stat.trend}</p>
              )}
            </div>
            <div className={`${stat.color} p-3 rounded-lg text-white`}>
              {stat.icon}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
