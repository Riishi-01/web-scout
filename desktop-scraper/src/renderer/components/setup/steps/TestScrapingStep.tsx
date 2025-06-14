import React, { useState } from 'react';

interface TestScrapingStepProps {
  onNext: () => void;
  onPrevious: () => void;
}

export const TestScrapingStep: React.FC<TestScrapingStepProps> = ({ onNext, onPrevious }) => {
  const [testCompleted, setTestCompleted] = useState(false);
  const [isRunning, setIsRunning] = useState(false);

  const handleRunTest = async () => {
    setIsRunning(true);
    // Simulate test scraping
    setTimeout(() => {
      setIsRunning(false);
      setTestCompleted(true);
    }, 3000);
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
          Test Scraping
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          Let's test the system with a simple scraping example
        </p>
      </div>

      <div className="max-w-2xl mx-auto">
        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Sample Task: Scrape Product Listings
          </h3>
          <div className="space-y-3 text-sm">
            <div className="flex">
              <span className="text-gray-500 dark:text-gray-400 w-20">URL:</span>
              <span className="text-gray-900 dark:text-white">https://example-store.com/products</span>
            </div>
            <div className="flex">
              <span className="text-gray-500 dark:text-gray-400 w-20">Goal:</span>
              <span className="text-gray-900 dark:text-white">Extract product names and prices</span>
            </div>
            <div className="flex">
              <span className="text-gray-500 dark:text-gray-400 w-20">Format:</span>
              <span className="text-gray-900 dark:text-white">Google Sheets</span>
            </div>
          </div>
        </div>

        {!testCompleted ? (
          <div className="text-center">
            <button
              onClick={handleRunTest}
              disabled={isRunning}
              className="px-8 py-3 bg-green-600 text-white font-medium rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isRunning ? (
                <div className="flex items-center">
                  <div className="spinner mr-2"></div>
                  Running Test...
                </div>
              ) : (
                'Run Test Scraping'
              )}
            </button>
          </div>
        ) : (
          <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-6">
            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-green-900 dark:text-green-200 mb-2">
                Test Completed Successfully!
              </h3>
              <p className="text-green-800 dark:text-green-300 mb-4">
                Extracted 25 products in 2.3 seconds
              </p>
              <div className="bg-white dark:bg-gray-800 rounded border p-3 text-left text-sm">
                <div className="font-medium mb-2">Sample Results:</div>
                <div className="space-y-1 text-gray-600 dark:text-gray-400">
                  <div>• Wireless Headphones - $89.99</div>
                  <div>• Bluetooth Speaker - $45.00</div>
                  <div>• USB Cable - $12.99</div>
                  <div>• And 22 more items...</div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="flex justify-between mt-8">
        <button
          onClick={onPrevious}
          className="px-6 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
        >
          Previous
        </button>
        <button
          onClick={onNext}
          disabled={!testCompleted}
          className="px-6 py-2 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Complete Setup
        </button>
      </div>
    </div>
  );
};