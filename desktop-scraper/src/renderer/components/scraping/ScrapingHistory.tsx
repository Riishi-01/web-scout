import React from 'react';
import { useScraping } from '../../contexts/ScrapingContext';

export const ScrapingHistory: React.FC = () => {
  const { recentTasks } = useScraping();

  return (
    <div className="max-w-6xl mx-auto">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
          Scraping History
        </h2>

        {recentTasks.length === 0 ? (
          <div className="text-center py-12">
            <svg className="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-gray-600 dark:text-gray-400">No scraping tasks yet</p>
          </div>
        ) : (
          <div className="space-y-4">
            {recentTasks.map((task) => (
              <div key={task.taskId} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <div className={`w-3 h-3 rounded-full ${
                      task.status === 'completed' ? 'bg-green-500' :
                      task.status === 'failed' ? 'bg-red-500' :
                      task.status === 'running' ? 'bg-blue-500' :
                      'bg-gray-500'
                    }`}></div>
                    <span className="font-medium text-gray-900 dark:text-white">
                      Task {task.taskId.substring(0, 8)}
                    </span>
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      task.status === 'completed' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' :
                      task.status === 'failed' ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200' :
                      task.status === 'running' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200' :
                      'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
                    }`}>
                      {task.status}
                    </span>
                  </div>
                  <span className="text-sm text-gray-500 dark:text-gray-400">
                    {task.startTime.toLocaleString()}
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500 dark:text-gray-400">Pages:</span>
                    <span className="ml-1 text-gray-900 dark:text-white">
                      {task.progress.currentPage}/{task.progress.totalPages}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500 dark:text-gray-400">Records:</span>
                    <span className="ml-1 text-gray-900 dark:text-white">
                      {task.progress.recordsExtracted}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500 dark:text-gray-400">Progress:</span>
                    <span className="ml-1 text-gray-900 dark:text-white">
                      {task.progress.totalPages > 0 ? 
                        Math.round((task.progress.currentPage / task.progress.totalPages) * 100) : 0}%
                    </span>
                  </div>
                </div>
                {task.error && (
                  <div className="mt-2 p-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded text-sm text-red-700 dark:text-red-300">
                    {task.error}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};