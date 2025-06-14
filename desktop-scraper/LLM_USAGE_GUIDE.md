# 🤖 LLM Usage Guide

The Local Web Scraper now includes a fully functional AI assistant powered by a mock TinyLlama model. Here's how to use it:

## 🚀 Getting Started

1. **Start the Application**:
   ```bash
   npm run dev
   ```

2. **Access the LLM Test Panel**:
   - Click the "🤖 LLM Test" tab in the sidebar
   - Or use the "🤖 Test LLM" button from the dashboard

## 🔧 Features Available

### 💬 Chat Mode
- **Purpose**: General AI assistant for web scraping questions
- **How to Use**:
  1. Type your question in the text area
  2. Click "🚀 Send" to get AI responses
  3. View conversation history with timestamps and response times

**Example Prompts**:
- "How do I scrape data from a website with JavaScript rendering?"
- "What are the best practices for web scraping?"
- "Explain CSS selectors for data extraction"

### 🎯 Selector Generation Mode
- **Purpose**: Generate CSS selectors from HTML code
- **How to Use**:
  1. Paste your HTML code in the input area
  2. Click "🎯 Generate CSS Selectors"
  3. Get intelligent selector suggestions

**Example HTML** (pre-loaded):
```html
<div class="product-container">
  <h1 class="product-title">Amazing Product</h1>
  <div class="price-section">
    <span class="price">$29.99</span>
    <span class="discount">20% off</span>
  </div>
</div>
```

### 🔍 Web Page Analysis Mode
- **Purpose**: Analyze HTML structure for scraping strategy
- **How to Use**:
  1. Enter your scraping intent (what you want to extract)
  2. Paste the HTML code to analyze
  3. Click "🔍 Analyze Webpage"
  4. Get detailed analysis with:
     - Content type detection
     - Data patterns identification
     - Recommended selectors
     - Pagination detection
     - Anti-bot measures assessment

## 📊 Model Status Indicators

- **✅ Model Loaded** (Green): Ready to process requests
- **⏳ Loading Model...** (Yellow): Model is initializing
- **❌ Error** (Red): Model failed to load
- **⚪ Model Not Loaded** (Gray): Model needs to be loaded

## 🎛️ Performance Metrics

The interface shows real-time performance data:
- **Model Name**: Mock-TinyLlama-1.1B-Web-Scraper
- **Quantization**: INT8 (optimized for speed)
- **Average Response Time**: ~850ms
- **Memory Usage**: Live monitoring

## 🔄 Using Real vs Mock Model

### Current Setup (Mock Model)
- **Advantages**: 
  - No model file required
  - Instant startup
  - Realistic responses for testing
  - Full API compatibility

### Switching to Real Model
To use an actual TinyLlama model:

1. **Download Model**: Place your ONNX model file at:
   ```
   ./models/tinyllama-web-scraper-quantized.onnx
   ```

2. **Environment Variable**: Set to disable mock:
   ```bash
   export USE_MOCK_MODEL=false
   ```

3. **Restart Application**: The system will automatically detect the real model

## 💡 Tips for Best Results

### Chat Mode
- Be specific about web scraping context
- Ask about specific technologies (Puppeteer, Selenium, etc.)
- Request code examples for implementation

### Selector Generation
- Include representative HTML structure
- Test with actual webpage HTML snippets
- Verify selectors in browser dev tools

### Analysis Mode
- Be clear about your extraction goals
- Include the main content area in HTML
- Specify data types you want to extract

## 🛠️ Troubleshooting

### Model Won't Load
1. Check console for error messages
2. Verify model file exists (if using real model)
3. Restart the application

### Slow Responses
- Mock model simulates realistic timing
- Real model performance depends on hardware
- Check system memory usage

### Connection Issues
- Ensure Electron app is running
- Check for JavaScript errors in console
- Verify ModelContext is properly initialized

## 🚀 Next Steps

1. **Test Different Scenarios**: Try various HTML structures and prompts
2. **Compare Results**: Test mock vs real model responses
3. **Integration**: Use LLM results in your scraping workflows
4. **Optimization**: Fine-tune prompts for better results

## 📝 Example Workflow

1. **Start with Analysis**: Understand the webpage structure
2. **Generate Selectors**: Get CSS selectors for target data
3. **Ask Questions**: Get implementation advice via chat
4. **Implement**: Use the suggestions in your scraping code
5. **Iterate**: Refine selectors and strategies

---

The LLM functionality is designed to be your AI assistant for all web scraping tasks. Experiment with different inputs to discover its full capabilities!