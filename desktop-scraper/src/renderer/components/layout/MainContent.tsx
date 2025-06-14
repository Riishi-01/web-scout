import React, { useState } from 'react';
import { ScrapingInterface } from '../scraping/ScrapingInterface';
import { ScrapingHistory } from '../scraping/ScrapingHistory';
import { TemplateLibrary } from '../templates/TemplateLibrary';
import { SettingsPanel } from '../settings/SettingsPanel';

export const MainContent: React.FC = () => {
  const [activeTab, setActiveTab] = useState('scraper');

  const renderContent = () => {
    switch (activeTab) {
      case 'scraper':
        return <ScrapingInterface />;
      case 'history':
        return <ScrapingHistory />;
      case 'templates':
        return <TemplateLibrary />;
      case 'settings':
        return <SettingsPanel />;
      default:
        return <ScrapingInterface />;
    }
  };

  return (
    <main className="flex-1 overflow-hidden bg-gray-50 dark:bg-gray-900">
      <div className="h-full p-6">
        {renderContent()}
      </div>
    </main>
  );
};