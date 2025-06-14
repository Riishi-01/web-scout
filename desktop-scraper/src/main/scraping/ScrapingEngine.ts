import { EventEmitter } from 'events';
import { chromium, Browser, BrowserContext, Page } from 'playwright';
import { ModelManager } from '../ai/ModelManager';
import { GoogleAuthManager } from '../auth/GoogleAuthManager';
import { v4 as uuidv4 } from 'uuid';

export interface ScrapingConfig {
  id?: string;
  prompt: string;
  urls: string[];
  maxPages?: number;
  delay?: number;
  outputFormat: 'sheets' | 'csv' | 'json';
  outputDestination?: string;
  customSelectors?: string[];
  filters?: Record<string, any>;
}

export interface ScrapingResult {
  taskId: string;
  success: boolean;
  data: any[];
  metadata: {
    totalPages: number;
    totalRecords: number;
    processingTime: number;
    errors: string[];
    qualityScore: number;
  };
  outputUrl?: string;
  outputPath?: string;
}

export interface ScrapingStatus {
  taskId: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: {
    currentPage: number;
    totalPages: number;
    recordsExtracted: number;
    currentUrl?: string;
  };
  startTime: Date;
  estimatedTimeRemaining?: number;
  error?: string;
}

export interface PreviewResult {
  success: boolean;
  sampleData: any[];
  extractedFields: string[];
  qualityAssessment: {
    completeness: number;
    consistency: number;
    accuracy: number;
    overallScore: number;
  };
  recommendedSelectors: string[];
  error?: string;
}

export class ScrapingEngine extends EventEmitter {
  private modelManager: ModelManager;
  private authManager: GoogleAuthManager;
  private browser: Browser | null = null;
  private activeTasks: Map<string, ScrapingStatus> = new Map();
  private contexts: Map<string, BrowserContext> = new Map();

  constructor(modelManager: ModelManager, authManager: GoogleAuthManager) {
    super();
    this.modelManager = modelManager;
    this.authManager = authManager;
  }

  async startScraping(config: ScrapingConfig): Promise<string> {
    const taskId = config.id || uuidv4();
    
    try {
      // Initialize browser if needed
      await this.initializeBrowser();

      // Validate configuration
      await this.validateConfig(config);

      // Create scraping status
      const status: ScrapingStatus = {
        taskId,
        status: 'pending',
        progress: {
          currentPage: 0,
          totalPages: config.urls.length * (config.maxPages || 1),
          recordsExtracted: 0
        },
        startTime: new Date()
      };

      this.activeTasks.set(taskId, status);
      this.emit('scraping-started', { taskId, config });

      // Start scraping in background
      this.performScraping(taskId, config);

      return taskId;
    } catch (error) {
      console.error('Failed to start scraping:', error);
      throw new Error(`Failed to start scraping: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async stopScraping(taskId: string): Promise<boolean> {
    const status = this.activeTasks.get(taskId);
    
    if (!status) {
      return false;
    }

    if (status.status === 'running') {
      status.status = 'cancelled';
      this.activeTasks.set(taskId, status);
      this.emit('scraping-cancelled', { taskId });
      
      // Clean up context
      const context = this.contexts.get(taskId);
      if (context) {
        await context.close();
        this.contexts.delete(taskId);
      }

      return true;
    }

    return false;
  }

  async previewScraping(config: ScrapingConfig): Promise<PreviewResult> {
    try {
      await this.initializeBrowser();
      await this.validateConfig(config);

      const previewTaskId = 'preview-' + uuidv4();
      const context = await this.browser!.newContext(this.getBrowserOptions());
      this.contexts.set(previewTaskId, context);

      try {
        // Take first URL for preview
        const url = config.urls[0];
        const page = await context.newPage();
        
        await this.configurePage(page);
        await page.goto(url, { waitUntil: 'networkidle' });

        // Get page content
        const html = await page.content();
        
        // Use AI to analyze page and generate selectors
        const analysis = await this.modelManager.analyzeWebPage(html, config.prompt);
        const selectors = config.customSelectors || analysis.recommended_selectors || 
                         await this.modelManager.generateSelectors(html.substring(0, 5000));

        // Extract sample data
        const sampleData = await this.extractSampleData(page, selectors, 50);
        
        // Assess data quality
        const qualityAssessment = this.assessDataQuality(sampleData);

        return {
          success: true,
          sampleData,
          extractedFields: this.extractFieldNames(sampleData),
          qualityAssessment,
          recommendedSelectors: selectors
        };
      } finally {
        await context.close();
        this.contexts.delete(previewTaskId);
      }
    } catch (error) {
      console.error('Preview failed:', error);
      return {
        success: false,
        sampleData: [],
        extractedFields: [],
        qualityAssessment: {
          completeness: 0,
          consistency: 0,
          accuracy: 0,
          overallScore: 0
        },
        recommendedSelectors: [],
        error: error instanceof Error ? error.message : 'Preview failed'
      };
    }
  }

  getScrapingStatus(taskId: string): ScrapingStatus | null {
    return this.activeTasks.get(taskId) || null;
  }

  private async performScraping(taskId: string, config: ScrapingConfig): Promise<void> {
    const status = this.activeTasks.get(taskId)!;
    status.status = 'running';
    this.activeTasks.set(taskId, status);

    const startTime = Date.now();
    const allData: any[] = [];
    const errors: string[] = [];

    try {
      // Create browser context for this task
      const context = await this.browser!.newContext(this.getBrowserOptions());
      this.contexts.set(taskId, context);

      // Generate or use provided selectors
      let selectors = config.customSelectors;
      
      if (!selectors || selectors.length === 0) {
        // Use AI to generate selectors from first page
        const firstPage = await context.newPage();
        await this.configurePage(firstPage);
        await firstPage.goto(config.urls[0], { waitUntil: 'networkidle' });
        
        const html = await firstPage.content();
        selectors = await this.modelManager.generateSelectors(html.substring(0, 5000));
        
        await firstPage.close();
      }

      // Process each URL
      for (const [urlIndex, url] of config.urls.entries()) {
        const currentStatus = this.activeTasks.get(taskId);
        if (currentStatus?.status === 'cancelled') break;

        try {
          status.progress.currentUrl = url;
          this.activeTasks.set(taskId, status);
          this.emit('scraping-progress', { taskId, status });

          const urlData = await this.scrapeUrl(context, url, selectors!, config);
          allData.push(...urlData);

          status.progress.currentPage = urlIndex + 1;
          status.progress.recordsExtracted = allData.length;
          this.activeTasks.set(taskId, status);

          // Add delay between requests
          if (config.delay && urlIndex < config.urls.length - 1) {
            await this.sleep(config.delay);
          }
        } catch (error) {
          const errorMsg = `Failed to scrape ${url}: ${error instanceof Error ? error.message : 'Unknown error'}`;
          errors.push(errorMsg);
          console.error(errorMsg);
        }
      }

      // Export data
      let outputUrl: string | undefined;
      let outputPath: string | undefined;

      if (allData.length > 0) {
        if (config.outputFormat === 'sheets') {
          outputUrl = await this.exportToSheets(taskId, allData, config);
        } else {
          outputPath = await this.exportToFile(taskId, allData, config);
        }
      }

      // Complete the task
      const processingTime = Date.now() - startTime;
      const qualityScore = this.calculateQualityScore(allData, errors);

      const result: ScrapingResult = {
        taskId,
        success: allData.length > 0,
        data: allData,
        metadata: {
          totalPages: status.progress.currentPage,
          totalRecords: allData.length,
          processingTime,
          errors,
          qualityScore
        },
        outputUrl,
        outputPath
      };

      status.status = allData.length > 0 ? 'completed' : 'failed';
      status.error = allData.length === 0 ? 'No data extracted' : undefined;
      this.activeTasks.set(taskId, status);

      this.emit('scraping-completed', { taskId, result });

    } catch (error) {
      status.status = 'failed';
      status.error = error instanceof Error ? error.message : 'Scraping failed';
      this.activeTasks.set(taskId, status);

      this.emit('scraping-failed', { taskId, error: status.error });
    } finally {
      // Clean up context
      const context = this.contexts.get(taskId);
      if (context) {
        await context.close();
        this.contexts.delete(taskId);
      }
    }
  }

  private async initializeBrowser(): Promise<void> {
    if (!this.browser) {
      this.browser = await chromium.launch({
        headless: true,
        args: [
          '--no-sandbox',
          '--disable-setuid-sandbox',
          '--disable-dev-shm-usage',
          '--disable-accelerated-2d-canvas',
          '--disable-gpu',
          '--window-size=1920,1080'
        ]
      });
    }
  }

  private getBrowserOptions(): any {
    return {
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      viewport: { width: 1920, height: 1080 },
      ignoreHTTPSErrors: true,
      javaScriptEnabled: true
    };
  }

  private async configurePage(page: Page): Promise<void> {
    // Block unnecessary resources to improve performance
    await page.route('**/*', (route) => {
      const resourceType = route.request().resourceType();
      if (['image', 'stylesheet', 'font', 'media'].includes(resourceType)) {
        route.abort();
      } else {
        route.continue();
      }
    });

    // Set extra headers
    await page.setExtraHTTPHeaders({
      'Accept-Language': 'en-US,en;q=0.9'
    });
  }

  private async scrapeUrl(context: BrowserContext, url: string, selectors: string[], config: ScrapingConfig): Promise<any[]> {
    const page = await context.newPage();
    
    try {
      await this.configurePage(page);
      await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });

      // Wait for dynamic content
      await page.waitForTimeout(2000);

      // Extract data using selectors
      const data = await page.evaluate((selectors: string[]) => {
        const results: any[] = [];
        
        // Find all container elements (assuming first selector defines containers)
        const containers = document.querySelectorAll(selectors[0] || 'body > *');
        
        containers.forEach((container, index) => {
          const record: any = { _index: index };
          
          selectors.forEach((selector, selectorIndex) => {
            try {
              const elements = container.querySelectorAll(selector);
              if (elements.length > 0) {
                const fieldName = `field_${selectorIndex}`;
                if (elements.length === 1) {
                  record[fieldName] = elements[0].textContent?.trim() || '';
                } else {
                  record[fieldName] = Array.from(elements).map(el => el.textContent?.trim() || '');
                }
              }
            } catch (error) {
              console.warn(`Selector failed: ${selector}`, error);
            }
          });
          
          // Only add record if it has meaningful data
          const hasData = Object.values(record).some((value: any) => 
            value && value !== '' && !String(value).startsWith('_')
          );
          
          if (hasData) {
            results.push(record);
          }
        });
        
        return results;
      }, selectors);

      return data.slice(0, config.maxPages || 100); // Limit results per page
    } finally {
      await page.close();
    }
  }

  private async extractSampleData(page: Page, selectors: string[], maxRecords: number): Promise<any[]> {
    return await page.evaluate(({ selectors, maxRecords }: { selectors: string[], maxRecords: number }) => {
      const results: any[] = [];
      const containers = document.querySelectorAll(selectors[0] || 'body > *');
      
      for (let i = 0; i < Math.min(containers.length, maxRecords); i++) {
        const container = containers[i];
        const record: any = { _index: i };
        
        selectors.forEach((selector, selectorIndex) => {
          try {
            const elements = container.querySelectorAll(selector);
            if (elements.length > 0) {
              const fieldName = `field_${selectorIndex}`;
              record[fieldName] = elements[0].textContent?.trim() || '';
            }
          } catch (error) {
            // Ignore selector errors in preview
          }
        });
        
        const hasData = Object.values(record).some((value: any) => 
          value && value !== '' && !String(value).startsWith('_')
        );
        
        if (hasData) {
          results.push(record);
        }
      }
      
      return results;
    }, { selectors, maxRecords });
  }

  private assessDataQuality(data: any[]): any {
    if (data.length === 0) {
      return { completeness: 0, consistency: 0, accuracy: 0, overallScore: 0 };
    }

    const fields = this.extractFieldNames(data);
    let completeness = 0;
    let consistency = 0;

    // Calculate completeness (% of non-empty fields)
    const totalFields = data.length * fields.length;
    const filledFields = data.reduce((count, record) => {
      return count + fields.filter(field => record[field] && record[field] !== '').length;
    }, 0);
    completeness = totalFields > 0 ? (filledFields / totalFields) * 100 : 0;

    // Calculate consistency (similar data types/formats)
    consistency = fields.length > 0 ? fields.reduce((avg: number, field: string) => {
      const values = data.map((record: any) => record[field]).filter((v: any) => v);
      const types = [...new Set(values.map((v: any) => typeof v))];
      return avg + (types.length === 1 ? 100 : 50);
    }, 0) / fields.length : 0;

    // Accuracy is harder to measure automatically, use heuristics
    const accuracy = Math.min(completeness, consistency);
    
    const overallScore = (completeness + consistency + accuracy) / 3;

    return {
      completeness: Math.round(completeness),
      consistency: Math.round(consistency),
      accuracy: Math.round(accuracy),
      overallScore: Math.round(overallScore)
    };
  }

  private extractFieldNames(data: any[]): string[] {
    if (data.length === 0) return [];
    
    const allFields = new Set<string>();
    data.forEach((record: any) => {
      Object.keys(record).forEach((key: string) => {
        if (!key.startsWith('_')) {
          allFields.add(key);
        }
      });
    });
    
    return Array.from(allFields);
  }

  private async exportToSheets(taskId: string, data: any[], config: ScrapingConfig): Promise<string> {
    if (data.length === 0) {
      throw new Error('No data to export');
    }

    const fields = this.extractFieldNames(data);
    const rows = [fields]; // Header row
    
    // Add data rows
    data.forEach((record: any) => {
      const row = fields.map((field: string) => record[field] || '');
      rows.push(row);
    });

    const title = `Scraped Data - ${new Date().toISOString().split('T')[0]} - ${taskId.substring(0, 8)}`;
    
    // Use enhanced formatted spreadsheet creation
    return await this.authManager.createFormattedSpreadsheet(title, rows, {
      headerFormat: true,
      autoResize: true,
      freezeHeader: true,
      sheetName: 'Scraped Data'
    });
  }

  private async exportToFile(taskId: string, data: any[], config: ScrapingConfig): Promise<string> {
    // File export would be implemented here
    // For now, return a placeholder path
    return `/tmp/scraped-data-${taskId}.${config.outputFormat}`;
  }

  private calculateQualityScore(data: any[], errors: string[]): number {
    if (data.length === 0) return 0;
    
    const errorPenalty = Math.min(errors.length * 10, 50);
    const baseScore = 100 - errorPenalty;
    
    return Math.max(baseScore, 0);
  }

  private async validateConfig(config: ScrapingConfig): Promise<void> {
    if (!config.urls || config.urls.length === 0) {
      throw new Error('At least one URL is required');
    }

    if (!config.prompt || config.prompt.trim() === '') {
      throw new Error('Prompt is required');
    }

    // Validate URLs
    for (const url of config.urls) {
      try {
        new URL(url);
      } catch {
        throw new Error(`Invalid URL: ${url}`);
      }
    }
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  cleanup(): void {
    // Close all active contexts
    this.contexts.forEach(async (context) => {
      try {
        await context.close();
      } catch (error) {
        console.error('Error closing context:', error);
      }
    });
    this.contexts.clear();

    // Close browser
    if (this.browser) {
      this.browser.close();
      this.browser = null;
    }

    // Clear active tasks
    this.activeTasks.clear();
  }
}