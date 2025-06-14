import React, { useState } from 'react';
import { LLMTestPanel } from '../ai/LLMTestPanel';
import { ProxyDashboard } from '../proxy/ProxyDashboard';
import { ScrapingInterface } from '../scraping/ScrapingInterface';

export const AppLayout: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'llm' | 'proxy' | 'scraping' | 'settings'>('scraping');

  return (
    <div style={{
      display: 'flex',
      height: '100vh',
      backgroundColor: 'var(--bg-primary)',
      fontFamily: 'Inter, sans-serif'
    }}>
      {/* Sidebar */}
      <div style={{
        width: '16rem',
        backgroundColor: 'var(--bg-secondary)',
        borderRight: '1px solid var(--border-primary)',
        display: 'flex',
        flexDirection: 'column'
      }}>
        <div style={{
          padding: '1.5rem',
          borderBottom: '1px solid var(--border-primary)'
        }}>
          <h2 style={{
            fontSize: '1.125rem',
            fontWeight: '600',
            color: 'var(--text-primary)'
          }}>
            🕷️ AI Web Scraper
          </h2>
        </div>
        <nav style={{ padding: '1rem' }}>
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '0.5rem'
          }}>
            {[
              { key: 'dashboard', label: '📊 Dashboard', emoji: '📊' },
              { key: 'llm', label: '🤖 LLM Test', emoji: '🤖' },
              { key: 'proxy', label: '🔗 Proxies', emoji: '🔗' },
              { key: 'scraping', label: '🕷️ Scraping', emoji: '🕷️' },
              { key: 'settings', label: '⚙️ Settings', emoji: '⚙️' }
            ].map(item => (
              <button
                key={item.key}
                onClick={() => setActiveTab(item.key as any)}
                style={{
                  padding: '0.75rem 1rem',
                  backgroundColor: activeTab === item.key ? 'var(--accent-primary)' : 'transparent',
                  color: activeTab === item.key ? 'var(--accent-text)' : 'var(--text-secondary)',
                  border: 'none',
                  borderRadius: '0.5rem',
                  cursor: 'pointer',
                  textAlign: 'left',
                  fontSize: '0.875rem',
                  fontWeight: activeTab === item.key ? '600' : 'normal',
                  transition: 'all 0.3s ease'
                }}
                onMouseEnter={(e) => {
                  if (activeTab !== item.key) {
                    e.currentTarget.style.backgroundColor = 'var(--bg-hover)';
                    e.currentTarget.style.color = 'var(--text-primary)';
                  }
                }}
                onMouseLeave={(e) => {
                  if (activeTab !== item.key) {
                    e.currentTarget.style.backgroundColor = 'transparent';
                    e.currentTarget.style.color = 'var(--text-secondary)';
                  }
                }}
              >
                {item.label}
              </button>
            ))}
          </div>
        </nav>
      </div>
      
      {/* Main Area */}
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden'
      }}>
        {/* Header */}
        <div style={{
          height: '4rem',
          backgroundColor: 'var(--bg-secondary)',
          borderBottom: '1px solid var(--border-primary)',
          display: 'flex',
          alignItems: 'center',
          padding: '0 1.5rem',
          justifyContent: 'space-between'
        }}>
          <h1 style={{
            fontSize: '1.25rem',
            fontWeight: '600',
            color: 'var(--text-primary)'
          }}>
            {activeTab === 'scraping' && '🕷️ AI-Powered Web Scraper'}
            {activeTab === 'dashboard' && '📊 Dashboard'}
            {activeTab === 'llm' && '🤖 LLM Test Panel'}
            {activeTab === 'proxy' && '🔗 Proxy Management'}
            {activeTab === 'settings' && '⚙️ Settings'}
          </h1>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '1rem'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <div style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                backgroundColor: 'var(--success)'
              }} />
              <span style={{
                fontSize: '0.875rem',
                color: 'var(--text-secondary)'
              }}>
                Development Mode
              </span>
            </div>
          </div>
        </div>
        
        {/* Main Content */}
        <div style={{
          flex: 1,
          overflow: 'auto'
        }}>
          {activeTab === 'dashboard' && (
            <div style={{ padding: '2rem' }}>
              <div style={{
                backgroundColor: 'var(--bg-secondary)',
                borderRadius: '0.5rem',
                border: '1px solid var(--border-primary)',
                padding: '2rem',
                textAlign: 'center'
              }}>
                <h2 style={{
                  fontSize: '1.5rem',
                  fontWeight: '600',
                  color: 'var(--text-primary)',
                  marginBottom: '1rem'
                }}>
                  Welcome to AI Web Scraper
                </h2>
                <p style={{
                  color: 'var(--text-secondary)',
                  marginBottom: '2rem',
                  maxWidth: '32rem',
                  margin: '0 auto 2rem auto'
                }}>
                  Intelligent web scraping with AI-powered selector generation and data extraction.
                </p>
                <div style={{
                  display: 'flex',
                  gap: '1rem',
                  justifyContent: 'center',
                  flexWrap: 'wrap'
                }}>
                  <button 
                    onClick={() => setActiveTab('scraping')}
                    style={{
                      padding: '0.75rem 1.5rem',
                      backgroundColor: 'var(--accent-primary)',
                      color: 'var(--accent-text)',
                      border: 'none',
                      borderRadius: '500px',
                      cursor: 'pointer',
                      fontSize: '0.875rem',
                      fontWeight: '700',
                      textTransform: 'uppercase',
                      letterSpacing: '1px',
                      transition: 'all 0.3s ease'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = 'var(--accent-hover)';
                      e.currentTarget.style.transform = 'scale(1.04)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = 'var(--accent-primary)';
                      e.currentTarget.style.transform = 'scale(1)';
                    }}
                  >
                    🕷️ Start Scraping
                  </button>
                  <button 
                    onClick={() => setActiveTab('llm')}
                    style={{
                      padding: '0.75rem 1.5rem',
                      backgroundColor: 'transparent',
                      color: 'var(--accent-primary)',
                      border: '2px solid var(--accent-primary)',
                      borderRadius: '500px',
                      cursor: 'pointer',
                      fontSize: '0.875rem',
                      fontWeight: '700',
                      textTransform: 'uppercase',
                      letterSpacing: '1px',
                      transition: 'all 0.3s ease'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = 'var(--accent-primary)';
                      e.currentTarget.style.color = 'var(--accent-text)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = 'transparent';
                      e.currentTarget.style.color = 'var(--accent-primary)';
                    }}
                  >
                    🤖 Test AI
                  </button>
                  <button 
                    onClick={() => setActiveTab('proxy')}
                    style={{
                      padding: '0.75rem 1.5rem',
                      backgroundColor: 'transparent',
                      color: 'var(--accent-primary)',
                      border: '2px solid var(--accent-primary)',
                      borderRadius: '500px',
                      cursor: 'pointer',
                      fontSize: '0.875rem',
                      fontWeight: '700',
                      textTransform: 'uppercase',
                      letterSpacing: '1px',
                      transition: 'all 0.3s ease'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = 'var(--accent-primary)';
                      e.currentTarget.style.color = 'var(--accent-text)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = 'transparent';
                      e.currentTarget.style.color = 'var(--accent-primary)';
                    }}
                  >
                    🔗 Proxies
                  </button>
                </div>
              </div>
            </div>
          )}
          
          {activeTab === 'llm' && <LLMTestPanel />}
          
          {activeTab === 'proxy' && <ProxyDashboard />}
          
          {activeTab === 'scraping' && <ScrapingInterface />}
          
          {activeTab === 'settings' && (
            <div style={{ padding: '2rem' }}>
              <div style={{
                backgroundColor: 'var(--bg-secondary)',
                borderRadius: '0.5rem',
                border: '1px solid var(--border-primary)',
                padding: '2rem',
                textAlign: 'center'
              }}>
                <h2 style={{ fontSize: '1.5rem', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '1rem' }}>
                  ⚙️ Settings
                </h2>
                <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem' }}>
                  Configure application settings and preferences.
                </p>
                <div style={{ 
                  padding: '2rem', 
                  backgroundColor: 'var(--bg-tertiary)', 
                  borderRadius: '8px',
                  border: '1px dashed var(--border-primary)'
                }}>
                  <h3 style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>Settings Panel</h3>
                  <p style={{ color: 'var(--text-muted)' }}>Model configuration, API keys, dark theme, and preferences</p>
                </div>
              </div>
            </div>
          )}
        </div>
        
        {/* Status Bar */}
        <div style={{
          height: '2rem',
          backgroundColor: 'var(--bg-tertiary)',
          borderTop: '1px solid var(--border-primary)',
          display: 'flex',
          alignItems: 'center',
          padding: '0 1.5rem',
          fontSize: '0.75rem',
          color: 'var(--text-muted)',
          justifyContent: 'space-between'
        }}>
          <span>🟢 Ready • Development Mode</span>
          <span>Model: TinyLlama 1.1B • Theme: Dark Mode • Spotify Green</span>
        </div>
      </div>
    </div>
  );
};