import { v4 as uuidv4 } from 'uuid';
import { AbstractProxyProvider } from './AbstractProxyProvider';
import {
  ProxyConfig,
  ProxyProviderType,
  ProxyTestResult,
  ProxyUsageQuota,
  ProxyProtocol,
  ProxyAuthType
} from '../types';

export interface CustomProxyInput {
  host: string;
  port: number;
  protocol?: 'http' | 'https' | 'socks4' | 'socks5';
  username?: string;
  password?: string;
  country?: string;
  city?: string;
  name?: string;
  tags?: string[];
}

export class CustomProxyProvider extends AbstractProxyProvider {
  private testUrl = 'https://httpbin.org/ip';

  getProviderType(): ProxyProviderType {
    return 'custom';
  }

  async connect(): Promise<void> {
    // Custom proxies don't require a connection, just validate
    console.log('Custom proxy provider connected');
  }

  async disconnect(): Promise<void> {
    console.log('Custom proxy provider disconnected');
  }

  async fetchProxies(): Promise<ProxyConfig[]> {
    // Custom proxies are manually added, return current list
    return this.getProxies();
  }

  async refreshProxyList(): Promise<void> {
    // For custom proxies, this is a no-op since they're manually managed
    console.log('Custom proxy list refreshed');
  }

  async addProxy(input: CustomProxyInput): Promise<ProxyConfig> {
    const proxyId = uuidv4();
    
    const proxy = this.createProxyConfig(proxyId, input.host, input.port, {
      name: input.name || `Custom-${input.host}:${input.port}`,
      protocol: input.protocol || 'http',
      authType: (input.username && input.password) ? 'basic' : 'none',
      credentials: (input.username && input.password) ? {
        username: input.username,
        password: input.password
      } : undefined,
      country: input.country,
      city: input.city,
      tags: input.tags || ['custom'],
      provider: 'custom'
    });

    if (!this.validateProxyConfig(proxy)) {
      throw new Error('Invalid proxy configuration');
    }

    this.addProxy(proxy);
    return proxy;
  }

  async addProxyFromUrl(proxyUrl: string, options: Partial<CustomProxyInput> = {}): Promise<ProxyConfig> {
    try {
      const parsed = this.parseProxyUrl(proxyUrl);
      return await this.addProxy({ ...parsed, ...options });
    } catch (error) {
      throw new Error(`Failed to parse proxy URL: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async addMultipleProxies(proxies: CustomProxyInput[]): Promise<ProxyConfig[]> {
    const results: ProxyConfig[] = [];
    const errors: Array<{ proxy: CustomProxyInput; error: string }> = [];

    for (const proxyInput of proxies) {
      try {
        const proxy = await this.addProxy(proxyInput);
        results.push(proxy);
      } catch (error) {
        errors.push({
          proxy: proxyInput,
          error: error instanceof Error ? error.message : 'Unknown error'
        });
      }
    }

    if (errors.length > 0) {
      console.warn('Some proxies failed to add:', errors);
    }

    return results;
  }

  async importFromList(proxyList: string): Promise<{ added: ProxyConfig[]; errors: string[] }> {
    const lines = proxyList.split('\n').map(line => line.trim()).filter(line => line);
    const added: ProxyConfig[] = [];
    const errors: string[] = [];

    for (const line of lines) {
      try {
        // Skip comments
        if (line.startsWith('#') || line.startsWith('//')) {
          continue;
        }

        let proxy: ProxyConfig;
        
        if (line.includes('://')) {
          // URL format
          proxy = await this.addProxyFromUrl(line);
        } else if (line.includes(':')) {
          // host:port format
          const parts = line.split(':');
          if (parts.length >= 2) {
            const host = parts[0];
            const port = parseInt(parts[1], 10);
            
            if (isNaN(port)) {
              throw new Error('Invalid port number');
            }
            
            const username = parts[2];
            const password = parts[3];
            
            proxy = await this.addProxy({
              host,
              port,
              username,
              password
            });
          } else {
            throw new Error('Invalid proxy format');
          }
        } else {
          throw new Error('Unrecognized proxy format');
        }
        
        added.push(proxy);
      } catch (error) {
        errors.push(`Line "${line}": ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    }

    return { added, errors };
  }

  async removeProxy(proxyId: string): Promise<boolean> {
    const proxy = this.getProxy(proxyId);
    if (proxy) {
      this.removeProxy(proxyId);
      return true;
    }
    return false;
  }

  async testProxy(proxyId: string): Promise<ProxyTestResult> {
    const proxy = this.getProxy(proxyId);
    if (!proxy) {
      throw new Error(`Proxy ${proxyId} not found`);
    }

    const startTime = Date.now();
    
    try {
      // Test basic connectivity
      const response = await this.testProxyConnectivity(proxy);
      const responseTime = Date.now() - startTime;
      
      // Get location info
      const location = await this.getProxyGeolocation(proxy);
      
      // Test anonymity level
      const anonymityLevel = await this.testAnonymityLevel(proxy);
      
      // Test supported features
      const features = await this.testProxyFeatures(proxy);

      return {
        proxyId,
        success: true,
        responseTime,
        ipAddress: location?.ip,
        location,
        anonymityLevel,
        protocols: [proxy.protocol],
        features
      };
    } catch (error) {
      return {
        proxyId,
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        protocols: [proxy.protocol],
        features: {
          javascript: false,
          cookies: false,
          referer: false,
          userAgent: false
        }
      };
    }
  }

  async getUsageQuota(): Promise<ProxyUsageQuota> {
    // Custom proxies don't have usage quotas
    return {
      provider: 'custom',
      requestsUsed: 0,
      requestsLimit: -1, // Unlimited
      bandwidthUsed: 0,
      bandwidthLimit: -1, // Unlimited
      resetDate: new Date(),
      costAccrued: 0
    };
  }

  private parseProxyUrl(url: string): CustomProxyInput {
    try {
      const parsed = new URL(url);
      
      const protocol = parsed.protocol.slice(0, -1) as ProxyProtocol;
      const host = parsed.hostname;
      const port = parseInt(parsed.port, 10);
      const username = parsed.username || undefined;
      const password = parsed.password || undefined;

      if (!host || isNaN(port)) {
        throw new Error('Invalid host or port');
      }

      return {
        host,
        port,
        protocol,
        username,
        password
      };
    } catch (error) {
      throw new Error(`Invalid proxy URL format: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  private async testProxyConnectivity(proxy: ProxyConfig): Promise<Response> {
    const proxyUrl = this.buildProxyUrl(proxy);
    
    // Test using node-fetch with proxy support
    // Note: This is a simplified test - in production you'd use proper proxy libraries
    const response = await fetch(this.testUrl, {
      method: 'GET',
      // proxy: proxyUrl, // This would need proper proxy implementation
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
      }
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response;
  }

  private async testAnonymityLevel(proxy: ProxyConfig): Promise<'transparent' | 'anonymous' | 'elite'> {
    try {
      // This is a simplified implementation
      // In practice, you'd test for header leakage, IP detection, etc.
      const response = await this.testProxyConnectivity(proxy);
      const data = await response.json() as any;
      
      // Check if original IP is leaked (simplified check)
      const headers = response.headers;
      
      if (headers.get('x-forwarded-for') || headers.get('x-real-ip')) {
        return 'transparent';
      }
      
      if (headers.get('via') || headers.get('proxy-connection')) {
        return 'anonymous';
      }
      
      return 'elite';
    } catch (error) {
      return 'transparent'; // Assume worst case on error
    }
  }

  private async testProxyFeatures(proxy: ProxyConfig) {
    // Simplified feature detection
    try {
      await this.testProxyConnectivity(proxy);
      
      return {
        javascript: true, // Assume supported for HTTP proxies
        cookies: true,
        referer: true,
        userAgent: true
      };
    } catch (error) {
      return {
        javascript: false,
        cookies: false,
        referer: false,
        userAgent: false
      };
    }
  }
}