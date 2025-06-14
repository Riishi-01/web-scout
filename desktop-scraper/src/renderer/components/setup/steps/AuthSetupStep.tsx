import React, { useState } from 'react';
import { useAuth } from '../../../contexts/AuthContext';

interface AuthSetupStepProps {
  onNext: () => void;
  onPrevious: () => void;
}

export const AuthSetupStep: React.FC<AuthSetupStepProps> = ({ onNext, onPrevious }) => {
  const { authStatus, loading, login } = useAuth();
  const [isAuthenticating, setIsAuthenticating] = useState(false);

  const handleLogin = async () => {
    try {
      setIsAuthenticating(true);
      await login();
    } catch (error) {
      console.error('Authentication failed:', error);
    } finally {
      setIsAuthenticating(false);
    }
  };

  const canProceed = authStatus.authenticated;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
          Connect Google Account
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          Connect your Google account to enable Sheets export
        </p>
      </div>

      <div className="max-w-md mx-auto text-center">
        {authStatus.authenticated ? (
          <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-6">
            <div className="w-16 h-16 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-green-900 dark:text-green-200 mb-2">
              Successfully Connected!
            </h3>
            {authStatus.userInfo && (
              <p className="text-green-800 dark:text-green-300">
                Logged in as {authStatus.userInfo.name} ({authStatus.userInfo.email})
              </p>
            )}
          </div>
        ) : (
          <div>
            <div className="mb-6">
              <svg className="w-16 h-16 text-gray-400 mx-auto mb-4" fill="currentColor" viewBox="0 0 24 24">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                Google Account Required
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                To export scraped data to Google Sheets, please authenticate with your Google account.
              </p>
            </div>

            <button
              onClick={handleLogin}
              disabled={isAuthenticating || loading}
              className="w-full flex items-center justify-center px-6 py-3 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isAuthenticating || loading ? (
                <div className="flex items-center">
                  <div className="spinner mr-2"></div>
                  Authenticating...
                </div>
              ) : (
                <>
                  <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                  </svg>
                  Continue with Google
                </>
              )}
            </button>

            <p className="text-xs text-gray-500 dark:text-gray-400 mt-4">
              This is optional. You can skip this step and export to CSV/JSON instead.
            </p>
          </div>
        )}
      </div>

      <div className="flex justify-between mt-8">
        <button
          onClick={onPrevious}
          className="px-6 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
        >
          Previous
        </button>
        <button
          onClick={onNext}
          className="px-6 py-2 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 transition-colors"
        >
          {canProceed ? 'Next' : 'Skip for Now'}
        </button>
      </div>
    </div>
  );
};