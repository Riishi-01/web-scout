import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface ModelInfo {
  name: string;
  version: string;
  size: number;
  quantization: string;
}

interface ModelPerformance {
  loadTime: number;
  avgInferenceTime: number;
  memoryUsage: number;
}

interface ModelStatus {
  loaded: boolean;
  loading: boolean;
  error?: string;
  modelInfo?: ModelInfo;
  performance?: ModelPerformance;
}

interface ModelContextType {
  status: ModelStatus;
  loadModel: () => Promise<void>;
  runInference: (prompt: string, options?: any) => Promise<string>;
  refreshStatus: () => Promise<void>;
}

export const ModelContext = createContext<ModelContextType | undefined>(undefined);

interface ModelProviderProps {
  children: ReactNode;
}

export const ModelProvider: React.FC<ModelProviderProps> = ({ children }) => {
  const [status, setStatus] = useState<ModelStatus>({
    loaded: false,
    loading: false
  });

  useEffect(() => {
    checkModelStatus();
    
    // Only set up event listeners if in Electron environment
    if (typeof window !== 'undefined' && window.electronAPI?.on) {
      // Listen for model events from main process
      const unsubscribeLoading = window.electronAPI.on('model-loading', () => {
        setStatus(prev => ({ ...prev, loading: true, error: undefined }));
      });

      const unsubscribeReady = window.electronAPI.on('model-ready', (modelStatus: ModelStatus) => {
        setStatus(modelStatus);
      });

      const unsubscribeError = window.electronAPI.on('model-error', (error: string) => {
        setStatus(prev => ({ ...prev, loading: false, error }));
      });

      return () => {
        if (unsubscribeLoading) unsubscribeLoading();
        if (unsubscribeReady) unsubscribeReady();
        if (unsubscribeError) unsubscribeError();
      };
    }
  }, []);

  const checkModelStatus = async () => {
    try {
      // Use web API instead of Electron IPC
      const response = await fetch('http://localhost:8000/api/model/status');
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const modelStatus = await response.json();
      setStatus(modelStatus);
    } catch (error) {
      console.error('Failed to check model status:', error);
      setStatus(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to connect to local server'
      }));
    }
  };

  const loadModel = async () => {
    try {
      setStatus(prev => ({ ...prev, loading: true, error: undefined }));
      
      // Use web API to load model
      const response = await fetch('http://localhost:8000/api/model/load', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      await checkModelStatus();
    } catch (error) {
      console.error('Failed to load model:', error);
      setStatus(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Failed to load model'
      }));
      throw error;
    }
  };

  const runInference = async (prompt: string, options?: any): Promise<string> => {
    if (!status.loaded) {
      throw new Error('Model not loaded');
    }

    try {
      // Use web API for inference (this will be handled by the scraping context)
      // For now, return a placeholder as direct inference isn't typically used in the UI
      console.log('Inference request:', prompt.substring(0, 50));
      return `Inference request received: ${prompt.substring(0, 50)}...`;
    } catch (error) {
      console.error('Inference failed:', error);
      throw new Error(error instanceof Error ? error.message : 'Inference failed');
    }
  };

  const refreshStatus = async () => {
    await checkModelStatus();
  };

  return (
    <ModelContext.Provider value={{
      status,
      loadModel,
      runInference,
      refreshStatus
    }}>
      {children}
    </ModelContext.Provider>
  );
};

export const useModel = (): ModelContextType => {
  const context = useContext(ModelContext);
  if (!context) {
    throw new Error('useModel must be used within a ModelProvider');
  }
  return context;
};