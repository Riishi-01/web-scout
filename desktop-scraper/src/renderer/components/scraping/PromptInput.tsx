import React, { useState } from 'react';
import { useScraping } from '../../contexts/ScrapingContext';

interface PromptInputProps {
  onNext: () => void;
}

export const PromptInput: React.FC<PromptInputProps> = ({ onNext }) => {
  const [prompt, setPrompt] = useState('');
  const [urls, setUrls] = useState<string[]>(['']);
  const { setConfig } = useScraping();

  const handleAddUrl = () => {
    setUrls([...urls, '']);
  };

  const handleRemoveUrl = (index: number) => {
    if (urls.length > 1) {
      setUrls(urls.filter((_, i) => i !== index));
    }
  };

  const handleUrlChange = (index: number, value: string) => {
    const newUrls = [...urls];
    newUrls[index] = value;
    setUrls(newUrls);
  };

  const handleSubmit = () => {
    const validUrls = urls.filter(url => url.trim() !== '');
    
    if (prompt.trim() && validUrls.length > 0) {
      setConfig({
        prompt: prompt.trim(),
        urls: validUrls,
        outputFormat: 'sheets',
        maxPages: 10,
        delay: 2000
      });
      onNext();
    }
  };

  const isValid = prompt.trim() !== '' && urls.some(url => url.trim() !== '');

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
          Describe Your Scraping Task
        </h2>

        {/* Prompt Input */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            What do you want to scrape?
          </label>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Example: Extract product listings with names, prices, and ratings from an e-commerce site"
            className="w-full h-32 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white resize-none"
          />
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Describe in natural language what data you want to extract
          </p>
        </div>

        {/* URL Inputs */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Target URLs
          </label>
          <div className="space-y-2">
            {urls.map((url, index) => (
              <div key={index} className="flex items-center space-x-2">
                <input
                  type="url"
                  value={url}
                  onChange={(e) => handleUrlChange(index, e.target.value)}
                  placeholder="https://example.com/products"
                  className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                />
                {urls.length > 1 && (
                  <button
                    onClick={() => handleRemoveUrl(index)}
                    className="p-2 text-red-600 hover:text-red-800 transition-colors"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                )}
              </div>
            ))}
          </div>
          <button
            onClick={handleAddUrl}
            className="mt-2 flex items-center text-sm text-blue-600 hover:text-blue-800 transition-colors"
          >
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            Add another URL
          </button>
        </div>

        {/* Example prompts */}
        <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
          <h3 className="text-sm font-medium text-blue-900 dark:text-blue-200 mb-2">
            Example Prompts:
          </h3>
          <div className="space-y-1 text-sm text-blue-800 dark:text-blue-300">
            <div>• "Extract job listings with title, company, location, and salary"</div>
            <div>• "Scrape product names, prices, and customer ratings"</div>
            <div>• "Get article headlines, authors, and publication dates"</div>
            <div>• "Extract real estate listings with price, location, and features"</div>
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex justify-end">
          <button
            onClick={handleSubmit}
            disabled={!isValid}
            className="px-6 py-2 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Configure Scraping
          </button>
        </div>
      </div>
    </div>
  );
};