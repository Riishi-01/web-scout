import React, { useState, useEffect } from 'react';
import { ProxyConfig, ProxyStats, ProxyTestResult, CustomProxyInput } from '../../../shared/types';

export const ProxyDashboard: React.FC = () => {
  const [proxies, setProxies] = useState<ProxyConfig[]>([]);
  const [stats, setStats] = useState<ProxyStats | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'proxies' | 'stats' | 'add'>('proxies');
  const [testResults, setTestResults] = useState<Map<string, ProxyTestResult>>(new Map());

  // Form state for adding proxies
  const [newProxy, setNewProxy] = useState<CustomProxyInput>({
    host: '',
    port: 8080,
    protocol: 'http',
    username: '',
    password: '',
    country: '',
    city: '',
    name: ''
  });

  useEffect(() => {
    loadProxies();
    loadStats();
    
    // Refresh data every 30 seconds
    const interval = setInterval(() => {
      loadStats();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const loadProxies = async () => {
    try {
      if (typeof window !== 'undefined' && window.electronAPI?.proxy) {
        const proxyList = await window.electronAPI.proxy.getProxies();
        setProxies(proxyList);
      } else {
        // Mock data for development
        console.log('Loading mock proxy data');
        setProxies([
          {
            id: 'mock-1',
            name: 'Mock Proxy 1',
            host: '127.0.0.1',
            port: 8080,
            protocol: 'http',
            authType: 'none',
            country: 'US',
            city: 'New York',
            provider: 'custom',
            enabled: true,
            createdAt: new Date(),
            tags: ['development']
          }
        ]);
      }
    } catch (error) {
      console.error('Failed to load proxies:', error);
    }
  };

  const loadStats = async () => {
    try {
      if (typeof window !== 'undefined' && window.electronAPI?.proxy) {
        const proxyStats = await window.electronAPI.proxy.getProxyStats();
        setStats(proxyStats);
      } else {
        // Mock stats for development
        setStats({
          pool: {
            totalProxies: 1,
            healthyProxies: 1,
            unhealthyProxies: 0,
            totalRequests: 0,
            totalFailures: 0,
            successRate: 100,
            avgResponseTime: 250,
            activeSessions: 0,
            strategy: 'round_robin'
          },
          monitoring: {
            isMonitoring: true,
            interval: 60000,
            totalProxies: 1,
            healthyProxies: 1,
            unhealthyProxies: 0,
            avgResponseTime: 250,
            lastCheckTime: new Date(),
            activeChecks: 0
          },
          providers: [
            {
              type: 'custom',
              totalProxies: 1,
              healthyProxies: 1,
              avgResponseTime: 250,
              successRate: 100,
              totalRequests: 0,
              bandwidthUsed: 0
            }
          ],
          totalRequests: 0
        });
      }
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  const handleAddProxy = async () => {
    if (!newProxy.host || !newProxy.port) {
      alert('Please fill in host and port');
      return;
    }

    setIsLoading(true);
    try {
      if (typeof window !== 'undefined' && window.electronAPI?.proxy) {
        await window.electronAPI.proxy.addCustomProxy(newProxy);
        setNewProxy({
          host: '',
          port: 8080,
          protocol: 'http',
          username: '',
          password: '',
          country: '',
          city: '',
          name: ''
        });
        await loadProxies();
        setActiveTab('proxies');
      } else {
        console.log('Would add proxy:', newProxy);
        alert('Proxy added (mock mode)');
      }
    } catch (error) {
      console.error('Failed to add proxy:', error);
      alert('Failed to add proxy: ' + (error instanceof Error ? error.message : 'Unknown error'));
    } finally {
      setIsLoading(false);
    }
  };

  const handleTestProxy = async (proxyId: string) => {
    setIsLoading(true);
    try {
      if (typeof window !== 'undefined' && window.electronAPI?.proxy) {
        const result = await window.electronAPI.proxy.testProxy(proxyId);
        setTestResults(prev => new Map(prev).set(proxyId, result));
      } else {
        // Mock test result
        const mockResult: ProxyTestResult = {
          proxyId,
          success: true,
          responseTime: 250,
          ipAddress: '127.0.0.1',
          location: { ip: '127.0.0.1', country: 'US', city: 'New York' },
          anonymityLevel: 'elite',
          protocols: ['http'],
          features: { javascript: true, cookies: true, referer: true, userAgent: true }
        };
        setTestResults(prev => new Map(prev).set(proxyId, mockResult));
      }
    } catch (error) {
      console.error('Failed to test proxy:', error);
      const errorResult: ProxyTestResult = {
        proxyId,
        success: false,
        error: error instanceof Error ? error.message : 'Test failed',
        protocols: ['http'],
        features: { javascript: false, cookies: false, referer: false, userAgent: false }
      };
      setTestResults(prev => new Map(prev).set(proxyId, errorResult));
    } finally {
      setIsLoading(false);
    }
  };

  const handleRemoveProxy = async (proxyId: string) => {
    if (!window.confirm('Are you sure you want to remove this proxy?')) {
      return;
    }

    try {
      if (typeof window !== 'undefined' && window.electronAPI?.proxy) {
        await window.electronAPI.proxy.removeProxy(proxyId);
        await loadProxies();
      } else {
        console.log('Would remove proxy:', proxyId);
        alert('Proxy removed (mock mode)');
      }
    } catch (error) {
      console.error('Failed to remove proxy:', error);
      alert('Failed to remove proxy');
    }
  };

  const handleForceHealthCheck = async () => {
    setIsLoading(true);
    try {
      if (typeof window !== 'undefined' && window.electronAPI?.proxy) {
        await window.electronAPI.proxy.forceHealthCheck();
        await loadStats();
      } else {
        console.log('Would force health check');
        alert('Health check completed (mock mode)');
      }
    } catch (error) {
      console.error('Failed to force health check:', error);
      alert('Failed to run health check');
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusColor = (proxy: ProxyConfig) => {
    const testResult = testResults.get(proxy.id);
    if (testResult !== undefined) {
      return testResult.success ? '#10b981' : '#ef4444';
    }
    return proxy.enabled ? '#f59e0b' : '#6b7280';
  };

  const getStatusText = (proxy: ProxyConfig) => {
    const testResult = testResults.get(proxy.id);
    if (testResult !== undefined) {
      return testResult.success ? '✅ Healthy' : '❌ Failed';
    }
    return proxy.enabled ? '⏳ Unknown' : '⚪ Disabled';
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'system-ui, -apple-system, sans-serif' }}>
      <div style={{ marginBottom: '20px' }}>
        <h2 style={{ margin: '0 0 10px 0', color: '#1f2937' }}>🔗 Proxy Management</h2>
        <p style={{ color: '#6b7280', marginBottom: '20px' }}>
          Manage proxy servers and monitor their health status
        </p>
      </div>

      {/* Tab Navigation */}
      <div style={{ 
        display: 'flex', 
        gap: '4px', 
        marginBottom: '20px',
        borderBottom: '1px solid #e5e7eb'
      }}>
        {[
          { key: 'proxies', label: '🌐 Proxies' },
          { key: 'stats', label: '📊 Statistics' },
          { key: 'add', label: '➕ Add Proxy' }
        ].map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key as any)}
            style={{
              padding: '10px 16px',
              border: 'none',
              backgroundColor: activeTab === tab.key ? '#3b82f6' : 'transparent',
              color: activeTab === tab.key ? 'white' : '#6b7280',
              borderRadius: '6px 6px 0 0',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: 'medium'
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Proxies Tab */}
      {activeTab === 'proxies' && (
        <div>
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            marginBottom: '20px'
          }}>
            <h3 style={{ margin: 0, color: '#1f2937' }}>
              Proxy List ({proxies.length} total)
            </h3>
            <button
              onClick={handleForceHealthCheck}
              disabled={isLoading}
              style={{
                padding: '8px 16px',
                backgroundColor: '#10b981',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: isLoading ? 'not-allowed' : 'pointer',
                fontSize: '14px'
              }}
            >
              {isLoading ? '🔄 Checking...' : '🔍 Health Check'}
            </button>
          </div>

          {proxies.length === 0 ? (
            <div style={{
              padding: '40px',
              textAlign: 'center',
              backgroundColor: '#f9fafb',
              borderRadius: '8px',
              border: '1px dashed #d1d5db'
            }}>
              <p style={{ color: '#6b7280', marginBottom: '10px' }}>No proxies configured</p>
              <button
                onClick={() => setActiveTab('add')}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#3b82f6',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '14px'
                }}
              >
                Add Your First Proxy
              </button>
            </div>
          ) : (
            <div style={{ display: 'grid', gap: '12px' }}>
              {proxies.map(proxy => (
                <div key={proxy.id} style={{
                  padding: '16px',
                  backgroundColor: 'white',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                        <h4 style={{ margin: 0, color: '#1f2937' }}>{proxy.name}</h4>
                        <span style={{
                          padding: '2px 8px',
                          backgroundColor: getStatusColor(proxy),
                          color: 'white',
                          borderRadius: '12px',
                          fontSize: '12px',
                          fontWeight: 'medium'
                        }}>
                          {getStatusText(proxy)}
                        </span>
                      </div>
                      
                      <div style={{ 
                        display: 'grid', 
                        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                        gap: '8px',
                        fontSize: '14px',
                        color: '#6b7280'
                      }}>
                        <div><strong>Address:</strong> {proxy.host}:{proxy.port}</div>
                        <div><strong>Protocol:</strong> {proxy.protocol.toUpperCase()}</div>
                        <div><strong>Provider:</strong> {proxy.provider || 'Custom'}</div>
                        {proxy.country && <div><strong>Location:</strong> {proxy.city ? `${proxy.city}, ` : ''}{proxy.country}</div>}
                      </div>

                      {testResults.has(proxy.id) && (
                        <div style={{ marginTop: '8px', fontSize: '12px' }}>
                          <div style={{ 
                            padding: '8px',
                            backgroundColor: '#f3f4f6',
                            borderRadius: '4px'
                          }}>
                            {testResults.get(proxy.id)?.success ? (
                              <>
                                <div><strong>Response Time:</strong> {testResults.get(proxy.id)?.responseTime}ms</div>
                                <div><strong>IP:</strong> {testResults.get(proxy.id)?.ipAddress}</div>
                                <div><strong>Anonymity:</strong> {testResults.get(proxy.id)?.anonymityLevel}</div>
                              </>
                            ) : (
                              <div style={{ color: '#ef4444' }}>
                                <strong>Error:</strong> {testResults.get(proxy.id)?.error}
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>

                    <div style={{ display: 'flex', gap: '8px' }}>
                      <button
                        onClick={() => handleTestProxy(proxy.id)}
                        disabled={isLoading}
                        style={{
                          padding: '6px 12px',
                          backgroundColor: '#8b5cf6',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: isLoading ? 'not-allowed' : 'pointer',
                          fontSize: '12px'
                        }}
                      >
                        Test
                      </button>
                      <button
                        onClick={() => handleRemoveProxy(proxy.id)}
                        style={{
                          padding: '6px 12px',
                          backgroundColor: '#ef4444',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: 'pointer',
                          fontSize: '12px'
                        }}
                      >
                        Remove
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Statistics Tab */}
      {activeTab === 'stats' && (
        <div>
          <h3 style={{ margin: '0 0 20px 0', color: '#1f2937' }}>Proxy Statistics</h3>
          
          {stats ? (
            <div style={{ display: 'grid', gap: '20px' }}>
              {/* Pool Stats */}
              <div style={{
                padding: '20px',
                backgroundColor: 'white',
                border: '1px solid #e5e7eb',
                borderRadius: '8px'
              }}>
                <h4 style={{ margin: '0 0 15px 0', color: '#1f2937' }}>Pool Status</h4>
                <div style={{ 
                  display: 'grid', 
                  gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                  gap: '15px'
                }}>
                  <div>
                    <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#10b981' }}>
                      {stats.pool.healthyProxies}
                    </div>
                    <div style={{ fontSize: '14px', color: '#6b7280' }}>Healthy Proxies</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#ef4444' }}>
                      {stats.pool.unhealthyProxies}
                    </div>
                    <div style={{ fontSize: '14px', color: '#6b7280' }}>Unhealthy Proxies</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#3b82f6' }}>
                      {Math.round(stats.pool.successRate)}%
                    </div>
                    <div style={{ fontSize: '14px', color: '#6b7280' }}>Success Rate</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#f59e0b' }}>
                      {Math.round(stats.pool.avgResponseTime)}ms
                    </div>
                    <div style={{ fontSize: '14px', color: '#6b7280' }}>Avg Response Time</div>
                  </div>
                </div>
              </div>

              {/* Monitoring Stats */}
              <div style={{
                padding: '20px',
                backgroundColor: 'white',
                border: '1px solid #e5e7eb',
                borderRadius: '8px'
              }}>
                <h4 style={{ margin: '0 0 15px 0', color: '#1f2937' }}>Health Monitoring</h4>
                <div style={{ fontSize: '14px', color: '#6b7280' }}>
                  <p><strong>Status:</strong> {stats.monitoring.isMonitoring ? '✅ Active' : '❌ Inactive'}</p>
                  <p><strong>Check Interval:</strong> {Math.round(stats.monitoring.interval / 1000)}s</p>
                  <p><strong>Last Check:</strong> {stats.monitoring.lastCheckTime?.toLocaleString() || 'Never'}</p>
                  <p><strong>Active Checks:</strong> {stats.monitoring.activeChecks}</p>
                </div>
              </div>

              {/* Provider Stats */}
              {stats.providers.length > 0 && (
                <div style={{
                  padding: '20px',
                  backgroundColor: 'white',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px'
                }}>
                  <h4 style={{ margin: '0 0 15px 0', color: '#1f2937' }}>Provider Statistics</h4>
                  {stats.providers.map(provider => (
                    <div key={provider.type} style={{ marginBottom: '15px', paddingBottom: '15px', borderBottom: '1px solid #f3f4f6' }}>
                      <h5 style={{ margin: '0 0 8px 0', textTransform: 'capitalize' }}>{provider.type}</h5>
                      <div style={{ fontSize: '14px', color: '#6b7280' }}>
                        <span>Proxies: {provider.totalProxies} | </span>
                        <span>Healthy: {provider.healthyProxies} | </span>
                        <span>Success Rate: {Math.round(provider.successRate)}% | </span>
                        <span>Avg Response: {Math.round(provider.avgResponseTime)}ms</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div style={{ textAlign: 'center', color: '#6b7280' }}>
              Loading statistics...
            </div>
          )}
        </div>
      )}

      {/* Add Proxy Tab */}
      {activeTab === 'add' && (
        <div>
          <h3 style={{ margin: '0 0 20px 0', color: '#1f2937' }}>Add Custom Proxy</h3>
          
          <div style={{
            maxWidth: '600px',
            padding: '20px',
            backgroundColor: 'white',
            border: '1px solid #e5e7eb',
            borderRadius: '8px'
          }}>
            <div style={{ display: 'grid', gap: '15px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '10px' }}>
                <div>
                  <label style={{ display: 'block', marginBottom: '5px', fontSize: '14px', fontWeight: 'medium' }}>
                    Host *
                  </label>
                  <input
                    type="text"
                    value={newProxy.host}
                    onChange={(e) => setNewProxy(prev => ({ ...prev, host: e.target.value }))}
                    placeholder="proxy.example.com"
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      border: '1px solid #d1d5db',
                      borderRadius: '6px',
                      fontSize: '14px'
                    }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', marginBottom: '5px', fontSize: '14px', fontWeight: 'medium' }}>
                    Port *
                  </label>
                  <input
                    type="number"
                    value={newProxy.port}
                    onChange={(e) => setNewProxy(prev => ({ ...prev, port: parseInt(e.target.value) || 8080 }))}
                    placeholder="8080"
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      border: '1px solid #d1d5db',
                      borderRadius: '6px',
                      fontSize: '14px'
                    }}
                  />
                </div>
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontSize: '14px', fontWeight: 'medium' }}>
                  Protocol
                </label>
                <select
                  value={newProxy.protocol}
                  onChange={(e) => setNewProxy(prev => ({ ...prev, protocol: e.target.value as any }))}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    border: '1px solid #d1d5db',
                    borderRadius: '6px',
                    fontSize: '14px'
                  }}
                >
                  <option value="http">HTTP</option>
                  <option value="https">HTTPS</option>
                  <option value="socks4">SOCKS4</option>
                  <option value="socks5">SOCKS5</option>
                </select>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div>
                  <label style={{ display: 'block', marginBottom: '5px', fontSize: '14px', fontWeight: 'medium' }}>
                    Username (optional)
                  </label>
                  <input
                    type="text"
                    value={newProxy.username}
                    onChange={(e) => setNewProxy(prev => ({ ...prev, username: e.target.value }))}
                    placeholder="username"
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      border: '1px solid #d1d5db',
                      borderRadius: '6px',
                      fontSize: '14px'
                    }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', marginBottom: '5px', fontSize: '14px', fontWeight: 'medium' }}>
                    Password (optional)
                  </label>
                  <input
                    type="password"
                    value={newProxy.password}
                    onChange={(e) => setNewProxy(prev => ({ ...prev, password: e.target.value }))}
                    placeholder="password"
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      border: '1px solid #d1d5db',
                      borderRadius: '6px',
                      fontSize: '14px'
                    }}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '10px' }}>
                <div>
                  <label style={{ display: 'block', marginBottom: '5px', fontSize: '14px', fontWeight: 'medium' }}>
                    Name (optional)
                  </label>
                  <input
                    type="text"
                    value={newProxy.name}
                    onChange={(e) => setNewProxy(prev => ({ ...prev, name: e.target.value }))}
                    placeholder="My Proxy"
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      border: '1px solid #d1d5db',
                      borderRadius: '6px',
                      fontSize: '14px'
                    }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', marginBottom: '5px', fontSize: '14px', fontWeight: 'medium' }}>
                    Country (optional)
                  </label>
                  <input
                    type="text"
                    value={newProxy.country}
                    onChange={(e) => setNewProxy(prev => ({ ...prev, country: e.target.value }))}
                    placeholder="US"
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      border: '1px solid #d1d5db',
                      borderRadius: '6px',
                      fontSize: '14px'
                    }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', marginBottom: '5px', fontSize: '14px', fontWeight: 'medium' }}>
                    City (optional)
                  </label>
                  <input
                    type="text"
                    value={newProxy.city}
                    onChange={(e) => setNewProxy(prev => ({ ...prev, city: e.target.value }))}
                    placeholder="New York"
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      border: '1px solid #d1d5db',
                      borderRadius: '6px',
                      fontSize: '14px'
                    }}
                  />
                </div>
              </div>

              <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
                <button
                  onClick={handleAddProxy}
                  disabled={isLoading || !newProxy.host || !newProxy.port}
                  style={{
                    padding: '10px 20px',
                    backgroundColor: isLoading || !newProxy.host || !newProxy.port ? '#9ca3af' : '#10b981',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: isLoading || !newProxy.host || !newProxy.port ? 'not-allowed' : 'pointer',
                    fontSize: '14px',
                    fontWeight: 'medium'
                  }}
                >
                  {isLoading ? '➕ Adding...' : '➕ Add Proxy'}
                </button>
                <button
                  onClick={() => setActiveTab('proxies')}
                  style={{
                    padding: '10px 20px',
                    backgroundColor: '#f3f4f6',
                    color: '#374151',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontSize: '14px',
                    fontWeight: 'medium'
                  }}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};