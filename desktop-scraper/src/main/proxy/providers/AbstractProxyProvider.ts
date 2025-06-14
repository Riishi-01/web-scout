import { EventEmitter } from 'events';
import {
  ProxyConfig,
  ProxyStatus,
  ProxyProviderConfig,
  ProxyProviderType,
  ProxyTestResult,
  ProxyUsageQuota,
  ProxyProviderStats,
  GeolocationInfo
} from '../types';

export abstract class AbstractProxyProvider extends EventEmitter {
  protected config: ProxyProviderConfig;
  protected proxies: Map<string, ProxyConfig> = new Map();
  protected stats: ProxyProviderStats;

  constructor(config: ProxyProviderConfig) {
    super();
    this.config = config;
    this.stats = {
      totalProxies: 0,
      healthyProxies: 0,
      avgResponseTime: 0,
      successRate: 0,
      totalRequests: 0,
      bandwidthUsed: 0
    };
  }

  // Abstract methods that must be implemented by each provider
  abstract getProviderType(): ProxyProviderType;
  abstract connect(): Promise<void>;
  abstract disconnect(): Promise<void>;
  abstract fetchProxies(): Promise<ProxyConfig[]>;
  abstract testProxy(proxyId: string): Promise<ProxyTestResult>;
  abstract getUsageQuota(): Promise<ProxyUsageQuota>;
  abstract refreshProxyList(): Promise<void>;

  // Common methods with default implementations
  async initialize(): Promise<void> {
    try {
      await this.connect();
      await this.refreshProxyList();
      this.emit('provider:connected', {
        provider: this.getProviderType(),
        proxiesCount: this.proxies.size
      });
    } catch (error) {
      this.emit('provider:error', {
        provider: this.getProviderType(),
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      throw error;
    }
  }

  async cleanup(): Promise<void> {
    try {
      await this.disconnect();
      this.proxies.clear();
      this.emit('provider:disconnected', {
        provider: this.getProviderType()
      });
    } catch (error) {
      console.error(`Cleanup failed for ${this.getProviderType()}:`, error);
    }
  }

  getProxies(): ProxyConfig[] {
    return Array.from(this.proxies.values());
  }

  getProxy(id: string): ProxyConfig | undefined {
    return this.proxies.get(id);
  }

  getHealthyProxies(): ProxyConfig[] {
    return this.getProxies().filter(proxy => proxy.enabled);
  }

  getProxiesByCountry(country: string): ProxyConfig[] {
    return this.getProxies().filter(proxy => 
      proxy.country?.toLowerCase() === country.toLowerCase()
    );
  }

  getProxiesByCity(city: string, country?: string): ProxyConfig[] {
    return this.getProxies().filter(proxy => {
      const cityMatch = proxy.city?.toLowerCase() === city.toLowerCase();
      const countryMatch = !country || proxy.country?.toLowerCase() === country.toLowerCase();
      return cityMatch && countryMatch;
    });
  }

  getStats(): ProxyProviderStats {
    return { ...this.stats };
  }

  updateStats(updates: Partial<ProxyProviderStats>): void {
    this.stats = { ...this.stats, ...updates };
    this.emit('provider:stats_updated', {
      provider: this.getProviderType(),
      stats: this.stats
    });
  }

  protected addProxy(proxy: ProxyConfig): void {
    this.proxies.set(proxy.id, proxy);
    this.stats.totalProxies = this.proxies.size;
    this.emit('proxy:added', { provider: this.getProviderType(), proxy });
  }

  protected removeProxy(proxyId: string): void {
    const proxy = this.proxies.get(proxyId);
    if (proxy) {
      this.proxies.delete(proxyId);
      this.stats.totalProxies = this.proxies.size;
      this.emit('proxy:removed', { provider: this.getProviderType(), proxy });
    }
  }

  protected updateProxy(proxyId: string, updates: Partial<ProxyConfig>): void {
    const proxy = this.proxies.get(proxyId);
    if (proxy) {
      const updatedProxy = { ...proxy, ...updates };
      this.proxies.set(proxyId, updatedProxy);
      this.emit('proxy:updated', { provider: this.getProviderType(), proxy: updatedProxy });
    }
  }

  // Helper method for making HTTP requests with retry logic
  protected async makeRequest(
    url: string, 
    options: RequestInit & { timeout?: number; retries?: number } = {}
  ): Promise<Response> {
    const { timeout = 10000, retries = 3, ...fetchOptions } = options;
    
    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        const response = await fetch(url, {
          ...fetchOptions,
          signal: controller.signal
        });

        clearTimeout(timeoutId);
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return response;
      } catch (error) {
        if (attempt === retries) {
          throw error;
        }
        
        // Wait before retrying (exponential backoff)
        await new Promise(resolve => 
          setTimeout(resolve, Math.pow(2, attempt) * 1000)
        );
      }
    }
    
    throw new Error('Max retries exceeded');
  }

  // Helper method for extracting geolocation from proxy response
  protected async getProxyGeolocation(proxyConfig: ProxyConfig): Promise<GeolocationInfo | null> {
    try {
      // Use a simple IP geolocation service
      const response = await this.makeRequest('http://ip-api.com/json', {
        timeout: 5000,
        retries: 1
      });
      
      const data = await response.json();
      
      if (data.status === 'success') {
        return {
          ip: data.query,
          country: data.country,
          countryCode: data.countryCode,
          city: data.city,
          region: data.regionName,
          timezone: data.timezone,
          isp: data.isp,
          accuracy: 1.0
        };
      }
      
      return null;
    } catch (error) {
      console.warn(`Failed to get geolocation for proxy ${proxyConfig.id}:`, error);
      return null;
    }
  }

  // Helper method for generating proxy URL
  protected buildProxyUrl(proxy: ProxyConfig): string {
    const { protocol, host, port, credentials } = proxy;
    
    if (credentials?.username && credentials?.password) {
      return `${protocol}://${credentials.username}:${credentials.password}@${host}:${port}`;
    }
    
    return `${protocol}://${host}:${port}`;
  }

  // Helper method for validating proxy configuration
  protected validateProxyConfig(config: ProxyConfig): boolean {
    if (!config.id || !config.host || !config.port) {
      return false;
    }
    
    if (config.port < 1 || config.port > 65535) {
      return false;
    }
    
    if (config.authType === 'basic' && (!config.credentials?.username || !config.credentials?.password)) {
      return false;
    }
    
    return true;
  }

  // Helper method for creating a standardized proxy config
  protected createProxyConfig(
    id: string,
    host: string,
    port: number,
    options: Partial<ProxyConfig> = {}
  ): ProxyConfig {
    return {
      id,
      name: options.name || `${this.getProviderType()}-${id}`,
      host,
      port,
      protocol: options.protocol || 'http',
      authType: options.authType || 'none',
      credentials: options.credentials,
      country: options.country,
      city: options.city,
      provider: this.getProviderType(),
      sticky: options.sticky || false,
      maxConcurrent: options.maxConcurrent || 10,
      timeout: options.timeout || 30000,
      retries: options.retries || 3,
      tags: options.tags || [],
      enabled: options.enabled !== undefined ? options.enabled : true,
      createdAt: new Date(),
      ...options
    };
  }
}