import React from 'react';
import { useTheme } from '../../contexts/ThemeContext';
import { useAuth } from '../../contexts/AuthContext';

export const Header: React.FC = () => {
  const { theme, setTheme } = useTheme();
  const { authStatus } = useAuth();

  const handleMinimize = () => {
    window.electronAPI.app.minimize();
  };

  const handleClose = () => {
    window.electronAPI.app.close();
  };

  return (
    <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-3 electron-app">
      <div className="flex items-center justify-between">
        {/* Left side - Quick actions */}
        <div className="flex items-center space-x-4">
          <button className="flex items-center px-3 py-1.5 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 transition-colors">
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            New Task
          </button>
          
          <div className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400">
            <span>Ready to scrape</span>
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          </div>
        </div>

        {/* Right side - Controls */}
        <div className="flex items-center space-x-4">
          {/* User info */}
          {authStatus.authenticated && authStatus.userInfo && (
            <div className="flex items-center space-x-2 text-sm">
              {authStatus.userInfo.picture && (
                <img
                  src={authStatus.userInfo.picture}
                  alt={authStatus.userInfo.name}
                  className="w-6 h-6 rounded-full"
                />
              )}
              <span className="text-gray-700 dark:text-gray-300">
                {authStatus.userInfo.name}
              </span>
            </div>
          )}

          {/* Theme toggle */}
          <button
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            title="Toggle theme"
          >
            {theme === 'dark' ? (
              <svg className="w-4 h-4 text-gray-600 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            ) : (
              <svg className="w-4 h-4 text-gray-600 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
              </svg>
            )}
          </button>

          {/* Settings */}
          <button className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
            <svg className="w-4 h-4 text-gray-600 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </button>

          {/* Window controls */}
          <div className="flex items-center space-x-1 ml-4">
            <button
              onClick={handleMinimize}
              className="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              <svg className="w-3 h-3 text-gray-600 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
              </svg>
            </button>
            <button
              onClick={handleClose}
              className="p-1.5 rounded hover:bg-red-100 dark:hover:bg-red-900 hover:text-red-600 transition-colors"
            >
              <svg className="w-3 h-3 text-gray-600 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};