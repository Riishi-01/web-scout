import { EventEmitter } from 'events';
import { ModelStatus, InferenceOptions } from './ModelManager';

/**
 * Mock Model Manager for development and testing
 * Provides realistic responses without requiring actual model files
 */
export class MockModelManager extends EventEmitter {
  private status: ModelStatus;
  private mockDelay: number = 1000; // Simulate model inference time

  constructor() {
    super();
    
    this.status = {
      loaded: false,
      loading: false,
      modelInfo: {
        name: 'Mock-TinyLlama-1.1B-Web-Scraper',
        version: '1.0.0-mock',
        size: 1100000000, // ~1.1GB
        quantization: 'INT8'
      },
      performance: {
        loadTime: 0,
        avgInferenceTime: 850,
        memoryUsage: 0
      }
    };
  }

  async initialize(): Promise<void> {
    console.log('🤖 Mock Model Manager: Initializing...');
    this.emit('status-change', { ...this.status, loading: true });
    
    // Simulate initialization delay
    await this.delay(500);
    
    this.emit('initialized');
    console.log('✅ Mock Model Manager: Initialized successfully');
  }

  async loadModel(): Promise<boolean> {
    if (this.status.loaded) {
      console.log('🤖 Mock Model: Already loaded');
      return true;
    }

    if (this.status.loading) {
      console.log('🤖 Mock Model: Already loading');
      return false;
    }

    console.log('🤖 Mock Model: Loading model...');
    this.status.loading = true;
    this.emit('status-change', this.status);

    const loadStartTime = Date.now();

    try {
      // Simulate model loading time
      await this.delay(2000);

      const loadTime = Date.now() - loadStartTime;

      this.status = {
        loaded: true,
        loading: false,
        modelInfo: {
          name: 'Mock-TinyLlama-1.1B-Web-Scraper',
          version: '1.0.0-mock',
          size: 1100000000,
          quantization: 'INT8'
        },
        performance: {
          loadTime,
          avgInferenceTime: 850,
          memoryUsage: process.memoryUsage().heapUsed
        }
      };

      this.emit('model-loaded', this.status);
      this.emit('status-change', this.status);
      
      console.log('✅ Mock Model: Loaded successfully');
      return true;
    } catch (error) {
      console.error('❌ Mock Model: Loading failed:', error);
      this.status = {
        loaded: false,
        loading: false,
        error: 'Mock model loading failed'
      };
      
      this.emit('error', error);
      this.emit('status-change', this.status);
      
      return false;
    }
  }

  async runInference(prompt: string, options: InferenceOptions = {}): Promise<string> {
    if (!this.status.loaded) {
      throw new Error('Mock model not loaded. Call loadModel() first.');
    }

    console.log('🤖 Mock Model: Running inference for prompt:', prompt.substring(0, 100) + '...');

    // Simulate inference time
    await this.delay(this.mockDelay);

    // Generate mock responses based on prompt content
    return this.generateMockResponse(prompt, options);
  }

  async generateSelectors(htmlSnippet: string): Promise<string[]> {
    console.log('🤖 Mock Model: Generating CSS selectors...');
    await this.delay(800);

    // Analyze the HTML snippet to provide realistic selectors
    const selectors = this.analyzeMockHTML(htmlSnippet);
    
    console.log('✅ Mock Model: Generated selectors:', selectors);
    return selectors;
  }

  async analyzeWebPage(html: string, intent: string): Promise<any> {
    console.log('🤖 Mock Model: Analyzing webpage with intent:', intent);
    await this.delay(1200);

    const analysis = this.generateMockAnalysis(html, intent);
    
    console.log('✅ Mock Model: Analysis complete');
    return analysis;
  }

  getStatus(): ModelStatus {
    return { ...this.status };
  }

  cleanup(): void {
    console.log('🤖 Mock Model: Cleaning up...');
    this.status.loaded = false;
    this.emit('cleanup');
  }

  // Mock response generation methods
  private generateMockResponse(prompt: string, options: InferenceOptions = {}): string {
    const lowerPrompt = prompt.toLowerCase();

    // Web scraping related responses
    if (lowerPrompt.includes('css selector') || lowerPrompt.includes('extract')) {
      return this.generateSelectorResponse();
    }

    if (lowerPrompt.includes('analyze') && lowerPrompt.includes('html')) {
      return this.generateAnalysisResponse();
    }

    if (lowerPrompt.includes('scrape') || lowerPrompt.includes('data')) {
      return this.generateScrapingAdvice();
    }

    // Default AI assistant response
    return this.generateGenericResponse(prompt);
  }

  private generateSelectorResponse(): string {
    const selectors = [
      'article.post',
      '.content-main h1',
      '.product-price',
      'div[data-testid="product-info"]',
      'table.data-table tbody tr'
    ];

    return `Based on the HTML structure, I recommend these CSS selectors:

${selectors.map((sel, i) => `${i + 1}. \`${sel}\``).join('\n')}

These selectors target the main content areas while avoiding navigation and footer elements. Always test selectors on multiple pages to ensure consistency.`;
  }

  private generateAnalysisResponse(): string {
    return `{
  "content_type": "e-commerce_product_page",
  "data_patterns": [
    "Product listings with structured data",
    "Price information in specific containers",
    "User reviews and ratings",
    "Product specifications in tables"
  ],
  "recommended_selectors": [
    ".product-title",
    ".price-current",
    ".rating-stars",
    ".product-description"
  ],
  "pagination_info": {
    "type": "numbered",
    "selector": ".pagination a",
    "next_button": ".pagination .next"
  },
  "anti_bot_measures": [
    "Rate limiting detected",
    "JavaScript-rendered content",
    "CAPTCHA on form submission"
  ]
}`;
  }

  private generateScrapingAdvice(): string {
    return `Here are some web scraping best practices:

1. **Respect robots.txt** - Always check the site's robots.txt file
2. **Rate limiting** - Add delays between requests (1-2 seconds minimum)
3. **User agents** - Use realistic browser user agent strings
4. **Error handling** - Implement retry logic for failed requests
5. **Data validation** - Always validate extracted data before saving

For dynamic content, consider using headless browsers like Puppeteer or Playwright.`;
  }

  private generateGenericResponse(prompt: string): string {
    return `I understand you're asking about: "${prompt.substring(0, 100)}..."

As a web scraping AI assistant, I can help you with:
- Generating CSS selectors for data extraction
- Analyzing webpage structures
- Providing scraping strategies
- Optimizing scraping performance
- Handling dynamic content

Would you like me to analyze a specific webpage or help with selector generation?`;
  }

  private analyzeMockHTML(htmlSnippet: string): string[] {
    const selectors: string[] = [];

    // Look for common patterns and generate appropriate selectors
    if (htmlSnippet.includes('class=')) {
      const classMatches = htmlSnippet.match(/class=["']([^"']+)["']/g);
      if (classMatches) {
        classMatches.slice(0, 3).forEach(match => {
          const className = match.match(/class=["']([^"']+)["']/)?.[1];
          if (className) {
            selectors.push(`.${className.split(' ')[0]}`);
          }
        });
      }
    }

    if (htmlSnippet.includes('id=')) {
      const idMatches = htmlSnippet.match(/id=["']([^"']+)["']/g);
      if (idMatches) {
        idMatches.slice(0, 2).forEach(match => {
          const idName = match.match(/id=["']([^"']+)["']/)?.[1];
          if (idName) {
            selectors.push(`#${idName}`);
          }
        });
      }
    }

    // Add some generic selectors based on HTML structure
    if (htmlSnippet.includes('<h1')) selectors.push('h1');
    if (htmlSnippet.includes('<article')) selectors.push('article');
    if (htmlSnippet.includes('<table')) selectors.push('table tbody tr');
    if (htmlSnippet.includes('data-')) {
      const dataAttr = htmlSnippet.match(/data-[\w-]+/)?.[0];
      if (dataAttr) selectors.push(`[${dataAttr}]`);
    }

    // Fallback selectors if none found
    if (selectors.length === 0) {
      return [
        '.content',
        'main article',
        '.post-content',
        'div.container',
        'section.main'
      ];
    }

    return selectors.slice(0, 5); // Limit to 5 selectors
  }

  private generateMockAnalysis(html: string, intent: string): any {
    const contentTypes = ['blog_post', 'e-commerce', 'news_article', 'forum_post', 'product_catalog'];
    const contentType = contentTypes[Math.floor(Math.random() * contentTypes.length)];

    return {
      content_type: contentType,
      data_patterns: [
        "Structured content with clear hierarchy",
        "Consistent CSS class naming",
        "Semantic HTML elements used",
        "Data attributes for dynamic content"
      ],
      recommended_selectors: this.analyzeMockHTML(html),
      pagination_info: html.includes('pagination') ? {
        type: "numbered",
        selector: ".pagination a",
        next_button: ".pagination .next"
      } : null,
      anti_bot_measures: [
        "JavaScript-rendered content detected",
        "Rate limiting likely in place"
      ],
      confidence_score: 0.85,
      estimated_data_points: Math.floor(Math.random() * 500) + 50,
      intent_analysis: {
        user_intent: intent,
        feasibility: "high",
        recommended_approach: "CSS selector-based extraction with fallback to XPath"
      }
    };
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}