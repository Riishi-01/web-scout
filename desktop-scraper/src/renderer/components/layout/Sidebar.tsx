import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useModel } from '../../contexts/ModelContext';
import { useScraping } from '../../contexts/ScrapingContext';

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ collapsed, onToggle }) => {
  const [activeTab, setActiveTab] = useState('scraper');
  const { authStatus } = useAuth();
  const { status: modelStatus } = useModel();
  const { recentTasks } = useScraping();

  const navigationItems = [
    {
      id: 'scraper',
      name: 'Web Scraper',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9v-9m0-9v9" />
        </svg>
      )
    },
    {
      id: 'history',
      name: 'History',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      badge: recentTasks.length > 0 ? recentTasks.length : undefined
    },
    {
      id: 'templates',
      name: 'Templates',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      )
    },
    {
      id: 'settings',
      name: 'Settings',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      )
    }
  ];

  return (
    <div className={`bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 transition-all duration-300 ${collapsed ? 'w-16' : 'w-64'}`}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
        {!collapsed && (
          <h1 className="text-lg font-semibold text-gray-900 dark:text-white">
            Local Scraper
          </h1>
        )}
        <button
          onClick={onToggle}
          className="p-1 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
        >
          <svg
            className={`w-4 h-4 text-gray-500 dark:text-gray-400 transition-transform ${collapsed ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
          </svg>
        </button>
      </div>

      {/* Status Indicators */}
      {!collapsed && (
        <div className="p-4 space-y-3">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600 dark:text-gray-400">AI Model</span>
            <div className={`flex items-center ${modelStatus.loaded ? 'text-green-600' : 'text-red-600'}`}>
              <div className={`w-2 h-2 rounded-full mr-2 ${modelStatus.loaded ? 'bg-green-500' : 'bg-red-500'}`}></div>
              {modelStatus.loaded ? 'Ready' : 'Not Loaded'}
            </div>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600 dark:text-gray-400">Google</span>
            <div className={`flex items-center ${authStatus.authenticated ? 'text-green-600' : 'text-gray-600'}`}>
              <div className={`w-2 h-2 rounded-full mr-2 ${authStatus.authenticated ? 'bg-green-500' : 'bg-gray-500'}`}></div>
              {authStatus.authenticated ? 'Connected' : 'Not Connected'}
            </div>
          </div>
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 px-4 py-6">
        <ul className="space-y-2">
          {navigationItems.map((item) => (
            <li key={item.id}>
              <button
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                  activeTab === item.id
                    ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300'
                    : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
              >
                <span className="flex-shrink-0">{item.icon}</span>
                {!collapsed && (
                  <>
                    <span className="ml-3 flex-1 text-left">{item.name}</span>
                    {item.badge && (
                      <span className="ml-2 px-2 py-1 bg-blue-600 text-white text-xs rounded-full">
                        {item.badge}
                      </span>
                    )}
                  </>
                )}
              </button>
            </li>
          ))}
        </ul>
      </nav>

      {/* Footer */}
      {!collapsed && (
        <div className="p-4 border-t border-gray-200 dark:border-gray-700">
          <div className="text-xs text-gray-500 dark:text-gray-400 text-center">
            Local Web Scraper v1.0.0
          </div>
        </div>
      )}
    </div>
  );
};