import { contextBridge, ipcRenderer } from 'electron';

// Define the API that will be exposed to the renderer process
const electronAPI = {
  // Authentication methods
  auth: {
    getStatus: () => ipcRenderer.invoke('auth:getStatus'),
    startAuth: () => ipcRenderer.invoke('auth:startAuth'),
    logout: () => ipcRenderer.invoke('auth:logout')
  },

  // Model management methods
  model: {
    getStatus: () => ipcRenderer.invoke('model:getStatus'),
    loadModel: () => ipcRenderer.invoke('model:loadModel'),
    generateText: (prompt: string, options?: any) => 
      ipcRenderer.invoke('model:generateText', prompt, options),
    analyzeWebPage: (html: string, prompt: string) =>
      ipcRenderer.invoke('model:analyzeWebPage', html, prompt),
    generateSelectors: (html: string) =>
      ipcRenderer.invoke('model:generateSelectors', html)
  },

  // Scraping methods
  scraping: {
    startScraping: (config: any) => ipcRenderer.invoke('scraping:startScraping', config),
    stopScraping: (taskId: string) => ipcRenderer.invoke('scraping:stopScraping', taskId),
    previewScraping: (config: any) => ipcRenderer.invoke('scraping:previewScraping', config),
    getStatus: (taskId: string) => ipcRenderer.invoke('scraping:getStatus', taskId)
  },

  // Google Sheets methods
  sheets: {
    createSpreadsheet: (title: string, data: any[][]) => 
      ipcRenderer.invoke('sheets:createSpreadsheet', title, data),
    readSpreadsheet: (url: string, range?: string) =>
      ipcRenderer.invoke('sheets:readSpreadsheet', url, range),
    updateSpreadsheet: (url: string, data: any[][], options?: any) =>
      ipcRenderer.invoke('sheets:updateSpreadsheet', url, data, options),
    getSpreadsheetInfo: (url: string) =>
      ipcRenderer.invoke('sheets:getSpreadsheetInfo', url),
    createFormattedSpreadsheet: (title: string, data: any[][], options?: any) =>
      ipcRenderer.invoke('sheets:createFormattedSpreadsheet', title, data, options),
    validateSpreadsheetAccess: (url: string) =>
      ipcRenderer.invoke('sheets:validateSpreadsheetAccess', url)
  },

  // Proxy management methods
  proxy: {
    getProxies: () => ipcRenderer.invoke('proxy:getProxies'),
    addCustomProxy: (proxyData: any) => ipcRenderer.invoke('proxy:addCustomProxy', proxyData),
    removeProxy: (proxyId: string) => ipcRenderer.invoke('proxy:removeProxy', proxyId),
    testProxy: (proxyId: string) => ipcRenderer.invoke('proxy:testProxy', proxyId),
    getProxyStats: () => ipcRenderer.invoke('proxy:getProxyStats'),
    updatePoolConfig: (config: any) => ipcRenderer.invoke('proxy:updatePoolConfig', config),
    forceHealthCheck: () => ipcRenderer.invoke('proxy:forceHealthCheck'),
    addProvider: (config: any) => ipcRenderer.invoke('proxy:addProvider', config),
    removeProvider: (type: any) => ipcRenderer.invoke('proxy:removeProvider', type),
    getProviderQuotas: () => ipcRenderer.invoke('proxy:getProviderQuotas')
  },

  // Settings methods
  settings: {
    get: (key: string) => ipcRenderer.invoke('settings:get', key),
    set: (key: string, value: any) => ipcRenderer.invoke('settings:set', key, value),
    export: () => ipcRenderer.invoke('settings:export')
  },

  // App control methods
  app: {
    version: () => ipcRenderer.invoke('app:version'),
    quit: () => ipcRenderer.invoke('app:quit'),
    minimize: () => ipcRenderer.invoke('app:minimize'),
    close: () => ipcRenderer.invoke('app:close')
  },

  // Event listeners
  on: (channel: string, callback: Function) => {
    const validChannels = [
      'show-setup-wizard',
      'new-scraping-task',
      'save-configuration',
      'load-configuration',
      'show-preferences',
      'start-scraping',
      'stop-scraping',
      'preview-data',
      'show-about',
      'scraping-progress',
      'scraping-complete',
      'scraping-error',
      'model-loading',
      'model-ready',
      'model-error'
    ];

    if (validChannels.includes(channel)) {
      const subscription = (event: any, ...args: any[]) => callback(...args);
      ipcRenderer.on(channel, subscription);

      // Return unsubscribe function
      return () => ipcRenderer.removeListener(channel, subscription);
    }
  },

  // Remove all listeners for a channel
  removeAllListeners: (channel: string) => {
    ipcRenderer.removeAllListeners(channel);
  }
};

// Expose the API to the renderer process
contextBridge.exposeInMainWorld('electronAPI', electronAPI);

// Type definitions for TypeScript
declare global {
  interface Window {
    electronAPI: typeof electronAPI;
  }
}