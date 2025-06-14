import React from 'react';

interface CompletionStepProps {
  onComplete: () => void;
  onPrevious: () => void;
}

export const CompletionStep: React.FC<CompletionStepProps> = ({ onComplete, onPrevious }) => {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
      <div className="text-center mb-8">
        <div className="w-20 h-20 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center mx-auto mb-6">
          <svg className="w-10 h-10 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
          Setup Complete!
        </h2>
        <p className="text-lg text-gray-600 dark:text-gray-400 mb-8">
          Your Local Web Scraper is now ready to use
        </p>
      </div>

      <div className="max-w-2xl mx-auto">
        <div className="grid md:grid-cols-2 gap-6 mb-8">
          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              What's Ready
            </h3>
            <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
              <li className="flex items-center">
                <svg className="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                AI Model Loaded
              </li>
              <li className="flex items-center">
                <svg className="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                Google Account Connected
              </li>
              <li className="flex items-center">
                <svg className="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                Browser Engine Ready
              </li>
              <li className="flex items-center">
                <svg className="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                Test Completed
              </li>
            </ul>
          </div>

          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Next Steps
            </h3>
            <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
              <li>• Start with simple scraping tasks</li>
              <li>• Use natural language prompts</li>
              <li>• Preview data before full extraction</li>
              <li>• Export to Google Sheets with one click</li>
              <li>• Check documentation for advanced features</li>
            </ul>
          </div>
        </div>

        <div className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 rounded-lg p-6 mb-8">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
            🚀 Quick Start Tips
          </h3>
          <div className="grid md:grid-cols-2 gap-4 text-sm">
            <div>
              <h4 className="font-medium text-gray-900 dark:text-white mb-1">Example Prompts:</h4>
              <ul className="text-gray-600 dark:text-gray-400 space-y-1">
                <li>• "Extract product listings from store.com"</li>
                <li>• "Scrape job postings for Python developers"</li>
                <li>• "Get article titles and authors from news site"</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium text-gray-900 dark:text-white mb-1">Features:</h4>
              <ul className="text-gray-600 dark:text-gray-400 space-y-1">
                <li>• Live preview with 50 sample records</li>
                <li>• Anti-detection mechanisms built-in</li>
                <li>• Multiple export formats available</li>
              </ul>
            </div>
          </div>
        </div>

        <div className="text-center">
          <button
            onClick={onComplete}
            className="px-8 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium rounded-md hover:from-blue-700 hover:to-purple-700 transition-colors"
          >
            Start Scraping
          </button>
        </div>
      </div>

      <div className="flex justify-between mt-8">
        <button
          onClick={onPrevious}
          className="px-6 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
        >
          Previous
        </button>
        <div></div>
      </div>
    </div>
  );
};