import React, { useState, useEffect } from 'react';
import { useTheme } from '../../contexts/ThemeContext';
import { useAuth } from '../../contexts/AuthContext';
import { useModel } from '../../contexts/ModelContext';

export const SettingsPanel: React.FC = () => {
  const { theme, setTheme } = useTheme();
  const { authStatus, logout } = useAuth();
  const { status: modelStatus, loadModel } = useModel();
  const [autoLaunch, setAutoLaunch] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const autoLaunchSetting = await window.electronAPI.settings.get('autoLaunch');
      setAutoLaunch(autoLaunchSetting || false);
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
  };

  const handleAutoLaunchChange = async (enabled: boolean) => {
    try {
      await window.electronAPI.settings.set('autoLaunch', enabled);
      setAutoLaunch(enabled);
    } catch (error) {
      console.error('Failed to save auto-launch setting:', error);
    }
  };

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const handleLoadModel = async () => {
    try {
      await loadModel();
    } catch (error) {
      console.error('Failed to load model:', error);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
          Settings
        </h2>

        <div className="space-y-8">
          {/* Appearance */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Appearance
            </h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Theme
                </label>
                <select
                  value={theme}
                  onChange={(e) => setTheme(e.target.value as any)}
                  className="w-48 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                >
                  <option value="light">Light</option>
                  <option value="dark">Dark</option>
                  <option value="system">System</option>
                </select>
              </div>
            </div>
          </div>

          {/* Application */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Application
            </h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Auto-launch on startup
                  </label>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Start Local Web Scraper when your computer starts
                  </p>
                </div>
                <button
                  onClick={() => handleAutoLaunchChange(!autoLaunch)}
                  className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                    autoLaunch ? 'bg-blue-600' : 'bg-gray-200 dark:bg-gray-700'
                  }`}
                >
                  <span
                    className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                      autoLaunch ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>
            </div>
          </div>

          {/* AI Model */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              AI Model
            </h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div>
                  <div className="text-sm font-medium text-gray-900 dark:text-white">
                    TinyLlama Web Scraper Model
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    Status: {modelStatus.loaded ? 'Loaded' : modelStatus.loading ? 'Loading...' : 'Not Loaded'}
                  </div>
                  {modelStatus.modelInfo && (
                    <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      Version: {modelStatus.modelInfo.version} • 
                      Size: {(modelStatus.modelInfo.size / 1024 / 1024).toFixed(1)} MB
                    </div>
                  )}
                </div>
                <button
                  onClick={handleLoadModel}
                  disabled={modelStatus.loading}
                  className="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
                >
                  {modelStatus.loading ? 'Loading...' : modelStatus.loaded ? 'Reload' : 'Load Model'}
                </button>
              </div>
            </div>
          </div>

          {/* Google Account */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Google Account
            </h3>
            <div className="space-y-4">
              {authStatus.authenticated ? (
                <div className="flex items-center justify-between p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                  <div className="flex items-center space-x-3">
                    {authStatus.userInfo?.picture && (
                      <img
                        src={authStatus.userInfo.picture}
                        alt={authStatus.userInfo.name}
                        className="w-10 h-10 rounded-full"
                      />
                    )}
                    <div>
                      <div className="text-sm font-medium text-green-900 dark:text-green-200">
                        {authStatus.userInfo?.name}
                      </div>
                      <div className="text-xs text-green-700 dark:text-green-300">
                        {authStatus.userInfo?.email}
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={handleLogout}
                    className="px-4 py-2 bg-red-600 text-white text-sm rounded-md hover:bg-red-700 transition-colors"
                  >
                    Disconnect
                  </button>
                </div>
              ) : (
                <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div className="text-sm text-gray-700 dark:text-gray-300">
                    No Google account connected. Connect an account to enable Google Sheets export.
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* About */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              About
            </h3>
            <div className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
              <div>Local Web Scraper v1.0.0</div>
              <div>AI-powered desktop web scraping application</div>
              <div>Built with Electron, React, and TinyLlama</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};