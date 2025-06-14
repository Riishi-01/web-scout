import { EventEmitter } from 'events';
import Store from 'electron-store';
import {
  ProxyConfig,
  ProxyStatus,
  ProxyPoolConfig,
  ProxyProviderConfig,
  ProxyRequest,
  ProxyResponse,
  ProxyTestResult,
  ProxyUsageQuota,
  ProxyProviderType,
  ProxyProtocol,
  ProxyEventMap
} from './types';
import { ProxyPool } from './ProxyPool';
import { ProxyHealthMonitor } from './ProxyHealthMonitor';
import { AbstractProxyProvider } from './providers/AbstractProxyProvider';
import { CustomProxyProvider } from './providers/CustomProxyProvider';

export class ProxyManager extends EventEmitter {
  private store: Store;
  private pool: ProxyPool;
  private healthMonitor: ProxyHealthMonitor;
  private providers: Map<ProxyProviderType, AbstractProxyProvider> = new Map();
  private requestHistory: Map<string, ProxyResponse> = new Map();
  private isInitialized = false;

  constructor(store: Store) {
    super();
    this.store = store;

    // Initialize with default pool configuration
    const poolConfig: ProxyPoolConfig = this.getStoredPoolConfig();
    this.pool = new ProxyPool(poolConfig);
    this.healthMonitor = new ProxyHealthMonitor(this.pool, {
      interval: poolConfig.healthCheckInterval
    });

    this.setupEventHandlers();
  }

  // Initialize the proxy manager
  async initialize(): Promise<void> {
    if (this.isInitialized) {
      return;
    }

    try {
      // Load saved proxies and providers
      await this.loadStoredProxies();
      await this.loadStoredProviders();

      // Start health monitoring
      this.healthMonitor.start();

      this.isInitialized = true;
      this.emit('manager:initialized');
      console.log('ProxyManager initialized successfully');
    } catch (error) {
      console.error('Failed to initialize ProxyManager:', error);
      throw error;
    }
  }

  // Cleanup resources
  async cleanup(): Promise<void> {
    this.healthMonitor.stop();
    
    // Cleanup all providers
    for (const provider of this.providers.values()) {
      await provider.cleanup();
    }
    
    this.providers.clear();
    this.requestHistory.clear();
    this.isInitialized = false;
    
    this.emit('manager:cleanup');
    console.log('ProxyManager cleaned up');
  }

  // Add a proxy provider
  async addProvider(config: ProxyProviderConfig): Promise<void> {
    try {
      let provider: AbstractProxyProvider;

      switch (config.type) {
        case 'custom':
          provider = new CustomProxyProvider(config);
          break;
        // Add other providers here as they're implemented
        default:
          throw new Error(`Unsupported provider type: ${config.type}`);
      }

      await provider.initialize();
      this.providers.set(config.type, provider);

      // Add all proxies from this provider to the pool
      const proxies = provider.getProxies();
      proxies.forEach(proxy => this.pool.addProxy(proxy));

      // Save provider configuration
      this.saveProviderConfig(config);

      this.emit('provider:added', { type: config.type, proxiesCount: proxies.length });
    } catch (error) {
      console.error(`Failed to add provider ${config.type}:`, error);
      throw error;
    }
  }

  // Remove a proxy provider
  async removeProvider(type: ProxyProviderType): Promise<boolean> {
    const provider = this.providers.get(type);
    if (!provider) {
      return false;
    }

    try {
      // Remove all proxies from this provider
      const proxies = provider.getProxies();
      proxies.forEach(proxy => this.pool.removeProxy(proxy.id));

      // Cleanup provider
      await provider.cleanup();
      this.providers.delete(type);

      // Remove from storage
      this.removeProviderConfig(type);

      this.emit('provider:removed', { type, proxiesCount: proxies.length });
      return true;
    } catch (error) {
      console.error(`Failed to remove provider ${type}:`, error);
      return false;
    }
  }

  // Get a proxy for a request
  async getProxyForRequest(request: ProxyRequest): Promise<ProxyConfig | null> {
    if (!this.isInitialized) {
      throw new Error('ProxyManager not initialized');
    }

    const proxy = await this.pool.getProxy(request);
    
    if (proxy) {
      this.emit('proxy:assigned', { requestId: request.id, proxyId: proxy.id });
    } else {
      this.emit('proxy:unavailable', { requestId: request.id });
    }

    return proxy;
  }

  // Record the result of a proxy request
  recordProxyResponse(response: ProxyResponse): void {
    this.pool.recordProxyResponse(response);
    this.requestHistory.set(response.requestId, response);

    // Cleanup old history (keep last 1000 requests)
    if (this.requestHistory.size > 1000) {
      const oldestKey = this.requestHistory.keys().next().value;
      this.requestHistory.delete(oldestKey);
    }

    this.emit('proxy:response_recorded', response);
  }

  // Add a custom proxy
  async addCustomProxy(proxyData: {
    host: string;
    port: number;
    protocol?: ProxyProtocol;
    username?: string;
    password?: string;
    country?: string;
    city?: string;
    name?: string;
  }): Promise<ProxyConfig> {
    let customProvider = this.providers.get('custom') as CustomProxyProvider;
    
    if (!customProvider) {
      // Create custom provider if it doesn't exist
      const config: ProxyProviderConfig = {
        type: 'custom',
        name: 'Custom Proxies',
        credentials: {},
        settings: {},
        enabled: true
      };
      
      customProvider = new CustomProxyProvider(config);
      await customProvider.initialize();
      this.providers.set('custom', customProvider);
    }

    const proxy = await customProvider.addProxy(proxyData);
    this.pool.addProxy(proxy);
    this.saveProxiesToStorage();

    return proxy;
  }

  // Remove a proxy
  async removeProxy(proxyId: string): Promise<boolean> {
    const removed = this.pool.removeProxy(proxyId);
    
    if (removed) {
      // Also remove from provider if it's a custom proxy
      const customProvider = this.providers.get('custom') as CustomProxyProvider;
      if (customProvider) {
        await customProvider.removeProxy(proxyId);
      }
      
      this.saveProxiesToStorage();
      this.emit('proxy:removed_manual', { proxyId });
    }

    return removed;
  }

  // Test a specific proxy
  async testProxy(proxyId: string): Promise<ProxyTestResult> {
    const proxy = this.pool.getProxies().find(p => p.id === proxyId);
    if (!proxy) {
      throw new Error(`Proxy ${proxyId} not found`);
    }

    const provider = this.providers.get(proxy.provider || 'custom');
    if (!provider) {
      throw new Error(`Provider for proxy ${proxyId} not found`);
    }

    return await provider.testProxy(proxyId);
  }

  // Get proxy statistics
  getProxyStats() {
    const poolStats = this.pool.getPoolStats();
    const monitoringStats = this.healthMonitor.getMonitoringStats();
    
    const providerStats = Array.from(this.providers.entries()).map(([type, provider]) => ({
      type,
      ...provider.getStats()
    }));

    return {
      pool: poolStats,
      monitoring: monitoringStats,
      providers: providerStats,
      totalRequests: this.requestHistory.size
    };
  }

  // Get all proxies
  getProxies(): ProxyConfig[] {
    return this.pool.getProxies();
  }

  // Get healthy proxies
  getHealthyProxies(): ProxyConfig[] {
    return this.pool.getHealthyProxies();
  }

  // Get proxy status
  getProxyStatus(proxyId: string): ProxyStatus | null {
    return this.pool.getProxyStatus(proxyId);
  }

  // Update pool configuration
  updatePoolConfig(config: Partial<ProxyPoolConfig>): void {
    this.pool.updateConfig(config);
    this.savePoolConfig();
    this.emit('pool:config_updated', config);
  }

  // Update monitoring configuration
  updateMonitoringConfig(config: { interval?: number; healthCheckUrls?: string[] }): void {
    this.healthMonitor.updateConfig(config);
    this.emit('monitoring:config_updated', config);
  }

  // Force health check on all proxies
  async forceHealthCheck(): Promise<void> {
    await this.healthMonitor.performHealthChecks();
  }

  // Get provider quotas
  async getProviderQuotas(): Promise<ProxyUsageQuota[]> {
    const quotas: ProxyUsageQuota[] = [];
    
    for (const provider of this.providers.values()) {
      try {
        const quota = await provider.getUsageQuota();
        quotas.push(quota);
      } catch (error) {
        console.error(`Failed to get quota for provider:`, error);
      }
    }
    
    return quotas;
  }

  // Private helper methods
  private setupEventHandlers(): void {
    // Forward pool events
    this.pool.on('proxy:selected', (data) => this.emit('proxy:selected', data));
    this.pool.on('proxy:unhealthy', (data) => this.emit('proxy:unhealthy', data));
    this.pool.on('proxy:recovered', (data) => this.emit('proxy:recovered', data));

    // Forward monitoring events
    this.healthMonitor.on('monitoring:health_changed', (data) => this.emit('monitoring:health_changed', data));
    this.healthMonitor.on('monitoring:check_completed', (data) => this.emit('monitoring:check_completed', data));

    // Forward provider events
    this.on('provider:added', () => this.saveProxiesToStorage());
    this.on('provider:removed', () => this.saveProxiesToStorage());
  }

  private getStoredPoolConfig(): ProxyPoolConfig {
    return this.store.get('proxy.poolConfig', {
      strategy: 'round_robin',
      healthCheckInterval: 60000,
      maxRetries: 3,
      retryDelay: 1000,
      failureThreshold: 3,
      recoveryThreshold: 2,
      loadBalancing: true,
      enableGeoMatching: false,
      sessionStickiness: false,
      sessionTimeout: 300000
    }) as ProxyPoolConfig;
  }

  private savePoolConfig(): void {
    // Note: In a real implementation, you'd extract config from pool
    // For now, we'll save the current config when updated
  }

  private async loadStoredProxies(): Promise<void> {
    const proxies = this.store.get('proxy.proxies', []) as ProxyConfig[];
    proxies.forEach(proxy => this.pool.addProxy(proxy));
  }

  private saveProxiesToStorage(): void {
    const proxies = this.pool.getProxies();
    this.store.set('proxy.proxies', proxies);
  }

  private async loadStoredProviders(): Promise<void> {
    const providerConfigs = this.store.get('proxy.providers', []) as ProxyProviderConfig[];
    
    for (const config of providerConfigs) {
      if (config.enabled) {
        try {
          await this.addProvider(config);
        } catch (error) {
          console.error(`Failed to load provider ${config.type}:`, error);
        }
      }
    }
  }

  private saveProviderConfig(config: ProxyProviderConfig): void {
    const configs = this.store.get('proxy.providers', []) as ProxyProviderConfig[];
    const existingIndex = configs.findIndex(c => c.type === config.type);
    
    if (existingIndex >= 0) {
      configs[existingIndex] = config;
    } else {
      configs.push(config);
    }
    
    this.store.set('proxy.providers', configs);
  }

  private removeProviderConfig(type: ProxyProviderType): void {
    const configs = this.store.get('proxy.providers', []) as ProxyProviderConfig[];
    const filtered = configs.filter(c => c.type !== type);
    this.store.set('proxy.providers', filtered);
  }
}