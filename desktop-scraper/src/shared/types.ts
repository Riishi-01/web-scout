// Shared type definitions for the desktop scraper application

// Proxy types
export type ProxyProtocol = 'http' | 'https' | 'socks4' | 'socks5';
export type ProxyProviderType = 'brightdata' | 'proxymesh' | 'smartproxy' | 'oxylabs' | 'custom';
export type ProxyRotationStrategy = 'round_robin' | 'random' | 'sticky_session' | 'least_used' | 'fastest';

export interface ProxyConfig {
  id: string;
  name: string;
  host: string;
  port: number;
  protocol: ProxyProtocol;
  authType: 'none' | 'basic' | 'bearer' | 'ip_whitelist';
  credentials?: {
    username?: string;
    password?: string;
    apiKey?: string;
    token?: string;
  };
  country?: string;
  city?: string;
  provider?: ProxyProviderType;
  sticky?: boolean;
  maxConcurrent?: number;
  timeout?: number;
  retries?: number;
  tags?: string[];
  enabled: boolean;
  createdAt: Date;
  lastUsed?: Date;
}

export interface CustomProxyInput {
  host: string;
  port: number;
  protocol?: ProxyProtocol;
  username?: string;
  password?: string;
  country?: string;
  city?: string;
  name?: string;
  tags?: string[];
}

export interface ProxyTestResult {
  proxyId: string;
  success: boolean;
  responseTime?: number;
  error?: string;
  ipAddress?: string;
  location?: {
    ip: string;
    country: string;
    city: string;
  };
  anonymityLevel?: 'transparent' | 'anonymous' | 'elite';
  protocols: ProxyProtocol[];
  features: {
    javascript: boolean;
    cookies: boolean;
    referer: boolean;
    userAgent: boolean;
  };
}

export interface ProxyUsageQuota {
  provider: ProxyProviderType;
  requestsUsed: number;
  requestsLimit: number;
  bandwidthUsed: number;
  bandwidthLimit: number;
  resetDate: Date;
  costAccrued: number;
  costLimit?: number;
}

export interface ProxyProviderConfig {
  type: ProxyProviderType;
  name: string;
  apiEndpoint?: string;
  credentials: {
    username?: string;
    password?: string;
    apiKey?: string;
    token?: string;
  };
  settings: Record<string, any>;
  enabled: boolean;
}

export interface ProxyPoolConfig {
  strategy: ProxyRotationStrategy;
  healthCheckInterval: number;
  maxRetries: number;
  retryDelay: number;
  failureThreshold: number;
  recoveryThreshold: number;
  loadBalancing: boolean;
  enableGeoMatching: boolean;
  sessionStickiness: boolean;
  sessionTimeout: number;
}

export interface ProxyStats {
  pool: {
    totalProxies: number;
    healthyProxies: number;
    unhealthyProxies: number;
    totalRequests: number;
    totalFailures: number;
    successRate: number;
    avgResponseTime: number;
    activeSessions: number;
    strategy: ProxyRotationStrategy;
  };
  monitoring: {
    isMonitoring: boolean;
    interval: number;
    totalProxies: number;
    healthyProxies: number;
    unhealthyProxies: number;
    avgResponseTime: number;
    lastCheckTime: Date | null;
    activeChecks: number;
  };
  providers: Array<{
    type: ProxyProviderType;
    totalProxies: number;
    healthyProxies: number;
    avgResponseTime: number;
    successRate: number;
    totalRequests: number;
    costThisMonth?: number;
    bandwidthUsed: number;
  }>;
  totalRequests: number;
}

export interface ScrapingConfig {
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

export interface ScrapingProgress {
  currentPage: number;
  totalPages: number;
  recordsExtracted: number;
  currentUrl?: string;
}

export interface ScrapingStatus {
  taskId: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: ScrapingProgress;
  startTime: Date;
  estimatedTimeRemaining?: number;
  error?: string;
}

export interface PreviewResult {
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

export interface ModelInfo {
  name: string;
  version: string;
  size: number;
  quantization: string;
}

export interface ModelPerformance {
  loadTime: number;
  avgInferenceTime: number;
  memoryUsage: number;
}

export interface ModelStatus {
  loaded: boolean;
  loading: boolean;
  error?: string;
  modelInfo?: ModelInfo;
  performance?: ModelPerformance;
}

export interface UserInfo {
  email: string;
  name: string;
  picture?: string;
}

export interface AuthStatus {
  authenticated: boolean;
  userInfo?: UserInfo;
  scopes: string[];
  expiresAt?: Date;
}

// Electron IPC API types
export interface ElectronAPI {
  // Settings methods
  settings: {
    get: (key: string) => Promise<any>;
    set: (key: string, value: any) => Promise<void>;
    delete: (key: string) => Promise<void>;
  };

  // Model methods
  model: {
    getStatus: () => Promise<ModelStatus>;
    loadModel: () => Promise<void>;
    generateText: (prompt: string, options?: any) => Promise<string>;
    analyzeWebPage: (html: string, prompt: string) => Promise<any>;
    generateSelectors: (html: string) => Promise<string[]>;
  };

  // Authentication methods
  auth: {
    getStatus: () => Promise<AuthStatus>;
    startAuth: () => Promise<AuthStatus>;
    logout: () => Promise<void>;
  };

  // Scraping methods
  scraping: {
    startScraping: (config: ScrapingConfig) => Promise<string>;
    stopScraping: (taskId: string) => Promise<boolean>;
    getStatus: (taskId: string) => Promise<ScrapingStatus | null>;
    previewScraping: (config: ScrapingConfig) => Promise<PreviewResult>;
  };

  // Google Sheets methods
  sheets: {
    createSpreadsheet: (title: string, data: any[][]) => Promise<string>;
    readSpreadsheet: (url: string, range?: string) => Promise<any[][]>;
    updateSpreadsheet: (url: string, data: any[][], options?: any) => Promise<void>;
    getSpreadsheetInfo: (url: string) => Promise<any>;
  };

  // Proxy management methods
  proxy: {
    getProxies: () => Promise<ProxyConfig[]>;
    addCustomProxy: (proxyData: CustomProxyInput) => Promise<ProxyConfig>;
    removeProxy: (proxyId: string) => Promise<boolean>;
    testProxy: (proxyId: string) => Promise<ProxyTestResult>;
    getProxyStats: () => Promise<ProxyStats>;
    updatePoolConfig: (config: Partial<ProxyPoolConfig>) => Promise<void>;
    forceHealthCheck: () => Promise<void>;
    addProvider: (config: ProxyProviderConfig) => Promise<void>;
    removeProvider: (type: ProxyProviderType) => Promise<boolean>;
    getProviderQuotas: () => Promise<ProxyUsageQuota[]>;
  };

  // Event handlers
  on: (channel: string, callback: (...args: any[]) => void) => () => void;
  off: (channel: string, callback: (...args: any[]) => void) => void;
  emit: (channel: string, ...args: any[]) => void;

  // App methods
  app: {
    getVersion: () => Promise<string>;
    quit: () => void;
    minimize: () => void;
    maximize: () => void;
    close: () => void;
  };
}

// Window interface is extended in preload.ts