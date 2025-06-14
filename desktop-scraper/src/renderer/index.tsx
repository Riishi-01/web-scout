import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';

// Ensure the DOM is ready
const container = document.getElementById('root');
if (!container) {
  throw new Error('Root element not found');
}

// Create React root and render app
const root = createRoot(container);
root.render(<App />);

// Hot module replacement for development
if ((module as any).hot) {
  (module as any).hot.accept('./App', () => {
    const NextApp = require('./App').default;
    root.render(<NextApp />);
  });
}