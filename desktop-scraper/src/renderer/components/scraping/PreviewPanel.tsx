import React, { useState, useEffect } from 'react';
import { useScraping } from '../../contexts/ScrapingContext';

interface PreviewPanelProps {
  onNext: () => void;
}

export const PreviewPanel: React.FC<PreviewPanelProps> = ({ onNext }) => {
  const { currentConfig, previewResult, previewScraping, startScraping } = useScraping();
  const [isGeneratingPreview, setIsGeneratingPreview] = useState(false);

  useEffect(() => {
    if (currentConfig && !previewResult) {
      handleGeneratePreview();
    }
  }, [currentConfig]);

  const handleGeneratePreview = async () => {
    if (!currentConfig) return;

    try {
      setIsGeneratingPreview(true);
      await previewScraping(currentConfig);
    } catch (error) {
      console.error('Preview failed:', error);
    } finally {
      setIsGeneratingPreview(false);
    }
  };

  const handleStartScraping = async () => {
    if (!currentConfig) return;
    
    try {
      await startScraping(currentConfig);
      onNext();
    } catch (error) {
      console.error('Failed to start scraping:', error);
    }
  };

  return (
    <div className="max-w-6xl mx-auto">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            Data Preview
          </h2>
          <button
            onClick={handleGeneratePreview}
            disabled={isGeneratingPreview}
            className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 disabled:opacity-50 transition-colors"
          >
            {isGeneratingPreview ? 'Generating...' : 'Refresh Preview'}
          </button>
        </div>

        {isGeneratingPreview ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-4"></div>
            <p className="text-gray-600 dark:text-gray-400">Generating preview...</p>
          </div>
        ) : previewResult ? (
          <div>
            {/* Quality Assessment */}
            <div className="grid grid-cols-4 gap-4 mb-6">
              <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg text-center">
                <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                  {previewResult.qualityAssessment.completeness}%
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Completeness</div>
              </div>
              <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg text-center">
                <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                  {previewResult.qualityAssessment.consistency}%
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Consistency</div>
              </div>
              <div className="bg-purple-50 dark:bg-purple-900/20 p-4 rounded-lg text-center">
                <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                  {previewResult.qualityAssessment.accuracy}%
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Accuracy</div>
              </div>
              <div className="bg-orange-50 dark:bg-orange-900/20 p-4 rounded-lg text-center">
                <div className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                  {previewResult.qualityAssessment.overallScore}%
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Overall Score</div>
              </div>
            </div>

            {/* Sample Data */}
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
                Sample Data ({previewResult.sampleData.length} records)
              </h3>
              <div className="overflow-x-auto border border-gray-200 dark:border-gray-700 rounded-lg">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                  <thead className="bg-gray-50 dark:bg-gray-700">
                    <tr>
                      {previewResult.extractedFields.map((field, index) => (
                        <th
                          key={index}
                          className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider"
                        >
                          {field}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                    {previewResult.sampleData.slice(0, 10).map((record, index) => (
                      <tr key={index}>
                        {previewResult.extractedFields.map((field, fieldIndex) => (
                          <td
                            key={fieldIndex}
                            className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100"
                          >
                            {record[field] || '-'}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex justify-end space-x-4">
              <button
                onClick={handleGeneratePreview}
                className="px-6 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                Regenerate Preview
              </button>
              <button
                onClick={handleStartScraping}
                className="px-6 py-2 bg-green-600 text-white font-medium rounded-md hover:bg-green-700 transition-colors"
              >
                Start Full Scraping
              </button>
            </div>
          </div>
        ) : (
          <div className="text-center py-12">
            <p className="text-gray-600 dark:text-gray-400">No preview available</p>
          </div>
        )}
      </div>
    </div>
  );
};