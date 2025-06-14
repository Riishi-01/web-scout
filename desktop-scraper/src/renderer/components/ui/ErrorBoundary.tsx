import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          backgroundColor: '#f9fafb',
          fontFamily: 'Inter, sans-serif'
        }}>
          <div style={{
            maxWidth: '28rem',
            margin: '0 auto',
            textAlign: 'center',
            padding: '2rem'
          }}>
            <div style={{ marginBottom: '1rem' }}>
              <svg
                style={{
                  margin: '0 auto',
                  height: '4rem',
                  width: '4rem',
                  color: '#ef4444'
                }}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"
                />
              </svg>
            </div>
            <h2 style={{
              fontSize: '1.5rem',
              fontWeight: 'bold',
              color: '#111827',
              marginBottom: '1rem'
            }}>
              Something went wrong
            </h2>
            <p style={{
              color: '#6b7280',
              marginBottom: '1.5rem'
            }}>
              The application encountered an unexpected error. Please try restarting the app.
            </p>
            {this.state.error && (
              <details style={{
                marginBottom: '1.5rem',
                textAlign: 'left'
              }}>
                <summary style={{
                  cursor: 'pointer',
                  fontSize: '0.875rem',
                  fontWeight: '500',
                  color: '#374151',
                  marginBottom: '0.5rem'
                }}>
                  Error Details
                </summary>
                <pre style={{
                  fontSize: '0.75rem',
                  backgroundColor: '#f3f4f6',
                  padding: '0.75rem',
                  borderRadius: '0.25rem',
                  border: '1px solid #e5e7eb',
                  overflow: 'auto',
                  maxHeight: '8rem'
                }}>
                  {this.state.error.toString()}
                </pre>
              </details>
            )}
            <button
              onClick={() => window.location.reload()}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: '#2563eb',
                color: 'white',
                border: 'none',
                borderRadius: '0.375rem',
                cursor: 'pointer',
                fontSize: '0.875rem',
                transition: 'background-color 0.2s'
              }}
              onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#1d4ed8'}
              onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#2563eb'}
            >
              Reload App
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}