import React from 'react';
import { useScraping } from '../../contexts/ScrapingContext';

export const ProgressPanel: React.FC = () => {
  const { activeTask, stopScraping } = useScraping();

  const handleStop = async () => {
    if (activeTask) {
      await stopScraping(activeTask.taskId);
    }
  };

  if (!activeTask) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 text-center">
          <p className="text-gray-600 dark:text-gray-400">No active scraping task</p>
        </div>
      </div>
    );
  }

  const progressPercent = activeTask.progress.totalPages > 0 
    ? (activeTask.progress.currentPage / activeTask.progress.totalPages) * 100 
    : 0;

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            Scraping Progress
          </h2>
          {activeTask.status === 'running' && (
            <button
              onClick={handleStop}
              className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
            >
              Stop Scraping
            </button>
          )}
        </div>

        {/* Progress Bar */}
        <div className="mb-6">
          <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400 mb-2">
            <span>Progress</span>
            <span>{progressPercent.toFixed(1)}%</span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
            <div
              className="progress-bar h-3 rounded-full transition-all duration-500"
              style={{ width: `${progressPercent}%` }}
            ></div>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="text-center p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {activeTask.progress.currentPage}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Pages Processed</div>
          </div>
          <div className="text-center p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {activeTask.progress.totalPages}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Total Pages</div>
          </div>
          <div className="text-center p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {activeTask.progress.recordsExtracted}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Records Found</div>
          </div>
          <div className="text-center p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <div className={`text-2xl font-bold ${
              activeTask.status === 'running' ? 'text-blue-600' :
              activeTask.status === 'completed' ? 'text-green-600' :
              activeTask.status === 'failed' ? 'text-red-600' :
              'text-gray-600'
            }`}>
              {activeTask.status.toUpperCase()}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Status</div>
          </div>
        </div>

        {/* Current URL */}
        {activeTask.progress.currentUrl && (
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Currently Processing:
            </label>
            <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-md text-sm text-gray-900 dark:text-white font-mono break-all">
              {activeTask.progress.currentUrl}
            </div>
          </div>
        )}

        {/* Error */}
        {activeTask.error && (
          <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <h3 className="text-sm font-medium text-red-800 dark:text-red-200 mb-1">Error</h3>
            <p className="text-sm text-red-700 dark:text-red-300">{activeTask.error}</p>
          </div>
        )}

        {/* Success Message */}
        {activeTask.status === 'completed' && (
          <div className="p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg text-center">
            <div className="text-green-800 dark:text-green-200">
              <h3 className="text-lg font-semibold mb-1">Scraping Completed!</h3>
              <p className="text-sm">Successfully extracted {activeTask.progress.recordsExtracted} records</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};