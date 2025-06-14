const { app, BrowserWindow } = require('electron');
const path = require('path');

async function startApp() {
  const isDev = process.env.NODE_ENV === 'development';

  // In development, we'll import from the TypeScript source
  // In production, we'll use the compiled JavaScript
  const mainPath = isDev 
    ? path.join(__dirname, '../src/main/main.ts')
    : path.join(__dirname, '../dist/main/main.js');

  // Require ts-node for development
  if (isDev) {
    require('ts-node').register({
      project: path.join(__dirname, '../tsconfig.json'),
      compilerOptions: {
        module: 'commonjs'
      }
    });
  }

  // Import the main application
  require(mainPath);
}

// Start the app
startApp().catch(console.error);