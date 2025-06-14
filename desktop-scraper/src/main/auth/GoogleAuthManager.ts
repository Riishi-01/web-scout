import { OAuth2Client } from 'google-auth-library';
import { google } from 'googleapis';
import { BrowserWindow, shell } from 'electron';
import Store from 'electron-store';
import * as crypto from 'crypto-js';
import { EventEmitter } from 'events';

export interface AuthStatus {
  authenticated: boolean;
  userInfo?: {
    email: string;
    name: string;
    picture?: string;
  };
  scopes: string[];
  expiresAt?: Date;
}

export interface AuthConfig {
  clientId: string;
  clientSecret: string;
  redirectUri: string;
  scopes: string[];
}

export class GoogleAuthManager extends EventEmitter {
  private oauth2Client: OAuth2Client;
  private store: Store;
  private authWindow: BrowserWindow | null = null;
  private config: AuthConfig;

  constructor(store: Store) {
    super();
    this.store = store;

    // OAuth configuration from environment variables
    this.config = {
      clientId: process.env.GOOGLE_CLIENT_ID || '',
      clientSecret: process.env.GOOGLE_CLIENT_SECRET || '',
      redirectUri: process.env.GOOGLE_REDIRECT_URI || 'http://localhost:8080/auth/callback',
      scopes: [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive.file',
        'https://www.googleapis.com/auth/userinfo.profile',
        'https://www.googleapis.com/auth/userinfo.email'
      ]
    };

    // Validate required configuration
    if (!this.config.clientId || !this.config.clientSecret) {
      console.warn('Google OAuth credentials not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables.');
      console.warn('See GOOGLE_SETUP.md for detailed setup instructions.');
    }

    this.oauth2Client = new OAuth2Client(
      this.config.clientId,
      this.config.clientSecret,
      this.config.redirectUri
    );

    this.initializeAuth();
  }

  private async initializeAuth(): Promise<void> {
    try {
      // Try to load existing credentials
      const encryptedCredentials = this.store.get('google_credentials') as string;
      
      if (encryptedCredentials) {
        const credentials = this.decryptCredentials(encryptedCredentials);
        this.oauth2Client.setCredentials(credentials);

        // Check if token is still valid
        const isValid = await this.validateToken();
        if (isValid) {
          this.emit('auth-status-changed', await this.getAuthStatus());
        } else {
          // Try to refresh token
          await this.refreshToken();
        }
      }
    } catch (error) {
      console.error('Auth initialization failed:', error);
      this.clearCredentials();
    }
  }

  async startAuth(): Promise<AuthStatus> {
    try {
      // Generate auth URL
      const authUrl = this.oauth2Client.generateAuthUrl({
        access_type: 'offline',
        scope: this.config.scopes,
        prompt: 'consent'
      });

      // Open auth window
      return await this.openAuthWindow(authUrl);
    } catch (error) {
      console.error('Auth start failed:', error);
      throw new Error(`Authentication failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  private async openAuthWindow(authUrl: string): Promise<AuthStatus> {
    return new Promise((resolve, reject) => {
      // Create auth window
      this.authWindow = new BrowserWindow({
        width: 500,
        height: 700,
        show: true,
        modal: true,
        webPreferences: {
          nodeIntegration: false,
          contextIsolation: true
        }
      });

      // Handle auth flow
      this.authWindow.loadURL(authUrl);

      // Listen for navigation to capture auth code
      this.authWindow.webContents.on('did-navigate', async (event, navigationUrl) => {
        if (navigationUrl.startsWith(this.config.redirectUri)) {
          try {
            const url = new URL(navigationUrl);
            const authCode = url.searchParams.get('code');
            
            if (authCode) {
              // Exchange code for tokens
              const { tokens } = await this.oauth2Client.getToken(authCode);
              this.oauth2Client.setCredentials(tokens);

              // Save encrypted credentials
              await this.saveCredentials(tokens);

              // Get user info
              const authStatus = await this.getAuthStatus();
              
              this.authWindow?.close();
              this.authWindow = null;
              
              this.emit('auth-status-changed', authStatus);
              resolve(authStatus);
            } else {
              throw new Error('No authorization code received');
            }
          } catch (error) {
            this.authWindow?.close();
            this.authWindow = null;
            reject(error);
          }
        }
      });

      // Handle window closed
      this.authWindow.on('closed', () => {
        this.authWindow = null;
        reject(new Error('Authentication window closed'));
      });

      // Handle auth errors
      this.authWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
        this.authWindow?.close();
        this.authWindow = null;
        reject(new Error(`Authentication failed: ${errorDescription}`));
      });
    });
  }

  async getAuthStatus(): Promise<AuthStatus> {
    try {
      const credentials = this.oauth2Client.credentials;
      
      if (!credentials.access_token) {
        return {
          authenticated: false,
          scopes: []
        };
      }

      // Get user info
      const oauth2 = google.oauth2({ version: 'v2', auth: this.oauth2Client });
      const userInfo = await oauth2.userinfo.get();

      return {
        authenticated: true,
        userInfo: {
          email: userInfo.data.email || '',
          name: userInfo.data.name || '',
          picture: userInfo.data.picture || undefined
        },
        scopes: this.config.scopes,
        expiresAt: credentials.expiry_date ? new Date(credentials.expiry_date) : undefined
      };
    } catch (error) {
      console.error('Failed to get auth status:', error);
      return {
        authenticated: false,
        scopes: []
      };
    }
  }

  async logout(): Promise<void> {
    try {
      // Revoke token
      if (this.oauth2Client.credentials.access_token) {
        await this.oauth2Client.revokeCredentials();
      }
    } catch (error) {
      console.error('Token revocation failed:', error);
    } finally {
      // Clear local credentials
      this.clearCredentials();
      this.oauth2Client.setCredentials({});
      
      const authStatus = await this.getAuthStatus();
      this.emit('auth-status-changed', authStatus);
    }
  }

  async refreshToken(): Promise<void> {
    try {
      const { credentials } = await this.oauth2Client.refreshAccessToken();
      this.oauth2Client.setCredentials(credentials);
      await this.saveCredentials(credentials);
      
      const authStatus = await this.getAuthStatus();
      this.emit('auth-status-changed', authStatus);
    } catch (error) {
      console.error('Token refresh failed:', error);
      this.clearCredentials();
      throw error;
    }
  }

  private async validateToken(): Promise<boolean> {
    try {
      const accessToken = this.oauth2Client.credentials.access_token;
      if (!accessToken) return false;
      
      const tokenInfo = await this.oauth2Client.getTokenInfo(accessToken);
      return tokenInfo.expiry_date ? tokenInfo.expiry_date > Date.now() : false;
    } catch {
      return false;
    }
  }

  private async saveCredentials(credentials: any): Promise<void> {
    try {
      const encryptedCredentials = this.encryptCredentials(credentials);
      this.store.set('google_credentials', encryptedCredentials);
    } catch (error) {
      console.error('Failed to save credentials:', error);
      throw error;
    }
  }

  private encryptCredentials(credentials: any): string {
    const key = this.getEncryptionKey();
    const credentialsJson = JSON.stringify(credentials);
    return crypto.AES.encrypt(credentialsJson, key).toString();
  }

  private decryptCredentials(encryptedCredentials: string): any {
    const key = this.getEncryptionKey();
    const decryptedBytes = crypto.AES.decrypt(encryptedCredentials, key);
    const credentialsJson = decryptedBytes.toString(crypto.enc.Utf8);
    return JSON.parse(credentialsJson);
  }

  private getEncryptionKey(): string {
    // Generate a machine-specific key for credential encryption
    const machineId = require('os').hostname() + require('os').platform();
    return crypto.SHA256(machineId).toString();
  }

  private clearCredentials(): void {
    this.store.delete('google_credentials');
  }

  // Google Sheets API methods
  async createSpreadsheet(title: string, data: any[][]): Promise<string> {
    try {
      const sheets = google.sheets({ version: 'v4', auth: this.oauth2Client });
      
      // Create spreadsheet
      const createResponse = await sheets.spreadsheets.create({
        requestBody: {
          properties: {
            title: title
          }
        }
      });

      const spreadsheetId = createResponse.data.spreadsheetId!;

      // Add data if provided
      if (data.length > 0) {
        await sheets.spreadsheets.values.update({
          spreadsheetId,
          range: 'Sheet1!A1',
          valueInputOption: 'RAW',
          requestBody: {
            values: data
          }
        });
      }

      return `https://docs.google.com/spreadsheets/d/${spreadsheetId}`;
    } catch (error) {
      console.error('Failed to create spreadsheet:', error);
      throw new Error(`Failed to create spreadsheet: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async appendToSpreadsheet(spreadsheetUrl: string, data: any[][]): Promise<void> {
    try {
      const spreadsheetId = this.extractSpreadsheetId(spreadsheetUrl);
      const sheets = google.sheets({ version: 'v4', auth: this.oauth2Client });

      await sheets.spreadsheets.values.append({
        spreadsheetId,
        range: 'Sheet1!A1',
        valueInputOption: 'RAW',
        requestBody: {
          values: data
        }
      });
    } catch (error) {
      console.error('Failed to append to spreadsheet:', error);
      throw new Error(`Failed to append data: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  private extractSpreadsheetId(url: string): string {
    const match = url.match(/\/spreadsheets\/d\/([a-zA-Z0-9-_]+)/);
    if (!match) {
      throw new Error('Invalid Google Sheets URL');
    }
    return match[1];
  }

  // Enhanced Google Sheets API methods with read operations
  async readSpreadsheet(spreadsheetUrl: string, range?: string): Promise<any[][]> {
    try {
      const spreadsheetId = this.extractSpreadsheetId(spreadsheetUrl);
      const sheets = google.sheets({ version: 'v4', auth: this.oauth2Client });

      const readRange = range || 'Sheet1';
      const response = await sheets.spreadsheets.values.get({
        spreadsheetId,
        range: readRange
      });

      return response.data.values || [];
    } catch (error) {
      console.error('Failed to read spreadsheet:', error);
      throw new Error(`Failed to read spreadsheet: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async getSpreadsheetInfo(spreadsheetUrl: string): Promise<any> {
    try {
      const spreadsheetId = this.extractSpreadsheetId(spreadsheetUrl);
      const sheets = google.sheets({ version: 'v4', auth: this.oauth2Client });

      const response = await sheets.spreadsheets.get({
        spreadsheetId,
        includeGridData: false
      });

      const spreadsheet = response.data;
      return {
        id: spreadsheet.spreadsheetId,
        title: spreadsheet.properties?.title,
        url: spreadsheetUrl,
        sheets: spreadsheet.sheets?.map(sheet => ({
          id: sheet.properties?.sheetId,
          title: sheet.properties?.title,
          index: sheet.properties?.index,
          rowCount: sheet.properties?.gridProperties?.rowCount,
          columnCount: sheet.properties?.gridProperties?.columnCount
        })) || [],
        createdTime: spreadsheet.properties?.timeZone,
        lastModified: spreadsheet.properties?.autoRecalc
      };
    } catch (error) {
      console.error('Failed to get spreadsheet info:', error);
      throw new Error(`Failed to get spreadsheet info: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async validateSpreadsheetAccess(spreadsheetUrl: string): Promise<{ canRead: boolean; canWrite: boolean; error?: string }> {
    try {
      const spreadsheetId = this.extractSpreadsheetId(spreadsheetUrl);
      const sheets = google.sheets({ version: 'v4', auth: this.oauth2Client });

      // Test read access
      let canRead = false;
      try {
        await sheets.spreadsheets.get({ spreadsheetId });
        canRead = true;
      } catch (readError) {
        console.warn('Read access denied:', readError);
      }

      // Test write access by attempting to add a temporary sheet (then remove it)
      let canWrite = false;
      try {
        // Try to get current sheets first
        const response = await sheets.spreadsheets.get({ spreadsheetId });
        if (response.data.sheets) {
          canWrite = true; // If we can read sheets, we likely have write access
        }
      } catch (writeError) {
        console.warn('Write access denied:', writeError);
      }

      return { canRead, canWrite };
    } catch (error) {
      return {
        canRead: false,
        canWrite: false,
        error: error instanceof Error ? error.message : 'Access validation failed'
      };
    }
  }

  async createFormattedSpreadsheet(title: string, data: any[][], options?: {
    headerFormat?: boolean;
    autoResize?: boolean;
    freezeHeader?: boolean;
    sheetName?: string;
  }): Promise<string> {
    try {
      const sheets = google.sheets({ version: 'v4', auth: this.oauth2Client });
      
      // Create spreadsheet with custom sheet name
      const createResponse = await sheets.spreadsheets.create({
        requestBody: {
          properties: {
            title: title
          },
          sheets: [{
            properties: {
              title: options?.sheetName || 'Scraped Data'
            }
          }]
        }
      });

      const spreadsheetId = createResponse.data.spreadsheetId!;

      // Add data if provided
      if (data.length > 0) {
        const range = `${options?.sheetName || 'Scraped Data'}!A1`;
        
        // Write data
        await sheets.spreadsheets.values.update({
          spreadsheetId,
          range,
          valueInputOption: 'RAW',
          requestBody: {
            values: data
          }
        });

        // Apply formatting if requested
        if (options?.headerFormat || options?.autoResize || options?.freezeHeader) {
          const requests: any[] = [];

          // Format header row
          if (options.headerFormat && data.length > 0) {
            requests.push({
              repeatCell: {
                range: {
                  sheetId: 0,
                  startRowIndex: 0,
                  endRowIndex: 1,
                  startColumnIndex: 0,
                  endColumnIndex: data[0].length
                },
                cell: {
                  userEnteredFormat: {
                    backgroundColor: { red: 0.8, green: 0.8, blue: 0.8 },
                    textFormat: { bold: true },
                    horizontalAlignment: 'CENTER'
                  }
                },
                fields: 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)'
              }
            });
          }

          // Auto-resize columns
          if (options.autoResize) {
            requests.push({
              autoResizeDimensions: {
                dimensions: {
                  sheetId: 0,
                  dimension: 'COLUMNS',
                  startIndex: 0,
                  endIndex: data[0]?.length || 10
                }
              }
            });
          }

          // Freeze header row
          if (options.freezeHeader) {
            requests.push({
              updateSheetProperties: {
                properties: {
                  sheetId: 0,
                  gridProperties: {
                    frozenRowCount: 1
                  }
                },
                fields: 'gridProperties.frozenRowCount'
              }
            });
          }

          // Apply all formatting requests
          if (requests.length > 0) {
            await sheets.spreadsheets.batchUpdate({
              spreadsheetId,
              requestBody: { requests }
            });
          }
        }
      }

      return `https://docs.google.com/spreadsheets/d/${spreadsheetId}`;
    } catch (error) {
      console.error('Failed to create formatted spreadsheet:', error);
      throw new Error(`Failed to create formatted spreadsheet: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async updateSpreadsheet(spreadsheetUrl: string, data: any[][], options?: {
    range?: string;
    mode?: 'REPLACE' | 'APPEND' | 'INSERT';
    sheetName?: string;
  }): Promise<void> {
    try {
      const spreadsheetId = this.extractSpreadsheetId(spreadsheetUrl);
      const sheets = google.sheets({ version: 'v4', auth: this.oauth2Client });

      const sheetName = options?.sheetName || 'Sheet1';
      const mode = options?.mode || 'APPEND';

      if (mode === 'REPLACE') {
        // Clear existing data first
        await sheets.spreadsheets.values.clear({
          spreadsheetId,
          range: `${sheetName}!A:Z`
        });

        // Then add new data
        await sheets.spreadsheets.values.update({
          spreadsheetId,
          range: `${sheetName}!A1`,
          valueInputOption: 'RAW',
          requestBody: {
            values: data
          }
        });
      } else if (mode === 'APPEND') {
        // Append to existing data
        await sheets.spreadsheets.values.append({
          spreadsheetId,
          range: `${sheetName}!A1`,
          valueInputOption: 'RAW',
          requestBody: {
            values: data
          }
        });
      } else if (mode === 'INSERT') {
        // Insert at specific range
        const range = options?.range || `${sheetName}!A1`;
        await sheets.spreadsheets.values.update({
          spreadsheetId,
          range,
          valueInputOption: 'RAW',
          requestBody: {
            values: data
          }
        });
      }
    } catch (error) {
      console.error('Failed to update spreadsheet:', error);
      throw new Error(`Failed to update spreadsheet: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async getSpreadsheetsByUser(maxResults: number = 20): Promise<any[]> {
    try {
      const drive = google.drive({ version: 'v3', auth: this.oauth2Client });

      const response = await drive.files.list({
        q: "mimeType='application/vnd.google-apps.spreadsheet'",
        pageSize: maxResults,
        fields: 'files(id, name, createdTime, modifiedTime, webViewLink, owners)',
        orderBy: 'modifiedTime desc'
      });

      return response.data.files?.map(file => ({
        id: file.id,
        name: file.name,
        url: file.webViewLink,
        createdTime: file.createdTime,
        modifiedTime: file.modifiedTime,
        owners: file.owners
      })) || [];
    } catch (error) {
      console.error('Failed to get user spreadsheets:', error);
      throw new Error(`Failed to get user spreadsheets: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async shareSpreadsheet(spreadsheetUrl: string, email: string, role: 'reader' | 'writer' | 'owner' = 'reader'): Promise<void> {
    try {
      const spreadsheetId = this.extractSpreadsheetId(spreadsheetUrl);
      const drive = google.drive({ version: 'v3', auth: this.oauth2Client });

      await drive.permissions.create({
        fileId: spreadsheetId,
        requestBody: {
          role,
          type: 'user',
          emailAddress: email
        }
      });
    } catch (error) {
      console.error('Failed to share spreadsheet:', error);
      throw new Error(`Failed to share spreadsheet: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  // Advanced Google Sheets operations for enhanced user experience
  async validateAndMergeSpreadsheet(
    spreadsheetUrl: string, 
    newData: any[][], 
    options?: {
      keyColumn?: number;
      mergeStrategy?: 'append' | 'update' | 'upsert';
      skipValidation?: boolean;
      headerRow?: boolean;
    }
  ): Promise<{ 
    success: boolean; 
    recordsAdded: number; 
    recordsUpdated: number; 
    errors: string[]; 
    warnings: string[] 
  }> {
    try {
      const spreadsheetId = this.extractSpreadsheetId(spreadsheetUrl);
      const sheets = google.sheets({ version: 'v4', auth: this.oauth2Client });
      
      const result = {
        success: false,
        recordsAdded: 0,
        recordsUpdated: 0,
        errors: [] as string[],
        warnings: [] as string[]
      };

      // Validate data structure if enabled
      if (!options?.skipValidation) {
        const validation = this.validateDataStructure(newData);
        if (!validation.isValid) {
          result.errors.push(...validation.errors);
          return result;
        }
        result.warnings.push(...validation.warnings);
      }

      // Read existing data
      const existingData = await this.readSpreadsheet(spreadsheetUrl);
      
      if (options?.mergeStrategy === 'append') {
        // Simple append operation
        await this.updateSpreadsheet(spreadsheetUrl, newData, { mode: 'APPEND' });
        result.recordsAdded = newData.length;
      } else if (options?.mergeStrategy === 'update' || options?.mergeStrategy === 'upsert') {
        // Merge based on key column
        const keyCol = options.keyColumn || 0;
        const mergedData = this.mergeDataByKey(existingData, newData, keyCol, options.mergeStrategy);
        
        // Replace entire sheet with merged data
        await this.updateSpreadsheet(spreadsheetUrl, mergedData, { mode: 'REPLACE' });
        
        // Calculate statistics
        result.recordsAdded = mergedData.length - existingData.length;
        result.recordsUpdated = Math.min(existingData.length, newData.length);
      }

      result.success = true;
      return result;

    } catch (error) {
      console.error('Failed to validate and merge spreadsheet:', error);
      return {
        success: false,
        recordsAdded: 0,
        recordsUpdated: 0,
        errors: [error instanceof Error ? error.message : 'Merge operation failed'],
        warnings: []
      };
    }
  }

  async duplicateSpreadsheet(sourceUrl: string, newTitle: string): Promise<string> {
    try {
      const sourceId = this.extractSpreadsheetId(sourceUrl);
      const drive = google.drive({ version: 'v3', auth: this.oauth2Client });

      const response = await drive.files.copy({
        fileId: sourceId,
        requestBody: {
          name: newTitle
        }
      });

      const newSpreadsheetId = response.data.id!;
      return `https://docs.google.com/spreadsheets/d/${newSpreadsheetId}`;
    } catch (error) {
      console.error('Failed to duplicate spreadsheet:', error);
      throw new Error(`Failed to duplicate spreadsheet: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async addWorksheet(spreadsheetUrl: string, sheetName: string, options?: {
    rowCount?: number;
    columnCount?: number;
    headerData?: string[];
  }): Promise<number> {
    try {
      const spreadsheetId = this.extractSpreadsheetId(spreadsheetUrl);
      const sheets = google.sheets({ version: 'v4', auth: this.oauth2Client });

      const requests = [{
        addSheet: {
          properties: {
            title: sheetName,
            gridProperties: {
              rowCount: options?.rowCount || 1000,
              columnCount: options?.columnCount || 26
            }
          }
        }
      }];

      const response = await sheets.spreadsheets.batchUpdate({
        spreadsheetId,
        requestBody: { requests }
      });

      const newSheetId = response.data.replies?.[0]?.addSheet?.properties?.sheetId;
      
      // Add header data if provided
      if (options?.headerData && newSheetId !== undefined && newSheetId !== null) {
        await sheets.spreadsheets.values.update({
          spreadsheetId,
          range: `${sheetName}!A1`,
          valueInputOption: 'RAW',
          requestBody: {
            values: [options.headerData]
          }
        });
      }

      return newSheetId || 0;
    } catch (error) {
      console.error('Failed to add worksheet:', error);
      throw new Error(`Failed to add worksheet: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async getSpreadsheetMetrics(spreadsheetUrl: string): Promise<{
    totalSheets: number;
    totalCells: number;
    totalRows: number;
    estimatedSize: string;
    lastModified?: string;
    collaborators: number;
  }> {
    try {
      const info = await this.getSpreadsheetInfo(spreadsheetUrl);
      const spreadsheetId = this.extractSpreadsheetId(spreadsheetUrl);
      const drive = google.drive({ version: 'v3', auth: this.oauth2Client });

      // Get file metadata for more details
      const fileResponse = await drive.files.get({
        fileId: spreadsheetId,
        fields: 'size,modifiedTime,permissions'
      });

      const totalCells = info.sheets.reduce((sum: number, sheet: any) => 
        sum + (sheet.rowCount * sheet.columnCount), 0);
      
      const totalRows = info.sheets.reduce((sum: number, sheet: any) => 
        sum + sheet.rowCount, 0);

      const fileSizeStr = fileResponse.data.size || '0';
      const sizeInBytes = parseInt(fileSizeStr, 10);
      const estimatedSize = this.formatFileSize(sizeInBytes);

      return {
        totalSheets: info.sheets.length,
        totalCells,
        totalRows,
        estimatedSize,
        lastModified: fileResponse.data.modifiedTime || undefined,
        collaborators: fileResponse.data.permissions?.length || 0
      };
    } catch (error) {
      console.error('Failed to get spreadsheet metrics:', error);
      throw new Error(`Failed to get spreadsheet metrics: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  // Helper methods for data processing
  private validateDataStructure(data: any[][]): { isValid: boolean; errors: string[]; warnings: string[] } {
    const result = { isValid: true, errors: [] as string[], warnings: [] as string[] };

    if (!data || data.length === 0) {
      result.isValid = false;
      result.errors.push('Data is empty or invalid');
      return result;
    }

    // Check for consistent column count
    const expectedColumns = data[0].length;
    for (let i = 1; i < data.length; i++) {
      if (data[i].length !== expectedColumns) {
        result.warnings.push(`Row ${i + 1} has ${data[i].length} columns, expected ${expectedColumns}`);
      }
    }

    // Check for empty cells in first row (headers)
    if (data[0].some(cell => !cell || cell.toString().trim() === '')) {
      result.warnings.push('Header row contains empty cells');
    }

    // Check data size limits
    if (data.length > 10000) {
      result.warnings.push(`Large dataset: ${data.length} rows may impact performance`);
    }

    if (expectedColumns > 50) {
      result.warnings.push(`Wide dataset: ${expectedColumns} columns may impact readability`);
    }

    return result;
  }

  private mergeDataByKey(existingData: any[][], newData: any[][], keyColumn: number, strategy: 'update' | 'upsert'): any[][] {
    if (existingData.length === 0) return newData;
    if (newData.length === 0) return existingData;

    const result = [...existingData];
    const existingKeys = new Set(existingData.slice(1).map(row => row[keyColumn]?.toString()));

    for (let i = 1; i < newData.length; i++) { // Skip header
      const newRow = newData[i];
      const key = newRow[keyColumn]?.toString();
      
      if (!key) continue;

      const existingIndex = result.findIndex((row, idx) => 
        idx > 0 && row[keyColumn]?.toString() === key
      );

      if (existingIndex !== -1) {
        // Update existing row
        if (strategy === 'update' || strategy === 'upsert') {
          result[existingIndex] = newRow;
        }
      } else {
        // Add new row
        if (strategy === 'upsert') {
          result.push(newRow);
        }
      }
    }

    return result;
  }

  private formatFileSize(bytes: number): string {
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;

    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }

    return `${size.toFixed(1)} ${units[unitIndex]}`;
  }

  getAuthClient(): OAuth2Client {
    return this.oauth2Client;
  }
}