import React, { useState } from 'react';
import { useScraping } from '../../contexts/ScrapingContext';

interface ConfigurationPanelProps {
  onNext: () => void;
}

export const ConfigurationPanel: React.FC<ConfigurationPanelProps> = ({ onNext }) => {
  const { currentConfig, setConfig } = useScraping();
  const [outputFormat, setOutputFormat] = useState<'sheets' | 'csv' | 'json'>(currentConfig?.outputFormat || 'sheets');
  const [maxPages, setMaxPages] = useState(currentConfig?.maxPages || 10);
  const [delay, setDelay] = useState(currentConfig?.delay || 2000);

  const handleSave = () => {
    if (currentConfig) {
      setConfig({
        ...currentConfig,
        outputFormat,
        maxPages,
        delay
      });
    }
    onNext();
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
          Configure Scraping Parameters
        </h2>

        <div className="grid md:grid-cols-2 gap-6">
          {/* Output Format */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Output Format
            </label>
            <select
              value={outputFormat}
              onChange={(e) => setOutputFormat(e.target.value as any)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
            >
              <option value="sheets">Google Sheets</option>
              <option value="csv">CSV File</option>
              <option value="json">JSON File</option>
            </select>
          </div>

          {/* Max Pages */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Max Pages per URL
            </label>
            <input
              type="number"
              value={maxPages}
              onChange={(e) => setMaxPages(parseInt(e.target.value))}
              min="1"
              max="100"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
            />
          </div>

          {/* Delay */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Delay Between Requests (ms)
            </label>
            <input
              type="number"
              value={delay}
              onChange={(e) => setDelay(parseInt(e.target.value))}
              min="500"
              max="10000"
              step="500"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
            />
          </div>
        </div>

        <div className="flex justify-end mt-6">
          <button
            onClick={handleSave}
            className="px-6 py-2 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 transition-colors"
          >
            Preview Data
          </button>
        </div>
      </div>
    </div>
  );
};