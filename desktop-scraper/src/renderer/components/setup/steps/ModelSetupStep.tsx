import React, { useState, useEffect } from 'react';
import { useModel } from '../../../contexts/ModelContext';

interface ModelSetupStepProps {
  onNext: () => void;
  onPrevious: () => void;
}

export const ModelSetupStep: React.FC<ModelSetupStepProps> = ({ onNext, onPrevious }) => {
  const { status, loadModel } = useModel();
  const [isLoading, setIsLoading] = useState(false);

  const handleLoadModel = async () => {
    try {
      setIsLoading(true);
      await loadModel();
    } catch (error) {
      console.error('Failed to load model:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const canProceed = status.loaded && !status.error;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
          AI Model Setup
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          Load the TinyLlama model for intelligent web scraping
        </p>
      </div>

      <div className="max-w-2xl mx-auto">
        {/* Model Status */}
        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              TinyLlama Web Scraper Model
            </h3>
            <div className={`px-3 py-1 rounded-full text-sm font-medium ${
              status.loaded 
                ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                : status.loading
                ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                : status.error
                ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                : 'bg-gray-100 text-gray-800 dark:bg-gray-600 dark:text-gray-200'
            }`}>
              {status.loaded ? 'Loaded' : status.loading ? 'Loading...' : status.error ? 'Error' : 'Not Loaded'}
            </div>
          </div>

          {status.modelInfo && (
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-500 dark:text-gray-400">Version:</span>
                <span className="ml-2 text-gray-900 dark:text-white">{status.modelInfo.version}</span>
              </div>
              <div>
                <span className="text-gray-500 dark:text-gray-400">Size:</span>
                <span className="ml-2 text-gray-900 dark:text-white">
                  {(status.modelInfo.size / 1024 / 1024).toFixed(1)} MB
                </span>
              </div>
              <div>
                <span className="text-gray-500 dark:text-gray-400">Quantization:</span>
                <span className="ml-2 text-gray-900 dark:text-white">{status.modelInfo.quantization}</span>
              </div>
              <div>
                <span className="text-gray-500 dark:text-gray-400">Platform:</span>
                <span className="ml-2 text-gray-900 dark:text-white">CPU Optimized</span>
              </div>
            </div>
          )}

          {status.performance && (
            <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-600">
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <span className="text-gray-500 dark:text-gray-400">Load Time:</span>
                  <span className="ml-2 text-gray-900 dark:text-white">
                    {(status.performance.loadTime / 1000).toFixed(1)}s
                  </span>
                </div>
                <div>
                  <span className="text-gray-500 dark:text-gray-400">Inference:</span>
                  <span className="ml-2 text-gray-900 dark:text-white">
                    {status.performance.avgInferenceTime.toFixed(0)}ms
                  </span>
                </div>
                <div>
                  <span className="text-gray-500 dark:text-gray-400">Memory:</span>
                  <span className="ml-2 text-gray-900 dark:text-white">
                    {(status.performance.memoryUsage / 1024 / 1024).toFixed(0)}MB
                  </span>
                </div>
              </div>
            </div>
          )}

          {status.error && (
            <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded">
              <p className="text-red-800 dark:text-red-200 text-sm">{status.error}</p>
            </div>
          )}
        </div>

        {/* Load Button */}
        {!status.loaded && (
          <div className="text-center mb-6">
            <button
              onClick={handleLoadModel}
              disabled={isLoading || status.loading}
              className="px-6 py-3 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isLoading || status.loading ? (
                <div className="flex items-center">
                  <div className="spinner mr-2"></div>
                  Loading Model...
                </div>
              ) : (
                'Load AI Model'
              )}
            </button>
          </div>
        )}

        {/* Requirements Info */}
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <h4 className="font-semibold text-blue-900 dark:text-blue-200 mb-2">
            System Requirements
          </h4>
          <ul className="text-sm text-blue-800 dark:text-blue-300 space-y-1">
            <li>• RAM: 2GB available memory</li>
            <li>• Storage: 500MB free space</li>
            <li>• CPU: Dual-core processor recommended</li>
            <li>• First load may take 10-30 seconds</li>
          </ul>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex justify-between mt-8">
        <button
          onClick={onPrevious}
          className="px-6 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
        >
          Previous
        </button>
        <button
          onClick={onNext}
          disabled={!canProceed}
          className="px-6 py-2 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Next
        </button>
      </div>
    </div>
  );
};