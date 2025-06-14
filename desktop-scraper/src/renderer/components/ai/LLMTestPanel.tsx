import React, { useState, useEffect, useContext } from 'react';
import { ModelContext } from '../../contexts/ModelContext';

interface TestResult {
  prompt: string;
  response: string;
  timestamp: Date;
  duration: number;
}

export const LLMTestPanel: React.FC = () => {
  const modelContext = useContext(ModelContext);
  const [prompt, setPrompt] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [testResults, setTestResults] = useState<TestResult[]>([]);
  const [activeTab, setActiveTab] = useState<'chat' | 'selectors' | 'analysis'>('chat');

  // Sample HTML for testing
  const [htmlInput, setHtmlInput] = useState(`<div class="product-container">
  <h1 class="product-title">Amazing Product</h1>
  <div class="price-section">
    <span class="price">$29.99</span>
    <span class="discount">20% off</span>
  </div>
  <div class="product-description">
    <p>This is an amazing product that will change your life.</p>
  </div>
  <div class="reviews">
    <div class="review">
      <span class="rating">5 stars</span>
      <p class="review-text">Great product!</p>
    </div>
  </div>
</div>`);

  const [analysisIntent, setAnalysisIntent] = useState('Extract product information including name, price, and reviews');

  useEffect(() => {
    // Auto-load model when component mounts
    if (modelContext && !modelContext.status.loaded && !modelContext.status.loading) {
      modelContext.loadModel();
    }
  }, [modelContext]);

  if (!modelContext) {
    return <div>Error: ModelContext not found</div>;
  }
  
  const { status: modelStatus, loadModel, runInference } = modelContext;

  const handleSendPrompt = async () => {
    if (!prompt.trim() || isLoading || !modelStatus.loaded) return;

    setIsLoading(true);
    const startTime = Date.now();

    try {
      const response = await runInference(prompt);
      const duration = Date.now() - startTime;

      const newResult: TestResult = {
        prompt,
        response,
        timestamp: new Date(),
        duration
      };

      setTestResults(prev => [newResult, ...prev]);
      setPrompt('');
    } catch (error) {
      console.error('LLM test failed:', error);
      const newResult: TestResult = {
        prompt,
        response: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date(),
        duration: Date.now() - startTime
      };
      setTestResults(prev => [newResult, ...prev]);
    } finally {
      setIsLoading(false);
    }
  };

  const generateSelectors = async (html: string): Promise<string[]> => {
    const prompt = `Generate CSS selectors for this HTML:

${html}

Return only a JSON array of CSS selectors that would extract the main content.`;
    
    try {
      const response = await runInference(prompt);
      // Try to parse selectors from response
      const selectorMatch = response.match(/\[.*?\]/);
      if (selectorMatch) {
        return JSON.parse(selectorMatch[0]);
      }
      // Fallback: extract CSS-like patterns
      const patterns = response.match(/[.#][\w-]+/g) || [];
      return patterns.slice(0, 5);
    } catch (error) {
      // Mock selectors as fallback
      return ['.content', 'article', '.post-title', '.product-info', 'main section'];
    }
  };

  const handleGenerateSelectors = async () => {
    if (!htmlInput.trim() || isLoading || !modelStatus.loaded) return;

    setIsLoading(true);
    const startTime = Date.now();

    try {
      const selectors = await generateSelectors(htmlInput);
      const duration = Date.now() - startTime;

      const response = `Generated CSS Selectors:\n${selectors.map((sel, i) => `${i + 1}. ${sel}`).join('\n')}`;

      const newResult: TestResult = {
        prompt: `Generate selectors for HTML: ${htmlInput.substring(0, 100)}...`,
        response,
        timestamp: new Date(),
        duration
      };

      setTestResults(prev => [newResult, ...prev]);
    } catch (error) {
      console.error('Selector generation failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const analyzeWebPage = async (html: string, intent: string): Promise<any> => {
    const prompt = `Analyze this webpage HTML for scraping purposes:

Intent: ${intent}
HTML: ${html.substring(0, 1000)}

Provide analysis in JSON format with:
1. content_type: What type of content this appears to be
2. data_patterns: Key data patterns found
3. recommended_selectors: CSS selectors for main content
4. pagination_info: Any pagination elements detected
5. anti_bot_measures: Any anti-bot measures detected`;

    try {
      const response = await runInference(prompt);
      // Try to parse JSON from response
      const jsonMatch = response.match(/\{.*\}/s);
      if (jsonMatch) {
        return JSON.parse(jsonMatch[0]);
      }
      // Fallback analysis
      return {
        content_type: 'web_page',
        data_patterns: ['Structured HTML content', 'CSS classes present'],
        recommended_selectors: ['.content', 'article', 'main'],
        pagination_info: null,
        anti_bot_measures: []
      };
    } catch (error) {
      return { error: 'Analysis failed', message: error instanceof Error ? error.message : 'Unknown error' };
    }
  };

  const handleAnalyzeWebPage = async () => {
    if (!htmlInput.trim() || !analysisIntent.trim() || isLoading || !modelStatus.loaded) return;

    setIsLoading(true);
    const startTime = Date.now();

    try {
      const analysis = await analyzeWebPage(htmlInput, analysisIntent);
      const duration = Date.now() - startTime;

      const response = `Analysis Results:\n${JSON.stringify(analysis, null, 2)}`;

      const newResult: TestResult = {
        prompt: `Analyze webpage with intent: ${analysisIntent}`,
        response,
        timestamp: new Date(),
        duration
      };

      setTestResults(prev => [newResult, ...prev]);
    } catch (error) {
      console.error('Web page analysis failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusColor = () => {
    if (modelStatus.loaded) return '#10b981'; // green
    if (modelStatus.loading) return '#f59e0b'; // yellow
    if (modelStatus.error) return '#ef4444'; // red
    return '#6b7280'; // gray
  };

  const getStatusText = () => {
    if (modelStatus.loaded) return '✅ Model Loaded';
    if (modelStatus.loading) return '⏳ Loading Model...';
    if (modelStatus.error) return `❌ Error: ${modelStatus.error}`;
    return '⚪ Model Not Loaded';
  };

  return (
    <div style={{ 
      padding: '20px', 
      fontFamily: 'system-ui, -apple-system, sans-serif',
      maxWidth: '1200px',
      margin: '0 auto'
    }}>
      <div style={{ marginBottom: '20px' }}>
        <h2 style={{ margin: '0 0 10px 0', color: '#1f2937' }}>🤖 LLM Test Panel</h2>
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: '10px',
          marginBottom: '20px'
        }}>
          <div style={{ 
            padding: '8px 12px', 
            backgroundColor: '#f3f4f6', 
            borderRadius: '6px',
            border: `2px solid ${getStatusColor()}`,
            fontSize: '14px',
            fontWeight: 'medium'
          }}>
            {getStatusText()}
          </div>
          {modelStatus.modelInfo && (
            <div style={{ fontSize: '12px', color: '#6b7280' }}>
              {modelStatus.modelInfo.name} | {modelStatus.modelInfo.quantization} | 
              {modelStatus.performance && ` Avg: ${modelStatus.performance.avgInferenceTime}ms`}
            </div>
          )}
          {!modelStatus.loaded && !modelStatus.loading && (
            <button
              onClick={loadModel}
              style={{
                padding: '8px 16px',
                backgroundColor: '#3b82f6',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '14px'
              }}
            >
              Load Model
            </button>
          )}
        </div>
      </div>

      {/* Tab Navigation */}
      <div style={{ 
        display: 'flex', 
        gap: '4px', 
        marginBottom: '20px',
        borderBottom: '1px solid #e5e7eb'
      }}>
        {[
          { key: 'chat', label: '💬 Chat' },
          { key: 'selectors', label: '🎯 Selectors' },
          { key: 'analysis', label: '🔍 Analysis' }
        ].map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key as any)}
            style={{
              padding: '10px 16px',
              border: 'none',
              backgroundColor: activeTab === tab.key ? '#3b82f6' : 'transparent',
              color: activeTab === tab.key ? 'white' : '#6b7280',
              borderRadius: '6px 6px 0 0',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: 'medium'
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Chat Tab */}
      {activeTab === 'chat' && (
        <div style={{ marginBottom: '30px' }}>
          <div style={{ marginBottom: '15px' }}>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Ask the AI anything about web scraping..."
              style={{
                width: '100%',
                height: '120px',
                padding: '12px',
                border: '1px solid #d1d5db',
                borderRadius: '8px',
                fontSize: '14px',
                fontFamily: 'inherit',
                resize: 'vertical'
              }}
            />
          </div>
          <button
            onClick={handleSendPrompt}
            disabled={!prompt.trim() || isLoading || !modelStatus.loaded}
            style={{
              padding: '10px 20px',
              backgroundColor: modelStatus.loaded && !isLoading ? '#10b981' : '#9ca3af',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: modelStatus.loaded && !isLoading ? 'pointer' : 'not-allowed',
              fontSize: '14px',
              fontWeight: 'medium'
            }}
          >
            {isLoading ? '🤔 Thinking...' : '🚀 Send'}
          </button>
        </div>
      )}

      {/* Selectors Tab */}
      {activeTab === 'selectors' && (
        <div style={{ marginBottom: '30px' }}>
          <div style={{ marginBottom: '15px' }}>
            <label style={{ display: 'block', marginBottom: '5px', fontSize: '14px', fontWeight: 'medium' }}>
              HTML Input:
            </label>
            <textarea
              value={htmlInput}
              onChange={(e) => setHtmlInput(e.target.value)}
              placeholder="Paste HTML code here..."
              style={{
                width: '100%',
                height: '200px',
                padding: '12px',
                border: '1px solid #d1d5db',
                borderRadius: '8px',
                fontSize: '12px',
                fontFamily: 'Monaco, Consolas, monospace',
                resize: 'vertical'
              }}
            />
          </div>
          <button
            onClick={handleGenerateSelectors}
            disabled={!htmlInput.trim() || isLoading || !modelStatus.loaded}
            style={{
              padding: '10px 20px',
              backgroundColor: modelStatus.loaded && !isLoading ? '#8b5cf6' : '#9ca3af',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: modelStatus.loaded && !isLoading ? 'pointer' : 'not-allowed',
              fontSize: '14px',
              fontWeight: 'medium'
            }}
          >
            {isLoading ? '🎯 Generating...' : '🎯 Generate CSS Selectors'}
          </button>
        </div>
      )}

      {/* Analysis Tab */}
      {activeTab === 'analysis' && (
        <div style={{ marginBottom: '30px' }}>
          <div style={{ marginBottom: '15px' }}>
            <label style={{ display: 'block', marginBottom: '5px', fontSize: '14px', fontWeight: 'medium' }}>
              Scraping Intent:
            </label>
            <input
              type="text"
              value={analysisIntent}
              onChange={(e) => setAnalysisIntent(e.target.value)}
              placeholder="What do you want to extract?"
              style={{
                width: '100%',
                padding: '10px 12px',
                border: '1px solid #d1d5db',
                borderRadius: '6px',
                fontSize: '14px',
                marginBottom: '15px'
              }}
            />
            <label style={{ display: 'block', marginBottom: '5px', fontSize: '14px', fontWeight: 'medium' }}>
              HTML Input:
            </label>
            <textarea
              value={htmlInput}
              onChange={(e) => setHtmlInput(e.target.value)}
              placeholder="Paste HTML code here..."
              style={{
                width: '100%',
                height: '200px',
                padding: '12px',
                border: '1px solid #d1d5db',
                borderRadius: '8px',
                fontSize: '12px',
                fontFamily: 'Monaco, Consolas, monospace',
                resize: 'vertical'
              }}
            />
          </div>
          <button
            onClick={handleAnalyzeWebPage}
            disabled={!htmlInput.trim() || !analysisIntent.trim() || isLoading || !modelStatus.loaded}
            style={{
              padding: '10px 20px',
              backgroundColor: modelStatus.loaded && !isLoading ? '#f59e0b' : '#9ca3af',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: modelStatus.loaded && !isLoading ? 'pointer' : 'not-allowed',
              fontSize: '14px',
              fontWeight: 'medium'
            }}
          >
            {isLoading ? '🔍 Analyzing...' : '🔍 Analyze Webpage'}
          </button>
        </div>
      )}

      {/* Results */}
      <div>
        <h3 style={{ margin: '0 0 15px 0', color: '#1f2937' }}>📋 Test Results</h3>
        {testResults.length === 0 ? (
          <div style={{ 
            padding: '40px',
            textAlign: 'center',
            color: '#6b7280',
            backgroundColor: '#f9fafb',
            borderRadius: '8px',
            border: '1px dashed #d1d5db'
          }}>
            No tests run yet. Try asking the AI something!
          </div>
        ) : (
          <div style={{ maxHeight: '600px', overflowY: 'auto' }}>
            {testResults.map((result, index) => (
              <div key={index} style={{ 
                marginBottom: '20px',
                padding: '16px',
                backgroundColor: '#ffffff',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
              }}>
                <div style={{ 
                  fontSize: '12px', 
                  color: '#6b7280',
                  marginBottom: '8px',
                  display: 'flex',
                  justifyContent: 'space-between'
                }}>
                  <span>{result.timestamp.toLocaleString()}</span>
                  <span>{result.duration}ms</span>
                </div>
                <div style={{ marginBottom: '12px' }}>
                  <strong style={{ color: '#1f2937' }}>Prompt:</strong>
                  <div style={{ 
                    marginTop: '4px',
                    padding: '8px',
                    backgroundColor: '#f3f4f6',
                    borderRadius: '4px',
                    fontSize: '14px'
                  }}>
                    {result.prompt}
                  </div>
                </div>
                <div>
                  <strong style={{ color: '#1f2937' }}>Response:</strong>
                  <div style={{ 
                    marginTop: '4px',
                    padding: '12px',
                    backgroundColor: '#f8fafc',
                    borderRadius: '4px',
                    fontSize: '14px',
                    whiteSpace: 'pre-wrap',
                    fontFamily: result.response.includes('{') ? 'Monaco, Consolas, monospace' : 'inherit'
                  }}>
                    {result.response}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};