export type ProxyProtocol = 'http' | 'https' | 'socks4' | 'socks5';

export type ProxyAuthType = 'none' | 'basic' | 'bearer' | 'ip_whitelist';

export type ProxyRotationStrategy = 'round_robin' | 'random' | 'sticky_session' | 'least_used' | 'fastest';

export type ProxyProviderType = 'brightdata' | 'proxymesh' | 'smartproxy' | 'oxylabs' | 'custom';

export interface ProxyCredentials {
  username?: string;
  password?: string;
  apiKey?: string;
  token?: string;
}

export interface ProxyConfig {
  id: string;
  name: string;
  host: string;
  port: number;
  protocol: ProxyProtocol;
  authType: ProxyAuthType;
  credentials?: ProxyCredentials;
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

export interface ProxyStatus {
  id: string;
  isHealthy: boolean;
  lastChecked: Date;
  responseTime: number;
  successRate: number;
  totalRequests: number;
  failedRequests: number;
  consecutiveFailures: number;
  currentConnections: number;
  error?: string;
  location?: {
    country: string;
    city: string;
    ip: string;
  };
}

export interface ProxyMetrics {
  id: string;
  totalRequests: number;
  successfulRequests: number;
  failedRequests: number;
  averageResponseTime: number;
  totalBandwidth: number;
  cost?: number;
  uptime: number;
  lastHour: {
    requests: number;
    avgResponseTime: number;
    successRate: number;
  };
  lastDay: {
    requests: number;
    avgResponseTime: number;
    successRate: number;
  };
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

export interface ProxyProviderConfig {
  type: ProxyProviderType;
  name: string;
  apiEndpoint?: string;
  credentials: ProxyCredentials;
  settings: Record<string, any>;
  enabled: boolean;
}

export interface ProxyRequest {
  id: string;
  url: string;
  method: string;
  headers?: Record<string, string>;
  timeout?: number;
  retries?: number;
  proxyId?: string;
  requiresStickiness?: boolean;
  geoRequirements?: {
    country?: string;
    city?: string;
  };
  metadata?: Record<string, any>;
}

export interface ProxyResponse {
  requestId: string;
  proxyId: string;
  success: boolean;
  statusCode?: number;
  responseTime: number;
  bandwidth: number;
  error?: string;
  retryCount: number;
  finalUrl?: string;
  headers?: Record<string, string>;
}

export interface ProxyHealthCheck {
  url: string;
  expectedStatus?: number;
  timeout: number;
  headers?: Record<string, string>;
  validateResponse?: (response: any) => boolean;
}

export interface ProxyProviderStats {
  totalProxies: number;
  healthyProxies: number;
  avgResponseTime: number;
  successRate: number;
  totalRequests: number;
  costThisMonth?: number;
  bandwidthUsed: number;
}

export interface GeolocationInfo {
  ip: string;
  country: string;
  countryCode: string;
  city: string;
  region: string;
  timezone: string;
  isp: string;
  accuracy: number;
}

export interface ProxyTestResult {
  proxyId: string;
  success: boolean;
  responseTime?: number;
  error?: string;
  ipAddress?: string;
  location?: GeolocationInfo | null;
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
  bandwidthUsed: number; // in bytes
  bandwidthLimit: number; // in bytes
  resetDate: Date;
  costAccrued: number;
  costLimit?: number;
}

export interface ProxyEvent {
  type: 'health_check' | 'request_success' | 'request_failure' | 'proxy_added' | 'proxy_removed' | 'rotation';
  proxyId: string;
  timestamp: Date;
  data?: any;
}

// Event types for proxy system
export interface ProxyEventMap {
  'proxy:health_changed': { proxyId: string; isHealthy: boolean; status: ProxyStatus };
  'proxy:request_completed': { request: ProxyRequest; response: ProxyResponse };
  'proxy:rotation': { previousProxy: string; newProxy: string; reason: string };
  'proxy:pool_updated': { added: string[]; removed: string[]; total: number };
  'proxy:provider_connected': { provider: ProxyProviderType; proxiesCount: number };
  'proxy:quota_warning': { provider: ProxyProviderType; quota: ProxyUsageQuota; percentage: number };
  'proxy:error': { proxyId?: string; error: string; context?: any };
}