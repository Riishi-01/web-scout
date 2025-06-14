import { EventEmitter } from 'events';
import {
  ProxyConfig,
  ProxyStatus,
  ProxyPoolConfig,
  ProxyRotationStrategy,
  ProxyRequest,
  ProxyResponse
} from './types';

export class ProxyPool extends EventEmitter {
  private proxies: Map<string, ProxyConfig> = new Map();
  private statuses: Map<string, ProxyStatus> = new Map();
  private sessions: Map<string, string> = new Map(); // requestId -> proxyId for sticky sessions
  private roundRobinIndex = 0;
  private config: ProxyPoolConfig;

  constructor(config: ProxyPoolConfig) {
    super();
    this.config = config;
  }

  // Add proxy to the pool
  addProxy(proxy: ProxyConfig): void {
    this.proxies.set(proxy.id, proxy);
    this.initializeProxyStatus(proxy);
    this.emit('proxy:added', { proxyId: proxy.id });
  }

  // Remove proxy from the pool
  removeProxy(proxyId: string): boolean {
    if (this.proxies.has(proxyId)) {
      this.proxies.delete(proxyId);
      this.statuses.delete(proxyId);
      
      // Clean up sessions using this proxy
      for (const [sessionId, sessionProxyId] of this.sessions.entries()) {
        if (sessionProxyId === proxyId) {
          this.sessions.delete(sessionId);
        }
      }
      
      this.emit('proxy:removed', { proxyId });
      return true;
    }
    return false;
  }

  // Get a proxy for the request based on the rotation strategy
  async getProxy(request: ProxyRequest): Promise<ProxyConfig | null> {
    const healthyProxies = this.getHealthyProxies();
    
    if (healthyProxies.length === 0) {
      return null;
    }

    // Check for sticky session
    if (request.requiresStickiness && this.sessions.has(request.id)) {
      const stickyProxyId = this.sessions.get(request.id)!;
      const stickyProxy = this.proxies.get(stickyProxyId);
      
      if (stickyProxy && this.isProxyHealthy(stickyProxyId)) {
        return stickyProxy;
      } else {
        // Remove invalid sticky session
        this.sessions.delete(request.id);
      }
    }

    // Filter by geographic requirements
    let availableProxies = healthyProxies;
    if (request.geoRequirements) {
      availableProxies = this.filterProxiesByGeo(healthyProxies, request.geoRequirements);
      
      if (availableProxies.length === 0) {
        console.warn('No proxies available for geo requirements:', request.geoRequirements);
        availableProxies = healthyProxies; // Fallback to any healthy proxy
      }
    }

    // Filter by specific proxy if requested
    if (request.proxyId) {
      const specificProxy = availableProxies.find(p => p.id === request.proxyId);
      if (specificProxy) {
        availableProxies = [specificProxy];
      }
    }

    if (availableProxies.length === 0) {
      return null;
    }

    // Select proxy based on strategy
    const selectedProxy = this.selectProxyByStrategy(availableProxies);

    // Set up sticky session if required
    if (request.requiresStickiness && selectedProxy) {
      this.sessions.set(request.id, selectedProxy.id);
      
      // Clean up session after timeout
      setTimeout(() => {
        this.sessions.delete(request.id);
      }, this.config.sessionTimeout);
    }

    if (selectedProxy) {
      this.updateProxyUsage(selectedProxy.id);
      this.emit('proxy:selected', {
        requestId: request.id,
        proxyId: selectedProxy.id,
        strategy: this.config.strategy
      });
    }

    return selectedProxy;
  }

  // Record the result of a proxy request
  recordProxyResponse(response: ProxyResponse): void {
    const status = this.statuses.get(response.proxyId);
    if (!status) return;

    status.totalRequests++;
    status.lastChecked = new Date();

    if (response.success) {
      status.successRate = (status.successRate * (status.totalRequests - 1) + 1) / status.totalRequests;
      status.consecutiveFailures = 0;
      status.responseTime = (status.responseTime + response.responseTime) / 2; // Running average
    } else {
      status.failedRequests++;
      status.consecutiveFailures++;
      status.successRate = (status.successRate * (status.totalRequests - 1)) / status.totalRequests;
      status.error = response.error;
    }

    // Check if proxy should be marked as unhealthy
    if (status.consecutiveFailures >= this.config.failureThreshold) {
      status.isHealthy = false;
      this.emit('proxy:unhealthy', { proxyId: response.proxyId, status });
    }

    this.statuses.set(response.proxyId, status);
    this.emit('proxy:response_recorded', { response, status });
  }

  // Mark proxy as healthy (for recovery)
  markProxyHealthy(proxyId: string): void {
    const status = this.statuses.get(proxyId);
    if (status) {
      status.isHealthy = true;
      status.consecutiveFailures = 0;
      status.error = undefined;
      this.statuses.set(proxyId, status);
      this.emit('proxy:recovered', { proxyId, status });
    }
  }

  // Get all proxies in the pool
  getProxies(): ProxyConfig[] {
    return Array.from(this.proxies.values());
  }

  // Get healthy proxies only
  getHealthyProxies(): ProxyConfig[] {
    return this.getProxies().filter(proxy => 
      proxy.enabled && this.isProxyHealthy(proxy.id)
    );
  }

  // Get proxy status
  getProxyStatus(proxyId: string): ProxyStatus | null {
    return this.statuses.get(proxyId) || null;
  }

  // Get all proxy statuses
  getAllStatuses(): ProxyStatus[] {
    return Array.from(this.statuses.values());
  }

  // Update pool configuration
  updateConfig(newConfig: Partial<ProxyPoolConfig>): void {
    this.config = { ...this.config, ...newConfig };
    this.emit('pool:config_updated', { config: this.config });
  }

  // Get pool statistics
  getPoolStats() {
    const proxies = this.getProxies();
    const healthyProxies = this.getHealthyProxies();
    const statuses = this.getAllStatuses();

    const totalRequests = statuses.reduce((sum, status) => sum + status.totalRequests, 0);
    const totalFailures = statuses.reduce((sum, status) => sum + status.failedRequests, 0);
    const avgResponseTime = statuses.length > 0 
      ? statuses.reduce((sum, status) => sum + status.responseTime, 0) / statuses.length 
      : 0;

    return {
      totalProxies: proxies.length,
      healthyProxies: healthyProxies.length,
      unhealthyProxies: proxies.length - healthyProxies.length,
      totalRequests,
      totalFailures,
      successRate: totalRequests > 0 ? ((totalRequests - totalFailures) / totalRequests) * 100 : 0,
      avgResponseTime,
      activeSessions: this.sessions.size,
      strategy: this.config.strategy
    };
  }

  // Clear all sticky sessions
  clearSessions(): void {
    this.sessions.clear();
    this.emit('pool:sessions_cleared');
  }

  // Private helper methods
  private initializeProxyStatus(proxy: ProxyConfig): void {
    const status: ProxyStatus = {
      id: proxy.id,
      isHealthy: true,
      lastChecked: new Date(),
      responseTime: 0,
      successRate: 1.0,
      totalRequests: 0,
      failedRequests: 0,
      consecutiveFailures: 0,
      currentConnections: 0
    };
    
    this.statuses.set(proxy.id, status);
  }

  private isProxyHealthy(proxyId: string): boolean {
    const status = this.statuses.get(proxyId);
    return status ? status.isHealthy : false;
  }

  private filterProxiesByGeo(
    proxies: ProxyConfig[], 
    geoRequirements: { country?: string; city?: string }
  ): ProxyConfig[] {
    return proxies.filter(proxy => {
      if (geoRequirements.country && proxy.country !== geoRequirements.country) {
        return false;
      }
      if (geoRequirements.city && proxy.city !== geoRequirements.city) {
        return false;
      }
      return true;
    });
  }

  private selectProxyByStrategy(proxies: ProxyConfig[]): ProxyConfig {
    switch (this.config.strategy) {
      case 'round_robin':
        return this.selectRoundRobin(proxies);
      
      case 'random':
        return this.selectRandom(proxies);
      
      case 'least_used':
        return this.selectLeastUsed(proxies);
      
      case 'fastest':
        return this.selectFastest(proxies);
      
      default:
        return this.selectRandom(proxies);
    }
  }

  private selectRoundRobin(proxies: ProxyConfig[]): ProxyConfig {
    const proxy = proxies[this.roundRobinIndex % proxies.length];
    this.roundRobinIndex = (this.roundRobinIndex + 1) % proxies.length;
    return proxy;
  }

  private selectRandom(proxies: ProxyConfig[]): ProxyConfig {
    const randomIndex = Math.floor(Math.random() * proxies.length);
    return proxies[randomIndex];
  }

  private selectLeastUsed(proxies: ProxyConfig[]): ProxyConfig {
    let leastUsedProxy = proxies[0];
    let minRequests = this.statuses.get(leastUsedProxy.id)?.totalRequests || 0;

    for (const proxy of proxies) {
      const status = this.statuses.get(proxy.id);
      const requests = status?.totalRequests || 0;
      
      if (requests < minRequests) {
        minRequests = requests;
        leastUsedProxy = proxy;
      }
    }

    return leastUsedProxy;
  }

  private selectFastest(proxies: ProxyConfig[]): ProxyConfig {
    let fastestProxy = proxies[0];
    let minResponseTime = this.statuses.get(fastestProxy.id)?.responseTime || Infinity;

    for (const proxy of proxies) {
      const status = this.statuses.get(proxy.id);
      const responseTime = status?.responseTime || Infinity;
      
      if (responseTime < minResponseTime) {
        minResponseTime = responseTime;
        fastestProxy = proxy;
      }
    }

    return fastestProxy;
  }

  private updateProxyUsage(proxyId: string): void {
    const status = this.statuses.get(proxyId);
    if (status) {
      status.currentConnections++;
      this.statuses.set(proxyId, status);
    }
  }
}