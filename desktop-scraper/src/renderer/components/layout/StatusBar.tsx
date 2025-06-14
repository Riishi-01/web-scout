import React from 'react';
import { useModel } from '../../contexts/ModelContext';
import { useScraping } from '../../contexts/ScrapingContext';

export const StatusBar: React.FC = () => {
  const { status: modelStatus } = useModel();
  const { activeTask } = useScraping();

  return (
    <footer className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 px-6 py-2">
      <div className="flex items-center justify-between text-xs text-gray-600 dark:text-gray-400">
        {/* Left side - System status */}
        <div className="flex items-center space-x-6">
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${modelStatus.loaded ? 'bg-green-500' : modelStatus.loading ? 'bg-yellow-500' : 'bg-red-500'}`}></div>
            <span>
              Model: {modelStatus.loaded ? 'Ready' : modelStatus.loading ? 'Loading...' : 'Not Loaded'}
            </span>
          </div>

          {modelStatus.performance && (
            <div className="flex items-center space-x-4">
              <span>Memory: {(modelStatus.performance.memoryUsage / 1024 / 1024).toFixed(0)}MB</span>
              <span>Avg Response: {modelStatus.performance.avgInferenceTime.toFixed(0)}ms</span>
            </div>
          )}
        </div>

        {/* Center - Active task status */}
        {activeTask && (
          <div className="flex items-center space-x-2">
            <div className="flex items-center space-x-1">
              {activeTask.status === 'running' && (
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
              )}
              <span className="font-medium">
                {activeTask.status === 'running' ? 'Scraping...' : 
                 activeTask.status === 'completed' ? 'Completed' :
                 activeTask.status === 'failed' ? 'Failed' :
                 activeTask.status}
              </span>
            </div>
            {activeTask.status === 'running' && (
              <span>
                {activeTask.progress.currentPage}/{activeTask.progress.totalPages} pages • 
                {activeTask.progress.recordsExtracted} records
              </span>
            )}
          </div>
        )}

        {/* Right side - App info */}
        <div className="flex items-center space-x-4">
          <span>Local Web Scraper v1.0.0</span>
          <button
            onClick={() => window.electronAPI.app.version()}
            className="hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
          >
            About
          </button>
        </div>
      </div>
    </footer>
  );
};