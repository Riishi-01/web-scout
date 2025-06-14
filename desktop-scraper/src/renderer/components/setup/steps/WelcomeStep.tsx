import React from 'react';

interface WelcomeStepProps {
  onNext: () => void;
}

export const WelcomeStep: React.FC<WelcomeStepProps> = ({ onNext }) => {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
      <div className="text-center mb-8">
        <div className="mb-6">
          <div className="mx-auto w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9v-9m0-9v9" />
            </svg>
          </div>
        </div>
        <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
          Welcome to Local Web Scraper
        </h2>
        <p className="text-lg text-gray-600 dark:text-gray-400 mb-8">
          The most powerful desktop web scraping tool with offline AI capabilities
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-6 mb-8">
        <div className="text-center p-4">
          <div className="w-12 h-12 bg-green-100 dark:bg-green-900 rounded-lg flex items-center justify-center mx-auto mb-3">
            <svg className="w-6 h-6 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </div>
          <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Offline AI</h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Fine-tuned TinyLlama model runs locally for privacy and speed
          </p>
        </div>

        <div className="text-center p-4">
          <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center mx-auto mb-3">
            <svg className="w-6 h-6 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
            </svg>
          </div>
          <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Natural Language</h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Just describe what you want to scrape in plain English
          </p>
        </div>

        <div className="text-center p-4">
          <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900 rounded-lg flex items-center justify-center mx-auto mb-3">
            <svg className="w-6 h-6 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Google Sheets</h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Export directly to Google Sheets with one click
          </p>
        </div>

        <div className="text-center p-4">
          <div className="w-12 h-12 bg-red-100 dark:bg-red-900 rounded-lg flex items-center justify-center mx-auto mb-3">
            <svg className="w-6 h-6 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Privacy First</h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            All processing happens locally - your data never leaves your computer
          </p>
        </div>
      </div>

      <div className="text-center">
        <button
          onClick={onNext}
          className="px-8 py-3 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 transition-colors"
        >
          Let's Get Started
        </button>
      </div>
    </div>
  );
};