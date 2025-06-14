import React, { useState, useEffect } from 'react';
import { ThemeProvider } from './contexts/ThemeContext';
import { AuthProvider } from './contexts/AuthContext';
import { ModelProvider } from './contexts/ModelContext';
import { ScrapingProvider } from './contexts/ScrapingContext';
import { AppLayout } from './components/layout/AppLayout';
import { SetupWizard } from './components/setup/SetupWizard';
import { LoadingScreen } from './components/ui/LoadingScreen';
import { ErrorBoundary } from './components/ui/ErrorBoundary';
import './styles/globals.css';

interface AppState {
  isFirstTime: boolean;
  loading: boolean;
  error?: string;
}

const App: React.FC = () => {
  const [appState, setAppState] = useState<AppState>({
    isFirstTime: false,
    loading: true
  });

  useEffect(() => {
    // Apply dark mode by default
    document.documentElement.classList.add('dark');
    initializeApp();
  }, []);

  const initializeApp = async () => {
    try {
      console.log('🌐 Initializing Local Web Scraper in browser mode');
      
      // Check localStorage for first time (web mode)
      const isFirstTime = localStorage.getItem('firstTime') !== 'false';
      
      // Check if the local server is running
      try {
        const response = await fetch('http://localhost:8000/health');
        if (!response.ok) {
          throw new Error('Server not responding');
        }
        const health = await response.json();
        console.log('✅ Local server is running:', health);
      } catch (serverError) {
        console.error('❌ Local server not available:', serverError);
        setAppState({
          isFirstTime: false,
          loading: false,
          error: 'Local server not running. Please start the web server with: python web_server.py'
        });
        return;
      }
      
      setAppState({
        isFirstTime,
        loading: false
      });
    } catch (error) {
      console.error('App initialization failed:', error);
      setAppState({
        isFirstTime: false,
        loading: false,
        error: error instanceof Error ? error.message : 'Failed to initialize app'
      });
    }
  };

  const handleSetupComplete = async () => {
    // Mark setup as completed in localStorage (web mode)
    localStorage.setItem('firstTime', 'false');
    setAppState(prev => ({ ...prev, isFirstTime: false }));
  };

  if (appState.loading) {
    return <LoadingScreen message="Initializing Local Web Scraper..." />;
  }

  if (appState.error) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        backgroundColor: '#f9fafb',
        fontFamily: 'Inter, sans-serif'
      }}>
        <div style={{ textAlign: 'center', padding: '2rem' }}>
          <h1 style={{
            fontSize: '1.5rem',
            fontWeight: 'bold',
            color: '#dc2626',
            marginBottom: '1rem'
          }}>
            Initialization Error
          </h1>
          <p style={{
            color: '#6b7280',
            marginBottom: '1.5rem'
          }}>
            {appState.error}
          </p>
          <button
            onClick={() => window.location.reload()}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: '#2563eb',
              color: 'white',
              border: 'none',
              borderRadius: '0.375rem',
              cursor: 'pointer',
              fontSize: '0.875rem'
            }}
            onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#1d4ed8'}
            onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#2563eb'}
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <ErrorBoundary>
      <ThemeProvider>
        <AuthProvider>
          <ModelProvider>
            <ScrapingProvider>
              {appState.isFirstTime ? (
                <SetupWizard onComplete={handleSetupComplete} />
              ) : (
                <AppLayout />
              )}
            </ScrapingProvider>
          </ModelProvider>
        </AuthProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
};

export default App;