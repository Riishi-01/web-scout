import { EventEmitter } from 'events';
import {
  ProxyConfig,
  ProxyStatus,
  ProxyHealthCheck,
  ProxyTestResult
} from './types';
import { ProxyPool } from './ProxyPool';

export class ProxyHealthMonitor extends EventEmitter {
  private pool: ProxyPool;
  private healthCheckInterval: number;
  private healthCheckUrls: string[];
  private isMonitoring = false;
  private monitoringInterval?: NodeJS.Timeout;
  private currentChecks = new Map<string, Promise<ProxyTestResult>>();

  constructor(pool: ProxyPool, options: {
    interval?: number;
    healthCheckUrls?: string[];
  } = {}) {
    super();
    this.pool = pool;
    this.healthCheckInterval = options.interval || 60000; // 1 minute default
    this.healthCheckUrls = options.healthCheckUrls || [
      'https://httpbin.org/ip',
      'https://ipinfo.io/json',
      'http://ip-api.com/json'
    ];
  }

  // Start monitoring proxy health
  start(): void {
    if (this.isMonitoring) {
      return;
    }

    this.isMonitoring = true;
    this.monitoringInterval = setInterval(() => {
      this.performHealthChecks();
    }, this.healthCheckInterval);

    this.emit('monitoring:started');
    console.log(`Proxy health monitoring started with ${this.healthCheckInterval}ms interval`);
  }

  // Stop monitoring
  stop(): void {
    if (!this.isMonitoring) {
      return;
    }

    this.isMonitoring = false;
    
    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
      this.monitoringInterval = undefined;
    }

    // Cancel any ongoing health checks
    this.currentChecks.clear();

    this.emit('monitoring:stopped');
    console.log('Proxy health monitoring stopped');
  }

  // Perform health checks on all proxies
  async performHealthChecks(): Promise<void> {
    const proxies = this.pool.getProxies();
    const healthyCount = this.pool.getHealthyProxies().length;

    this.emit('monitoring:check_started', {
      totalProxies: proxies.length,
      healthyProxies: healthyCount
    });

    const checkPromises = proxies.map(proxy => this.checkProxyHealth(proxy));
    const results = await Promise.allSettled(checkPromises);

    let successCount = 0;
    let failureCount = 0;
    const healthChanges: Array<{ proxyId: string; previousHealth: boolean; currentHealth: boolean }> = [];

    results.forEach((result, index) => {
      const proxy = proxies[index];
      const previousStatus = this.pool.getProxyStatus(proxy.id);
      const previousHealth = previousStatus?.isHealthy || true;

      if (result.status === 'fulfilled') {
        const testResult = result.value;
        const currentHealth = testResult.success;

        if (testResult.success) {
          successCount++;
          this.pool.markProxyHealthy(proxy.id);
        } else {
          failureCount++;
          this.handleProxyFailure(proxy.id, testResult.error || 'Health check failed');
        }

        if (previousHealth !== currentHealth) {
          healthChanges.push({
            proxyId: proxy.id,
            previousHealth,
            currentHealth
          });
        }

        this.emit('monitoring:proxy_checked', {
          proxyId: proxy.id,
          success: testResult.success,
          responseTime: testResult.responseTime,
          error: testResult.error
        });
      } else {
        failureCount++;
        this.handleProxyFailure(proxy.id, result.reason?.message || 'Health check failed');
        
        if (previousHealth) {
          healthChanges.push({
            proxyId: proxy.id,
            previousHealth: true,
            currentHealth: false
          });
        }
      }
    });

    // Emit health changes
    healthChanges.forEach(change => {
      this.emit('monitoring:health_changed', change);
    });

    this.emit('monitoring:check_completed', {
      totalProxies: proxies.length,
      successCount,
      failureCount,
      healthChanges: healthChanges.length
    });
  }

  // Check health of a specific proxy
  async checkProxyHealth(proxy: ProxyConfig): Promise<ProxyTestResult> {
    // Prevent duplicate health checks for the same proxy
    if (this.currentChecks.has(proxy.id)) {
      return await this.currentChecks.get(proxy.id)!;
    }

    const checkPromise = this.performSingleHealthCheck(proxy);
    this.currentChecks.set(proxy.id, checkPromise);

    try {
      const result = await checkPromise;
      return result;
    } finally {
      this.currentChecks.delete(proxy.id);
    }
  }

  // Perform health check with custom configuration
  async checkProxyWithConfig(proxy: ProxyConfig, healthCheck: ProxyHealthCheck): Promise<ProxyTestResult> {
    const startTime = Date.now();

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), healthCheck.timeout);

      const response = await fetch(healthCheck.url, {
        method: 'GET',
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
          ...healthCheck.headers
        },
        signal: controller.signal
      });

      clearTimeout(timeoutId);
      const responseTime = Date.now() - startTime;

      // Check expected status code
      if (healthCheck.expectedStatus && response.status !== healthCheck.expectedStatus) {
        throw new Error(`Expected status ${healthCheck.expectedStatus}, got ${response.status}`);
      }

      // Custom response validation
      if (healthCheck.validateResponse) {
        const responseData = await response.json();
        if (!healthCheck.validateResponse(responseData)) {
          throw new Error('Custom validation failed');
        }
      }

      return {
        proxyId: proxy.id,
        success: true,
        responseTime,
        protocols: [proxy.protocol],
        features: {
          javascript: false, // Health checks don't test JS
          cookies: false,
          referer: false,
          userAgent: false
        }
      };
    } catch (error) {
      const responseTime = Date.now() - startTime;
      
      return {
        proxyId: proxy.id,
        success: false,
        responseTime,
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

  // Get monitoring statistics
  getMonitoringStats() {
    const proxies = this.pool.getProxies();
    const statuses = this.pool.getAllStatuses();
    const healthyProxies = this.pool.getHealthyProxies();

    const avgResponseTime = statuses.length > 0
      ? statuses.reduce((sum, status) => sum + status.responseTime, 0) / statuses.length
      : 0;

    const lastCheckTime = statuses.length > 0
      ? Math.max(...statuses.map(status => status.lastChecked.getTime()))
      : 0;

    return {
      isMonitoring: this.isMonitoring,
      interval: this.healthCheckInterval,
      totalProxies: proxies.length,
      healthyProxies: healthyProxies.length,
      unhealthyProxies: proxies.length - healthyProxies.length,
      avgResponseTime,
      lastCheckTime: lastCheckTime > 0 ? new Date(lastCheckTime) : null,
      activeChecks: this.currentChecks.size
    };
  }

  // Update monitoring configuration
  updateConfig(config: { interval?: number; healthCheckUrls?: string[] }): void {
    if (config.interval && config.interval !== this.healthCheckInterval) {
      this.healthCheckInterval = config.interval;
      
      // Restart monitoring with new interval if currently running
      if (this.isMonitoring) {
        this.stop();
        this.start();
      }
    }

    if (config.healthCheckUrls) {
      this.healthCheckUrls = config.healthCheckUrls;
    }

    this.emit('monitoring:config_updated', {
      interval: this.healthCheckInterval,
      healthCheckUrls: this.healthCheckUrls
    });
  }

  // Private helper methods
  private async performSingleHealthCheck(proxy: ProxyConfig): Promise<ProxyTestResult> {
    // Try multiple health check URLs for redundancy
    for (let i = 0; i < this.healthCheckUrls.length; i++) {
      const url = this.healthCheckUrls[i];
      
      try {
        const result = await this.checkProxyWithConfig(proxy, {
          url,
          timeout: 10000, // 10 second timeout
          expectedStatus: 200
        });

        if (result.success) {
          return result;
        }
      } catch (error) {
        // Continue to next URL if this one fails
        if (i === this.healthCheckUrls.length - 1) {
          // This was the last URL, return failure
          return {
            proxyId: proxy.id,
            success: false,
            error: error instanceof Error ? error.message : 'All health check URLs failed',
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
    }

    // Fallback error (shouldn't reach here)
    return {
      proxyId: proxy.id,
      success: false,
      error: 'Health check failed for unknown reason',
      protocols: [proxy.protocol],
      features: {
        javascript: false,
        cookies: false,
        referer: false,
        userAgent: false
      }
    };
  }

  private handleProxyFailure(proxyId: string, error: string): void {
    const status = this.pool.getProxyStatus(proxyId);
    
    if (status) {
      const updatedStatus: ProxyStatus = {
        ...status,
        isHealthy: false,
        error,
        lastChecked: new Date(),
        consecutiveFailures: status.consecutiveFailures + 1
      };

      // Update status in the pool (this should be done through proper interface)
      this.emit('monitoring:proxy_failed', {
        proxyId,
        error,
        consecutiveFailures: updatedStatus.consecutiveFailures
      });
    }
  }
}