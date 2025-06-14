import { app, BrowserWindow, Menu, shell, ipcMain, dialog, Tray, nativeImage } from 'electron';
import { autoUpdater } from 'electron-updater';
import * as path from 'path';
import Store from 'electron-store';
import { ScrapingEngine } from './scraping/ScrapingEngine';
import { ModelManager } from './ai/ModelManager';
import { GoogleAuthManager } from './auth/GoogleAuthManager';
import { ProxyManager } from './proxy/ProxyManager';

class MainApp {
  private mainWindow: BrowserWindow | null = null;
  private tray: Tray | null = null;
  private store: Store<Record<string, unknown>>;
  private scrapingEngine: ScrapingEngine;
  private modelManager: ModelManager;
  private authManager: GoogleAuthManager;
  private proxyManager: ProxyManager;
  private isDev: boolean = process.env.NODE_ENV === 'development';

  constructor() {
    this.store = new Store<Record<string, unknown>>({
      schema: {
        windowBounds: {
          type: 'object',
          properties: {
            x: { type: 'number' },
            y: { type: 'number' },
            width: { type: 'number' },
            height: { type: 'number' }
          },
          default: { width: 1200, height: 800 }
        },
        theme: {
          type: 'string',
          enum: ['light', 'dark', 'system'],
          default: 'system'
        },
        autoLaunch: {
          type: 'boolean',
          default: false
        },
        firstTime: {
          type: 'boolean',
          default: true
        }
      }
    });

    this.modelManager = new ModelManager();
    this.authManager = new GoogleAuthManager(this.store);
    this.proxyManager = new ProxyManager(this.store);
    this.scrapingEngine = new ScrapingEngine(this.modelManager, this.authManager);

    this.initializeApp();
  }

  private async initializeApp(): Promise<void> {
    // Configure auto-updater
    if (!this.isDev) {
      autoUpdater.checkForUpdatesAndNotify();
    }

    // Set application menu
    this.createApplicationMenu();

    // Handle app events
    app.on('ready', this.onAppReady.bind(this));
    app.on('window-all-closed', this.onWindowAllClosed.bind(this));
    app.on('activate', this.onActivate.bind(this));
    app.on('before-quit', this.onBeforeQuit.bind(this));

    // Setup IPC handlers
    this.setupIpcHandlers();
  }

  private async onAppReady(): Promise<void> {
    // Create main window
    await this.createMainWindow();

    // Create system tray
    this.createSystemTray();

    // Initialize model manager
    await this.modelManager.initialize();

    // Initialize proxy manager
    await this.proxyManager.initialize();

    // Check for first time setup
    if (this.store.get('firstTime')) {
      this.mainWindow?.webContents.send('show-setup-wizard');
    }
  }

  private async createMainWindow(): Promise<void> {
    const windowBounds = this.store.get('windowBounds', { width: 1200, height: 800 }) as any;

    this.mainWindow = new BrowserWindow({
      ...windowBounds,
      minWidth: 1000,
      minHeight: 700,
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        enableRemoteModule: false,
        preload: this.isDev 
          ? path.join(__dirname, '../src/main/preload.ts')
          : path.join(__dirname, '../main/preload.js'),
        webSecurity: !this.isDev
      },
      icon: this.getIconPath(),
      show: false,
      titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default'
    });

    // Load the application
    const startUrl = this.isDev 
      ? 'http://localhost:3000' 
      : `file://${path.join(__dirname, '../../build/index.html')}`;

    await this.mainWindow.loadURL(startUrl);

    // Show window when ready
    this.mainWindow.once('ready-to-show', () => {
      this.mainWindow?.show();
      
      if (this.isDev) {
        this.mainWindow?.webContents.openDevTools();
      }
    });

    // Handle window events
    this.mainWindow.on('closed', () => {
      this.mainWindow = null;
    });

    this.mainWindow.on('resize', () => {
      this.saveWindowBounds();
    });

    this.mainWindow.on('move', () => {
      this.saveWindowBounds();
    });

    // Handle external links
    this.mainWindow.webContents.setWindowOpenHandler(({ url }) => {
      shell.openExternal(url);
      return { action: 'deny' };
    });
  }

  private createSystemTray(): void {
    const trayIcon = nativeImage.createFromPath(this.getIconPath()).resize({ width: 16, height: 16 });
    this.tray = new Tray(trayIcon);

    const contextMenu = Menu.buildFromTemplate([
      {
        label: 'Show App',
        click: () => {
          this.mainWindow?.show();
        }
      },
      {
        label: 'Hide App',
        click: () => {
          this.mainWindow?.hide();
        }
      },
      { type: 'separator' },
      {
        label: 'Quit',
        click: () => {
          app.quit();
        }
      }
    ]);

    this.tray.setContextMenu(contextMenu);
    this.tray.setToolTip('Local Web Scraper');

    this.tray.on('click', () => {
      this.mainWindow?.isVisible() ? this.mainWindow.hide() : this.mainWindow?.show();
    });
  }

  private createApplicationMenu(): void {
    const template = [
      {
        label: 'File',
        submenu: [
          {
            label: 'New Scraping Task',
            accelerator: 'CmdOrCtrl+N',
            click: () => {
              this.mainWindow?.webContents.send('new-scraping-task');
            }
          },
          {
            label: 'Open Configuration',
            accelerator: 'CmdOrCtrl+O',
            click: this.openConfiguration.bind(this)
          },
          {
            label: 'Save Configuration',
            accelerator: 'CmdOrCtrl+S',
            click: () => {
              this.mainWindow?.webContents.send('save-configuration');
            }
          },
          { type: 'separator' },
          {
            label: 'Preferences',
            accelerator: 'CmdOrCtrl+,',
            click: () => {
              this.mainWindow?.webContents.send('show-preferences');
            }
          },
          { type: 'separator' },
          {
            label: 'Quit',
            accelerator: process.platform === 'darwin' ? 'Cmd+Q' : 'Ctrl+Q',
            click: () => {
              app.quit();
            }
          }
        ]
      },
      {
        label: 'Edit',
        submenu: [
          { role: 'undo' },
          { role: 'redo' },
          { type: 'separator' },
          { role: 'cut' },
          { role: 'copy' },
          { role: 'paste' },
          { role: 'selectall' }
        ]
      },
      {
        label: 'View',
        submenu: [
          { role: 'reload' },
          { role: 'forceReload' },
          { role: 'toggleDevTools' },
          { type: 'separator' },
          { role: 'resetZoom' },
          { role: 'zoomIn' },
          { role: 'zoomOut' },
          { type: 'separator' },
          { role: 'togglefullscreen' }
        ]
      },
      {
        label: 'Scraping',
        submenu: [
          {
            label: 'Start Scraping',
            accelerator: 'F5',
            click: () => {
              this.mainWindow?.webContents.send('start-scraping');
            }
          },
          {
            label: 'Stop Scraping',
            accelerator: 'Shift+F5',
            click: () => {
              this.mainWindow?.webContents.send('stop-scraping');
            }
          },
          { type: 'separator' },
          {
            label: 'Preview Data',
            accelerator: 'CmdOrCtrl+P',
            click: () => {
              this.mainWindow?.webContents.send('preview-data');
            }
          }
        ]
      },
      {
        label: 'Help',
        submenu: [
          {
            label: 'Documentation',
            click: () => {
              shell.openExternal('https://github.com/local-scraper/docs');
            }
          },
          {
            label: 'Report Issue',
            click: () => {
              shell.openExternal('https://github.com/local-scraper/issues');
            }
          },
          { type: 'separator' },
          {
            label: 'About',
            click: () => {
              this.mainWindow?.webContents.send('show-about');
            }
          }
        ]
      }
    ];

    const menu = Menu.buildFromTemplate(template as any);
    Menu.setApplicationMenu(menu);
  }

  private setupIpcHandlers(): void {
    // Authentication handlers
    ipcMain.handle('auth:getStatus', async () => {
      try {
        return await this.authManager.getAuthStatus();
      } catch (error) {
        console.error('Auth status error:', error);
        throw error;
      }
    });

    ipcMain.handle('auth:startAuth', async () => {
      try {
        return await this.authManager.startAuth();
      } catch (error) {
        console.error('Google auth error:', error);
        throw error;
      }
    });

    ipcMain.handle('auth:logout', async () => {
      try {
        return await this.authManager.logout();
      } catch (error) {
        console.error('Logout error:', error);
        throw error;
      }
    });

    // Model management handlers
    ipcMain.handle('model:getStatus', async () => {
      return await this.modelManager.getStatus();
    });

    ipcMain.handle('model:loadModel', async () => {
      return await this.modelManager.loadModel();
    });

    ipcMain.handle('model:generateText', async (event, prompt: string, options?: any) => {
      return await this.modelManager.runInference(prompt, options);
    });

    ipcMain.handle('model:analyzeWebPage', async (event, html: string, prompt: string) => {
      return await this.modelManager.analyzeWebPage(html, prompt);
    });

    ipcMain.handle('model:generateSelectors', async (event, html: string) => {
      return await this.modelManager.generateSelectors(html);
    });

    // Scraping handlers
    ipcMain.handle('scraping:startScraping', async (event, config: any) => {
      return await this.scrapingEngine.startScraping(config);
    });

    ipcMain.handle('scraping:stopScraping', async (event, taskId: string) => {
      return await this.scrapingEngine.stopScraping(taskId);
    });

    ipcMain.handle('scraping:previewScraping', async (event, config: any) => {
      return await this.scrapingEngine.previewScraping(config);
    });

    ipcMain.handle('scraping:getStatus', async (event, taskId: string) => {
      return await this.scrapingEngine.getScrapingStatus(taskId);
    });

    // Google Sheets handlers
    ipcMain.handle('sheets:createSpreadsheet', async (event, title: string, data: any[][]) => {
      try {
        return await this.authManager.createSpreadsheet(title, data);
      } catch (error) {
        console.error('Create spreadsheet error:', error);
        throw error;
      }
    });

    ipcMain.handle('sheets:readSpreadsheet', async (event, url: string, range?: string) => {
      try {
        return await this.authManager.readSpreadsheet(url, range);
      } catch (error) {
        console.error('Read spreadsheet error:', error);
        throw error;
      }
    });

    ipcMain.handle('sheets:updateSpreadsheet', async (event, url: string, data: any[][], options?: any) => {
      try {
        return await this.authManager.updateSpreadsheet(url, data, options);
      } catch (error) {
        console.error('Update spreadsheet error:', error);
        throw error;
      }
    });

    ipcMain.handle('sheets:getSpreadsheetInfo', async (event, url: string) => {
      try {
        return await this.authManager.getSpreadsheetInfo(url);
      } catch (error) {
        console.error('Get spreadsheet info error:', error);
        throw error;
      }
    });

    ipcMain.handle('sheets:createFormattedSpreadsheet', async (event, title: string, data: any[][], options?: any) => {
      try {
        return await this.authManager.createFormattedSpreadsheet(title, data, options);
      } catch (error) {
        console.error('Create formatted spreadsheet error:', error);
        throw error;
      }
    });

    ipcMain.handle('sheets:validateSpreadsheetAccess', async (event, url: string) => {
      try {
        return await this.authManager.validateSpreadsheetAccess(url);
      } catch (error) {
        console.error('Validate spreadsheet access error:', error);
        throw error;
      }
    });

    // Proxy management handlers
    ipcMain.handle('proxy:getProxies', async () => {
      try {
        return this.proxyManager.getProxies();
      } catch (error) {
        console.error('Get proxies error:', error);
        throw error;
      }
    });

    ipcMain.handle('proxy:addCustomProxy', async (event, proxyData: any) => {
      try {
        return await this.proxyManager.addCustomProxy(proxyData);
      } catch (error) {
        console.error('Add custom proxy error:', error);
        throw error;
      }
    });

    ipcMain.handle('proxy:removeProxy', async (event, proxyId: string) => {
      try {
        return await this.proxyManager.removeProxy(proxyId);
      } catch (error) {
        console.error('Remove proxy error:', error);
        throw error;
      }
    });

    ipcMain.handle('proxy:testProxy', async (event, proxyId: string) => {
      try {
        return await this.proxyManager.testProxy(proxyId);
      } catch (error) {
        console.error('Test proxy error:', error);
        throw error;
      }
    });

    ipcMain.handle('proxy:getProxyStats', async () => {
      try {
        return this.proxyManager.getProxyStats();
      } catch (error) {
        console.error('Get proxy stats error:', error);
        throw error;
      }
    });

    ipcMain.handle('proxy:updatePoolConfig', async (event, config: any) => {
      try {
        this.proxyManager.updatePoolConfig(config);
        return true;
      } catch (error) {
        console.error('Update pool config error:', error);
        throw error;
      }
    });

    ipcMain.handle('proxy:forceHealthCheck', async () => {
      try {
        await this.proxyManager.forceHealthCheck();
        return true;
      } catch (error) {
        console.error('Force health check error:', error);
        throw error;
      }
    });

    ipcMain.handle('proxy:addProvider', async (event, config: any) => {
      try {
        await this.proxyManager.addProvider(config);
        return true;
      } catch (error) {
        console.error('Add provider error:', error);
        throw error;
      }
    });

    ipcMain.handle('proxy:removeProvider', async (event, type: any) => {
      try {
        return await this.proxyManager.removeProvider(type);
      } catch (error) {
        console.error('Remove provider error:', error);
        throw error;
      }
    });

    ipcMain.handle('proxy:getProviderQuotas', async () => {
      try {
        return await this.proxyManager.getProviderQuotas();
      } catch (error) {
        console.error('Get provider quotas error:', error);
        throw error;
      }
    });

    // Settings handlers
    ipcMain.handle('settings:get', async (event, key: string) => {
      return this.store.get(key);
    });

    ipcMain.handle('settings:set', async (event, key: string, value: any) => {
      this.store.set(key, value);
      return true;
    });

    ipcMain.handle('settings:export', async () => {
      const result = await dialog.showSaveDialog(this.mainWindow!, {
        defaultPath: 'scraper-config.json',
        filters: [
          { name: 'JSON Files', extensions: ['json'] }
        ]
      });

      if (!result.canceled && result.filePath) {
        // Export configuration logic here
        return { success: true, path: result.filePath };
      }
      return { success: false };
    });

    // System handlers
    ipcMain.handle('app:version', () => {
      return app.getVersion();
    });

    ipcMain.handle('app:quit', () => {
      app.quit();
    });

    ipcMain.handle('app:minimize', () => {
      this.mainWindow?.minimize();
    });

    ipcMain.handle('app:close', () => {
      this.mainWindow?.close();
    });
  }

  private async openConfiguration(): Promise<void> {
    const result = await dialog.showOpenDialog(this.mainWindow!, {
      filters: [
        { name: 'JSON Files', extensions: ['json'] }
      ],
      properties: ['openFile']
    });

    if (!result.canceled && result.filePaths.length > 0) {
      this.mainWindow?.webContents.send('load-configuration', result.filePaths[0]);
    }
  }

  private saveWindowBounds(): void {
    if (this.mainWindow) {
      const bounds = this.mainWindow.getBounds();
      this.store.set('windowBounds', bounds);
    }
  }

  private getIconPath(): string {
    const iconName = process.platform === 'win32' ? 'icon.ico' : 
                     process.platform === 'darwin' ? 'icon.icns' : 'icon.png';
    return this.isDev 
      ? path.join(__dirname, '../../assets', iconName)
      : path.join(__dirname, '../../../assets', iconName);
  }

  private onWindowAllClosed(): void {
    if (process.platform !== 'darwin') {
      app.quit();
    }
  }

  private onActivate(): void {
    if (this.mainWindow === null) {
      this.createMainWindow();
    }
  }

  private onBeforeQuit(): void {
    // Cleanup resources
    this.scrapingEngine.cleanup();
    this.modelManager.cleanup();
    this.proxyManager.cleanup();
  }
}

// Initialize the application
new MainApp();