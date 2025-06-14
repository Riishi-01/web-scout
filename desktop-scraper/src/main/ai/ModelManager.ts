import * as ort from 'onnxruntime-node';
import * as path from 'path';
import * as fs from 'fs';
import { EventEmitter } from 'events';
import { MockModelManager } from './MockModelManager';

export interface ModelConfig {
  modelPath: string;
  tokenizer: string;
  maxTokens: number;
  temperature: number;
  topP: number;
}

export interface InferenceOptions {
  maxTokens?: number;
  temperature?: number;
  topP?: number;
  stopTokens?: string[];
}

export interface ModelStatus {
  loaded: boolean;
  loading: boolean;
  error?: string;
  modelInfo?: {
    name: string;
    version: string;
    size: number;
    quantization: string;
  };
  performance?: {
    loadTime: number;
    avgInferenceTime: number;
    memoryUsage: number;
  };
}

export class ModelManager extends EventEmitter {
  private session: ort.InferenceSession | null = null;
  private tokenizer: any = null;
  private config: ModelConfig;
  private status: ModelStatus;
  private performanceMetrics: {
    inferenceTimes: number[];
    loadStartTime?: number;
  };
  private mockManager: MockModelManager | null = null;
  private useMock: boolean = false;

  constructor() {
    super();
    
    this.config = {
      modelPath: this.getModelPath(),
      tokenizer: 'tinyllama-tokenizer',
      maxTokens: 512,
      temperature: 0.7,
      topP: 0.9
    };

    this.status = {
      loaded: false,
      loading: false
    };

    this.performanceMetrics = {
      inferenceTimes: []
    };

    // Check if we should use mock implementation
    this.useMock = !fs.existsSync(this.config.modelPath) || process.env.USE_MOCK_MODEL === 'true';
    
    if (this.useMock) {
      console.log('🤖 Using Mock Model Manager (no model file found or USE_MOCK_MODEL=true)');
      this.mockManager = new MockModelManager();
      
      // Forward events from mock manager
      this.mockManager.on('status-change', (status) => this.emit('status-change', status));
      this.mockManager.on('model-loaded', (status) => this.emit('model-loaded', status));
      this.mockManager.on('error', (error) => this.emit('error', error));
      this.mockManager.on('initialized', () => this.emit('initialized'));
      this.mockManager.on('cleanup', () => this.emit('cleanup'));
    }
  }

  async initialize(): Promise<void> {
    if (this.useMock && this.mockManager) {
      return await this.mockManager.initialize();
    }

    try {
      this.emit('status-change', { ...this.status, loading: true });
      
      // Check if model file exists
      if (!fs.existsSync(this.config.modelPath)) {
        throw new Error(`Model file not found at ${this.config.modelPath}`);
      }

      // Pre-warm ONNX Runtime
      await this.preWarmRuntime();
      
      this.emit('initialized');
    } catch (error) {
      console.error('Model initialization failed:', error);
      this.status.error = error instanceof Error ? error.message : 'Unknown error';
      this.emit('error', error);
    }
  }

  async loadModel(): Promise<boolean> {
    if (this.useMock && this.mockManager) {
      return await this.mockManager.loadModel();
    }

    if (this.status.loaded) {
      return true;
    }

    if (this.status.loading) {
      return false;
    }

    this.status.loading = true;
    this.performanceMetrics.loadStartTime = Date.now();
    this.emit('status-change', this.status);

    try {
      // Configure ONNX Runtime session options for CPU optimization
      const sessionOptions: ort.InferenceSession.SessionOptions = {
        executionProviders: ['cpu'],
        graphOptimizationLevel: 'all',
        executionMode: 'sequential',
        enableCpuMemArena: true,
        enableMemPattern: true,
        interOpNumThreads: 4, // Optimize for quad-core systems
        intraOpNumThreads: 2
      };

      // Load the ONNX model
      this.session = await ort.InferenceSession.create(this.config.modelPath, sessionOptions);
      
      // Load tokenizer (simplified for demo - would use actual tokenizer)
      await this.loadTokenizer();

      // Calculate load time
      const loadTime = Date.now() - (this.performanceMetrics.loadStartTime || 0);

      this.status = {
        loaded: true,
        loading: false,
        modelInfo: {
          name: 'TinyLlama-1.1B-Web-Scraper',
          version: '1.0.0',
          size: this.getModelSize(),
          quantization: 'INT8'
        },
        performance: {
          loadTime,
          avgInferenceTime: 0,
          memoryUsage: process.memoryUsage().heapUsed
        }
      };

      this.emit('model-loaded', this.status);
      this.emit('status-change', this.status);

      return true;
    } catch (error) {
      console.error('Model loading failed:', error);
      this.status = {
        loaded: false,
        loading: false,
        error: error instanceof Error ? error.message : 'Model loading failed'
      };
      
      this.emit('error', error);
      this.emit('status-change', this.status);
      
      return false;
    }
  }

  async runInference(prompt: string, options: InferenceOptions = {}): Promise<string> {
    if (this.useMock && this.mockManager) {
      return await this.mockManager.runInference(prompt, options);
    }

    if (!this.status.loaded || !this.session) {
      throw new Error('Model not loaded. Call loadModel() first.');
    }

    const startTime = Date.now();

    try {
      // Prepare inference options
      const inferenceOptions = {
        maxTokens: options.maxTokens || this.config.maxTokens,
        temperature: options.temperature || this.config.temperature,
        topP: options.topP || this.config.topP,
        stopTokens: options.stopTokens || ['</s>', '<|endoftext|>']
      };

      // Tokenize input (simplified implementation)
      const inputTokens = await this.tokenizePrompt(prompt);
      
      // Prepare input tensor
      const bigIntTokens = inputTokens.map(token => BigInt(token));
      const inputIds = new ort.Tensor('int64', new BigInt64Array(bigIntTokens), [1, inputTokens.length]);
      
      // Run inference
      const outputs = await this.session.run({ input_ids: inputIds });
      
      // Decode output (simplified implementation)
      const result = await this.decodeOutput(outputs, inferenceOptions);

      // Update performance metrics
      const inferenceTime = Date.now() - startTime;
      this.updatePerformanceMetrics(inferenceTime);

      return result;
    } catch (error) {
      console.error('Inference failed:', error);
      throw new Error(`Inference failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async generateSelectors(htmlSnippet: string): Promise<string[]> {
    if (this.useMock && this.mockManager) {
      return await this.mockManager.generateSelectors(htmlSnippet);
    }

    const prompt = this.buildSelectorPrompt(htmlSnippet);
    
    try {
      const response = await this.runInference(prompt, {
        maxTokens: 256,
        temperature: 0.3, // Lower temperature for more deterministic selectors
        topP: 0.8
      });

      return this.parseSelectorsFromResponse(response);
    } catch (error) {
      console.error('Selector generation failed:', error);
      return [];
    }
  }

  async analyzeWebPage(html: string, intent: string): Promise<any> {
    if (this.useMock && this.mockManager) {
      return await this.mockManager.analyzeWebPage(html, intent);
    }

    const prompt = this.buildAnalysisPrompt(html, intent);
    
    try {
      const response = await this.runInference(prompt, {
        maxTokens: 512,
        temperature: 0.5
      });

      return this.parseAnalysisResponse(response);
    } catch (error) {
      console.error('Web page analysis failed:', error);
      return { error: 'Analysis failed' };
    }
  }

  getStatus(): ModelStatus {
    if (this.useMock && this.mockManager) {
      return this.mockManager.getStatus();
    }
    return { ...this.status };
  }

  cleanup(): void {
    if (this.useMock && this.mockManager) {
      return this.mockManager.cleanup();
    }

    if (this.session) {
      // ONNX Runtime sessions are automatically cleaned up
      this.session = null;
    }
    this.status.loaded = false;
    this.emit('cleanup');
  }

  private getModelPath(): string {
    // In production, model would be bundled with the app
    const modelFileName = 'tinyllama-web-scraper-quantized.onnx';
    return path.join(process.cwd(), 'models', modelFileName);
  }

  private getModelSize(): number {
    try {
      const stats = fs.statSync(this.config.modelPath);
      return stats.size;
    } catch {
      return 0;
    }
  }

  private async preWarmRuntime(): Promise<void> {
    // Pre-warm ONNX Runtime with a dummy session
    try {
      // Create a minimal tensor for warming up
      const dummyTensor = new ort.Tensor('float32', new Float32Array([1]), [1]);
      // This helps initialize internal ONNX Runtime structures
    } catch (error) {
      console.warn('Runtime pre-warming failed:', error);
    }
  }

  private async loadTokenizer(): Promise<void> {
    // Simplified tokenizer implementation
    // In production, would use actual TinyLlama tokenizer
    this.tokenizer = {
      encode: (text: string): number[] => {
        // Basic word-level tokenization for demo
        const words = text.toLowerCase().split(/\s+/);
        return words.map(word => this.getTokenId(word));
      },
      decode: (tokens: number[]): string => {
        // Basic detokenization for demo
        return tokens.map(id => this.getTokenText(id)).join(' ');
      }
    };
  }

  private getTokenId(token: string): number {
    // Simplified token mapping - would use actual tokenizer vocabulary
    return token.charCodeAt(0) % 32000; // TinyLlama vocab size approximation
  }

  private getTokenText(id: number): string {
    // Simplified token mapping - would use actual tokenizer vocabulary
    return String.fromCharCode(id % 128);
  }

  private async tokenizePrompt(prompt: string): Promise<number[]> {
    if (!this.tokenizer) {
      throw new Error('Tokenizer not loaded');
    }

    const template = `<s>[INST] You are a web scraping expert. ${prompt} [/INST]`;
    return this.tokenizer.encode(template);
  }

  private async decodeOutput(outputs: any, options: InferenceOptions): Promise<string> {
    // Simplified output decoding
    // In production, would implement proper autoregressive generation
    if (!this.tokenizer) {
      throw new Error('Tokenizer not loaded');
    }

    // Extract logits from output
    const logits = outputs.logits || outputs.output;
    if (!logits) {
      throw new Error('No valid output from model');
    }

    // Simple greedy decoding (would implement proper sampling in production)
    const outputTokens = Array.from(logits.data).slice(0, options.maxTokens || 100);
    return this.tokenizer.decode(outputTokens);
  }

  private buildSelectorPrompt(htmlSnippet: string): string {
    return `Given this HTML snippet, generate CSS selectors to extract the main content:

HTML:
${htmlSnippet.substring(0, 2000)}

Generate 3-5 CSS selectors that would extract the most important data from this structure. Format as a JSON array of strings.`;
  }

  private buildAnalysisPrompt(html: string, intent: string): string {
    return `Analyze this webpage HTML for scraping purposes:

Intent: ${intent}
HTML Preview: ${html.substring(0, 1500)}

Provide analysis in JSON format with:
1. content_type: What type of content this appears to be
2. data_patterns: Key data patterns found
3. recommended_selectors: CSS selectors for main content
4. pagination_info: Any pagination elements detected
5. anti_bot_measures: Any anti-bot measures detected`;
  }

  private parseSelectorsFromResponse(response: string): string[] {
    try {
      // Try to extract JSON array from response
      const jsonMatch = response.match(/\[.*?\]/s);
      if (jsonMatch) {
        return JSON.parse(jsonMatch[0]);
      }
      
      // Fallback: extract CSS selectors with simple patterns
      const selectorPattern = /([.#]?[\w-]+(?:\[[\w="'-]+\])?(?:\s*[>+~]\s*[\w.-]+)*)/g;
      const matches = response.match(selectorPattern) || [];
      return matches.slice(0, 5); // Limit to 5 selectors
    } catch {
      return [];
    }
  }

  private parseAnalysisResponse(response: string): any {
    try {
      // Try to extract JSON from response
      const jsonMatch = response.match(/\{.*\}/s);
      if (jsonMatch) {
        return JSON.parse(jsonMatch[0]);
      }
    } catch {
      // Fallback to structured parsing
    }

    return {
      content_type: 'unknown',
      data_patterns: [],
      recommended_selectors: [],
      pagination_info: null,
      anti_bot_measures: []
    };
  }

  private updatePerformanceMetrics(inferenceTime: number): void {
    this.performanceMetrics.inferenceTimes.push(inferenceTime);
    
    // Keep only last 100 measurements
    if (this.performanceMetrics.inferenceTimes.length > 100) {
      this.performanceMetrics.inferenceTimes.shift();
    }

    // Update average inference time
    const avgTime = this.performanceMetrics.inferenceTimes.reduce((a, b) => a + b, 0) / 
                   this.performanceMetrics.inferenceTimes.length;

    if (this.status.performance) {
      this.status.performance.avgInferenceTime = avgTime;
      this.status.performance.memoryUsage = process.memoryUsage().heapUsed;
    }
  }
}