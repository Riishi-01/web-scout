import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface ScrapingConfig {
  id?: string;
  prompt: string;
  urls: string[];
  maxPages?: number;
  delay?: number;
  outputFormat: 'sheets' | 'csv' | 'json';
  outputDestination?: string;
  customSelectors?: string[];
  filters?: Record<string, any>;
}

interface ScrapingProgress {
  currentPage: number;
  totalPages: number;
  recordsExtracted: number;
  currentUrl?: string;
}

interface ScrapingStatus {
  taskId: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: ScrapingProgress;
  startTime: Date;
  estimatedTimeRemaining?: number;
  error?: string;
}

interface PreviewResult {
  success: boolean;
  sampleData: any[];
  extractedFields: string[];
  qualityAssessment: {
    completeness: number;
    consistency: number;
    accuracy: number;
    overallScore: number;
  };
  recommendedSelectors: string[];
  error?: string;
}

interface ScrapingContextType {
  currentConfig: ScrapingConfig | null;
  activeTask: ScrapingStatus | null;
  previewResult: PreviewResult | null;
  recentTasks: ScrapingStatus[];
  setConfig: (config: ScrapingConfig) => void;
  startScraping: (config: ScrapingConfig) => Promise<string>;
  stopScraping: (taskId: string) => Promise<boolean>;
  previewScraping: (config: ScrapingConfig) => Promise<PreviewResult>;
  refreshTaskStatus: (taskId: string) => Promise<void>;
  clearPreview: () => void;
}

const ScrapingContext = createContext<ScrapingContextType | undefined>(undefined);

interface ScrapingProviderProps {
  children: ReactNode;
}

export const ScrapingProvider: React.FC<ScrapingProviderProps> = ({ children }) => {
  const [currentConfig, setCurrentConfig] = useState<ScrapingConfig | null>(null);
  const [activeTask, setActiveTask] = useState<ScrapingStatus | null>(null);
  const [previewResult, setPreviewResult] = useState<PreviewResult | null>(null);
  const [recentTasks, setRecentTasks] = useState<ScrapingStatus[]>([]);

  useEffect(() => {
    // Set up WebSocket connection for real-time updates
    let ws: WebSocket | null = null;
    
    try {
      ws = new WebSocket('ws://localhost:8000/ws');
      
      ws.onopen = () => {
        console.log('WebSocket connected for real-time updates');
      };
      
      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          
          switch (message.type) {
            case 'scraping_progress':
              if (activeTask?.taskId === message.task_id) {
                setActiveTask(prev => prev ? { ...prev, ...message.status } : null);
              }
              updateRecentTask(message.status);
              break;
              
            case 'scraping_complete':
              if (activeTask?.taskId === message.task_id) {
                setActiveTask(prev => prev ? { ...prev, status: 'completed' } : null);
              }
              setRecentTasks(prev => prev.map(task => 
                task.taskId === message.task_id ? { ...task, status: 'completed' as const } : task
              ));
              break;
              
            case 'scraping_error':
              if (activeTask?.taskId === message.task_id) {
                setActiveTask(prev => prev ? { ...prev, status: 'failed', error: message.error } : null);
              }
              setRecentTasks(prev => prev.map(task => 
                task.taskId === message.task_id ? { ...task, status: 'failed' as const, error: message.error } : task
              ));
              break;
              
            case 'model_loaded':
              console.log('Model loaded:', message.status);
              break;
              
            default:
              console.log('Received WebSocket message:', message);
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };
      
      ws.onclose = () => {
        console.log('WebSocket disconnected');
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
      
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
    }

    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [activeTask]);

  const setConfig = (config: ScrapingConfig) => {
    setCurrentConfig(config);
  };

  const startScraping = async (config: ScrapingConfig): Promise<string> => {
    try {
      // Use web API to start scraping
      const response = await fetch('http://localhost:8000/api/scraping/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          prompt: config.prompt,
          max_pages: config.maxPages || 10,
          output_format: config.outputFormat,
          output_destination: config.outputDestination
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      const taskId = result.task_id;
      
      const initialStatus: ScrapingStatus = {
        taskId,
        status: 'pending',
        progress: {
          currentPage: 0,
          totalPages: config.urls.length * (config.maxPages || 1),
          recordsExtracted: 0
        },
        startTime: new Date()
      };

      setActiveTask(initialStatus);
      addRecentTask(initialStatus);
      
      return taskId;
    } catch (error) {
      console.error('Failed to start scraping:', error);
      throw error;
    }
  };

  const stopScraping = async (taskId: string): Promise<boolean> => {
    try {
      // Use web API to stop scraping
      const response = await fetch(`http://localhost:8000/api/scraping/stop/${taskId}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      const stopped = result.status === 'success';
      
      if (stopped && activeTask?.taskId === taskId) {
        setActiveTask(prev => prev ? { ...prev, status: 'cancelled' } : null);
      }
      
      return stopped;
    } catch (error) {
      console.error('Failed to stop scraping:', error);
      throw error;
    }
  };

  const previewScraping = async (config: ScrapingConfig): Promise<PreviewResult> => {
    try {
      // Use web API to preview scraping
      const response = await fetch('http://localhost:8000/api/scraping/preview', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          prompt: config.prompt,
          max_pages: 1,
          output_format: config.outputFormat
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const apiResult = await response.json();
      
      const result: PreviewResult = {
        success: apiResult.success,
        sampleData: apiResult.data || [],
        extractedFields: apiResult.fields || [],
        qualityAssessment: {
          completeness: Math.round(apiResult.quality_score * 100) || 0,
          consistency: Math.round(apiResult.quality_score * 90) || 0,
          accuracy: Math.round(apiResult.quality_score * 95) || 0,
          overallScore: Math.round(apiResult.quality_score * 92) || 0
        },
        recommendedSelectors: apiResult.recommendations || []
      };
      
      setPreviewResult(result);
      return result;
    } catch (error) {
      console.error('Failed to preview scraping:', error);
      const errorResult: PreviewResult = {
        success: false,
        sampleData: [],
        extractedFields: [],
        qualityAssessment: {
          completeness: 0,
          consistency: 0,
          accuracy: 0,
          overallScore: 0
        },
        recommendedSelectors: [],
        error: error instanceof Error ? error.message : 'Preview failed'
      };
      setPreviewResult(errorResult);
      return errorResult;
    }
  };

  const refreshTaskStatus = async (taskId: string): Promise<void> => {
    try {
      // Use web API to get task status
      const response = await fetch(`http://localhost:8000/api/scraping/status/${taskId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const apiStatus = await response.json();
      
      const status: ScrapingStatus = {
        taskId: apiStatus.task_id,
        status: apiStatus.status,
        progress: apiStatus.progress,
        startTime: new Date(), // This should come from the API
        error: apiStatus.error
      };
      
      if (activeTask?.taskId === taskId) {
        setActiveTask(status);
      }
      updateRecentTask(status);
    } catch (error) {
      console.error('Failed to refresh task status:', error);
    }
  };

  const clearPreview = () => {
    setPreviewResult(null);
  };

  const addRecentTask = (task: ScrapingStatus) => {
    setRecentTasks(prev => {
      const updated = [task, ...prev.filter(t => t.taskId !== task.taskId)];
      return updated.slice(0, 10); // Keep only last 10 tasks
    });
  };

  const updateRecentTask = (task: ScrapingStatus) => {
    setRecentTasks(prev => 
      prev.map(t => t.taskId === task.taskId ? task : t)
    );
  };

  return (
    <ScrapingContext.Provider value={{
      currentConfig,
      activeTask,
      previewResult,
      recentTasks,
      setConfig,
      startScraping,
      stopScraping,
      previewScraping,
      refreshTaskStatus,
      clearPreview
    }}>
      {children}
    </ScrapingContext.Provider>
  );
};

export const useScraping = (): ScrapingContextType => {
  const context = useContext(ScrapingContext);
  if (!context) {
    throw new Error('useScraping must be used within a ScrapingProvider');
  }
  return context;
};