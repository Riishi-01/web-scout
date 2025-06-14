import React from 'react';

interface SetupWizardProps {
  onComplete: () => void;
}

export const SetupWizard: React.FC<SetupWizardProps> = ({ onComplete }) => {
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
        maxWidth: '32rem',
        width: '100%',
        backgroundColor: 'white',
        borderRadius: '0.5rem',
        border: '1px solid #e5e7eb',
        padding: '2rem',
        margin: '1rem'
      }}>
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <h1 style={{
            fontSize: '1.875rem',
            fontWeight: '700',
            color: '#111827',
            marginBottom: '0.5rem'
          }}>
            Welcome to Local Web Scraper
          </h1>
          <p style={{
            color: '#6b7280',
            fontSize: '1.125rem'
          }}>
            Let's get you set up with AI-powered web scraping
          </p>
        </div>

        <div style={{
          backgroundColor: '#f9fafb',
          borderRadius: '0.5rem',
          padding: '1.5rem',
          marginBottom: '2rem'
        }}>
          <h3 style={{
            fontSize: '1.125rem',
            fontWeight: '600',
            color: '#111827',
            marginBottom: '1rem'
          }}>
            Setup Status
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <div style={{
                width: '1.5rem',
                height: '1.5rem',
                backgroundColor: '#10b981',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <span style={{ color: 'white', fontSize: '0.75rem' }}>✓</span>
              </div>
              <span style={{ color: '#374151' }}>Application Framework</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <div style={{
                width: '1.5rem',
                height: '1.5rem',
                backgroundColor: '#f59e0b',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <span style={{ color: 'white', fontSize: '0.75rem' }}>!</span>
              </div>
              <span style={{ color: '#374151' }}>AI Model (Mock Mode)</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <div style={{
                width: '1.5rem',
                height: '1.5rem',
                backgroundColor: '#f59e0b',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <span style={{ color: 'white', fontSize: '0.75rem' }}>!</span>
              </div>
              <span style={{ color: '#374151' }}>Google Authentication (Mock Mode)</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <div style={{
                width: '1.5rem',
                height: '1.5rem',
                backgroundColor: '#10b981',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <span style={{ color: 'white', fontSize: '0.75rem' }}>✓</span>
              </div>
              <span style={{ color: '#374151' }}>Browser Engine</span>
            </div>
          </div>
        </div>

        <div style={{
          backgroundColor: '#eff6ff',
          borderRadius: '0.5rem',
          padding: '1rem',
          marginBottom: '2rem',
          border: '1px solid #dbeafe'
        }}>
          <p style={{
            color: '#1e40af',
            fontSize: '0.875rem',
            margin: 0
          }}>
            <strong>Development Mode:</strong> You're running in development mode with mock services. 
            Some features will use simulated data for testing purposes.
          </p>
        </div>

        <div style={{
          display: 'flex',
          gap: '1rem',
          justifyContent: 'center'
        }}>
          <button
            onClick={onComplete}
            style={{
              padding: '0.75rem 2rem',
              backgroundColor: '#3b82f6',
              color: 'white',
              border: 'none',
              borderRadius: '0.5rem',
              cursor: 'pointer',
              fontSize: '0.875rem',
              fontWeight: '500'
            }}
            onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#2563eb'}
            onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#3b82f6'}
          >
            Continue to Application
          </button>
        </div>
      </div>
    </div>
  );
};