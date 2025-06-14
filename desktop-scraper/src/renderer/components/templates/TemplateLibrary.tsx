import React from 'react';

export const TemplateLibrary: React.FC = () => {
  const templates = [
    {
      id: 'ecommerce',
      name: 'E-commerce Products',
      description: 'Extract product listings with names, prices, and ratings',
      prompt: 'Extract product listings with product name, price, rating, and availability status',
      category: 'E-commerce'
    },
    {
      id: 'jobs',
      name: 'Job Listings',
      description: 'Scrape job postings with titles, companies, and locations',
      prompt: 'Extract job listings with job title, company name, location, salary, and job description',
      category: 'Jobs'
    },
    {
      id: 'realestate',
      name: 'Real Estate',
      description: 'Property listings with prices, locations, and features',
      prompt: 'Extract real estate listings with property price, location, bedrooms, bathrooms, and square footage',
      category: 'Real Estate'
    },
    {
      id: 'news',
      name: 'News Articles',
      description: 'Article headlines, authors, and publication dates',
      prompt: 'Extract news articles with headline, author, publication date, and article summary',
      category: 'News'
    }
  ];

  return (
    <div className="max-w-6xl mx-auto">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
          Template Library
        </h2>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {templates.map((template) => (
            <div key={template.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:shadow-lg transition-shadow">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  {template.name}
                </h3>
                <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-xs rounded-full">
                  {template.category}
                </span>
              </div>
              <p className="text-gray-600 dark:text-gray-400 text-sm mb-4">
                {template.description}
              </p>
              <div className="mb-4">
                <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                  Template Prompt:
                </label>
                <div className="p-2 bg-gray-50 dark:bg-gray-700 rounded text-xs text-gray-700 dark:text-gray-300">
                  {template.prompt}
                </div>
              </div>
              <button className="w-full px-3 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 transition-colors">
                Use Template
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};