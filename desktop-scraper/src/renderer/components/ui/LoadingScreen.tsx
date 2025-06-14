import React from 'react';

interface LoadingScreenProps {
  message?: string;
}

export const LoadingScreen: React.FC<LoadingScreenProps> = ({ 
  message = "Loading..." 
}) => {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      backgroundColor: '#f9fafb',
      fontFamily: 'Inter, sans-serif'
    }}>
      <div style={{ textAlign: 'center' }}>
        <div style={{ marginBottom: '1rem' }}>
          <div style={{
            display: 'inline-block',
            width: '3rem',
            height: '3rem',
            border: '2px solid #e5e7eb',
            borderTop: '2px solid #2563eb',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite'
          }}></div>
        </div>
        <p style={{
          color: '#6b7280',
          fontSize: '1.125rem'
        }}>
          {message}
        </p>
      </div>
    </div>
  );
};