# 🤖 Simplified LLM System for Web Scraping

## Single Purpose, Multiple Providers for Maximum Reliability

This document describes the **simplified LLM architecture** that powers the Intelligent Web Scraping Agent (IWSA) with a **single clear purpose** and **multiple provider redundancy**.

---

## 🎯 **System Purpose**

**One Purpose**: HTML Analysis → Scraping Strategy Generation

The LLM system takes HTML content and user intent, then generates a complete scraping strategy including:
- CSS selectors for data extraction
- Pagination handling logic
- Filter detection and interaction
- Error handling strategies
- Confidence scoring

---

## 🏗️ **Provider Architecture**

### **Fallback Chain for Reliability**

```
1. 🏠 TinyLlama (Local)    → Primary: Fast, offline, $0 cost
2. ☁️ OpenAI (Cloud)       → Fallback 1: High accuracy 
3. ☁️ Claude (Cloud)       → Fallback 2: Alternative cloud
4. ☁️ HuggingFace (Cloud)  → Fallback 3: Free tier safety net
```

### **Automatic Provider Selection**

The system automatically chooses the optimal provider based on:
- **Provider availability** (circuit breaker status)
- **Request complexity** (HTML size, task complexity)
- **Cost optimization** (local first, cloud when needed)
- **Performance requirements** (speed vs accuracy)

---

## 🚀 **Quick Start**

### **1. Installation**

```bash
# Install dependencies
pip install -r requirements.txt

# Copy configuration template
cp .env.example .env

# Download TinyLlama model (optional, for local inference)
mkdir -p models
# Place tinyllama-1.1b-onnx model in models/ directory
```

### **2. Configuration**

Edit `.env` file:

```bash
# For cost-conscious users (local only)
PRIMARY_LLM_PROVIDER=tinyllama
TINYLLAMA_MODEL_PATH=./models/tinyllama-1.1b-onnx

# For maximum reliability (hybrid)
PRIMARY_LLM_PROVIDER=tinyllama
OPENAI_API_KEY=your_openai_key
CLAUDE_API_KEY=your_claude_key
ENABLE_HYBRID_ROUTING=true
```

### **3. Basic Usage**

```python
from iwsa.config import Settings
from iwsa.llm.hub import LLMHub

# Initialize
settings = Settings()
llm_hub = LLMHub(settings)

# Generate scraping strategy
strategy = await llm_hub.generate_scraping_strategy(
    html_content=html,
    url="https://example.com",
    user_intent="Extract job listings",
    extraction_fields=["title", "company", "salary"]
)

# Use the strategy
if strategy.success:
    print(f"Generated {len(strategy.selectors)} selectors")
    print(f"Provider used: {strategy.provider_used}")
    print(f"Cost: ${strategy.cost}")
```

---

## 📊 **Performance Characteristics**

### **Response Times**

| Provider | Typical Response | Use Case |
|----------|------------------|-----------|
| TinyLlama | 0.5-2s | Simple HTML analysis |
| OpenAI | 2-8s | Complex strategy generation |
| Claude | 3-10s | Alternative cloud processing |
| HuggingFace | 5-15s | Fallback processing |

### **Cost Comparison**

| Provider | Cost per Request | Monthly (1000 requests) |
|----------|-----------------|------------------------|
| TinyLlama | $0.00 | $0.00 |
| OpenAI | $0.01-0.05 | $10-50 |
| Claude | $0.008-0.04 | $8-40 |
| HuggingFace | $0.00 | $0.00 |

### **Accuracy Levels**

| Provider | Accuracy | Best For |
|----------|----------|----------|
| TinyLlama | 70-85% | Simple, structured sites |
| OpenAI | 85-95% | Complex sites, edge cases |
| Claude | 80-90% | Natural language understanding |
| HuggingFace | 65-80% | Basic extraction tasks |

---

## ⚙️ **Configuration Options**

### **Provider Priority Settings**

```bash
# Local-first (cost optimized)
PRIMARY_LLM_PROVIDER=tinyllama
LOCAL_COMPLEXITY_THRESHOLD=0.8

# Cloud-first (accuracy optimized)  
PRIMARY_LLM_PROVIDER=openai
LOCAL_COMPLEXITY_THRESHOLD=0.1

# Balanced hybrid
PRIMARY_LLM_PROVIDER=tinyllama
LOCAL_COMPLEXITY_THRESHOLD=0.3
ENABLE_HYBRID_ROUTING=true
```

### **Performance Tuning**

```bash
# TinyLlama optimization
TINYLLAMA_THREADS=8          # Match CPU cores
TINYLLAMA_QUANTIZATION=int8   # Speed vs accuracy
TINYLLAMA_MAX_MEMORY=2GB     # Available RAM

# Routing thresholds
LOCAL_TOKEN_LIMIT=1000       # Token limit for local
LOCAL_COMPLEXITY_THRESHOLD=0.3  # Complexity threshold
```

### **Reliability Settings**

```bash
# Circuit breaker configuration
LLM_RETRY_ATTEMPTS=3
LLM_TIMEOUT=30
LLM_RATE_LIMITING=true

# Provider fallback behavior
FALLBACK_LLM_PROVIDER=openai
```

---

## 🔍 **Monitoring & Health Checks**

### **Provider Status**

```python
# Check provider health
status = llm_hub.get_provider_status()
for provider, info in status.items():
    print(f"{provider}: {info['available']} (CB: {info['circuit_breaker_state']})")
```

### **Health Check**

```python
# Comprehensive health check
health = await llm_hub.health_check()
print(f"Overall Health: {health['overall_health']}")
print(f"Primary Provider: {health['primary_provider']}")
```

### **Performance Metrics**

```python
# Built-in performance tracking
strategy = await llm_hub.generate_scraping_strategy(...)
print(f"Response Time: {strategy.response_time:.2f}s")
print(f"Provider Used: {strategy.provider_used}")
print(f"Cost: ${strategy.cost:.4f}")
print(f"Confidence: {strategy.confidence_score:.2f}")
```

---

## 🛠️ **Advanced Features**

### **Circuit Breakers**

Automatic provider isolation when failures occur:
- **Failure Threshold**: 3 consecutive failures
- **Recovery Timeout**: 5 minutes
- **Graceful Degradation**: Automatic fallback to next provider

### **Intelligent Routing**

Request complexity assessment based on:
- HTML content size
- Task complexity (extraction vs analysis)
- Available provider capacity
- Cost optimization preferences

### **Cost Optimization**

- **Local-first routing** for cost reduction
- **Automatic cost estimation** before requests
- **Budget enforcement** with usage tracking
- **Free tier utilization** when possible

---

## 📋 **Strategy Response Format**

```python
@dataclass
class ScrapingStrategy:
    success: bool                    # Whether strategy was generated
    selectors: List[str]             # CSS selectors for extraction
    extraction_logic: str            # How to extract data
    pagination_strategy: Dict        # Pagination handling
    filters: List[Dict]              # Detected filters
    error_handling: List[str]        # Error recovery strategies
    confidence_score: float          # AI confidence (0.0-1.0)
    reasoning: str                   # AI explanation
    provider_used: str               # Which LLM was used
    response_time: float             # Response time in seconds
    cost: float                      # Cost in USD
```

### **Example Strategy Response**

```json
{
  "success": true,
  "selectors": [
    ".job-card",
    ".job-title",
    ".company-name", 
    ".salary"
  ],
  "extraction_logic": "Extract each job-card container, then get title, company, and salary from child elements",
  "pagination_strategy": {
    "type": "numbered",
    "selectors": [".pagination .next-btn"],
    "logic": "Click next button until disabled"
  },
  "filters": [
    {
      "name": "location",
      "selector": "#location-filter",
      "type": "dropdown",
      "default_value": "all"
    }
  ],
  "error_handling": [
    "Retry with alternative selectors",
    "Skip missing fields",
    "Wait for dynamic content"
  ],
  "confidence_score": 0.87,
  "reasoning": "HTML structure is well-organized with clear class names",
  "provider_used": "tinyllama",
  "response_time": 1.23,
  "cost": 0.0
}
```

---

## 🚨 **Troubleshooting**

### **Common Issues**

**TinyLlama not loading:**
```bash
# Check model path
ls -la ./models/tinyllama-1.1b-onnx

# Check ONNX Runtime installation
pip install onnxruntime

# Check memory requirements
free -h  # Ensure 2GB+ available
```

**Provider failures:**
```bash
# Check API keys
echo $OPENAI_API_KEY | head -c 20

# Check network connectivity
curl -I https://api.openai.com

# Review circuit breaker status
python -c "from iwsa.llm.hub import LLMHub; print(LLMHub().get_provider_status())"
```

**Performance issues:**
```bash
# Monitor memory usage
htop

# Adjust threading
export TINYLLAMA_THREADS=4

# Check rate limiting
export RATE_LIMIT_DELAY=1.0
```

### **Error Codes**

| Error | Meaning | Solution |
|-------|---------|----------|
| `MODEL_NOT_FOUND` | TinyLlama model missing | Download model to correct path |
| `ALL_PROVIDERS_FAILED` | All LLM providers failed | Check API keys and connectivity |
| `STRATEGY_PARSING_FAILED` | AI response invalid | Retry with different provider |
| `CIRCUIT_BREAKER_OPEN` | Provider temporarily disabled | Wait for recovery or use fallback |

---

## 🎯 **Best Practices**

### **For Cost Optimization**

1. **Use local-first configuration**
2. **Set appropriate complexity thresholds** 
3. **Monitor usage and costs**
4. **Use free tier providers when possible**

### **For Maximum Reliability**

1. **Configure multiple providers**
2. **Enable hybrid routing**
3. **Monitor circuit breaker status**
4. **Set appropriate retry limits**

### **For Performance**

1. **Tune TinyLlama threads to CPU cores**
2. **Use appropriate quantization settings**
3. **Monitor response times**
4. **Optimize HTML input size**

---

## 📈 **Scalability**

The simplified LLM system is designed for scalability:

- **Stateless design** for horizontal scaling
- **Provider pooling** for concurrent requests
- **Circuit breakers** prevent cascade failures
- **Async processing** for high throughput
- **Resource monitoring** for auto-scaling

---

## 🤝 **Integration Examples**

### **With Web Scraper**

```python
# Automatic integration in scraping engine
from iwsa.core.engine import ScrapingEngine

engine = ScrapingEngine(settings)
response = await engine.process_request(
    "Extract job listings from example.com"
)
```

### **Standalone Usage**

```python
# Direct strategy generation
from iwsa.llm.strategy_generator import LLMStrategyGenerator

generator = LLMStrategyGenerator(settings)
strategy = await generator.generate_scraping_strategy(
    html_content=html,
    url=url,
    user_intent=intent
)
```

### **Custom Implementation**

```python
# Custom provider priority
from iwsa.llm.providers import TinyLlamaProvider, OpenAIProvider

# Initialize providers manually
local_provider = TinyLlamaProvider(settings)
cloud_provider = OpenAIProvider(settings)

# Custom fallback logic
if local_provider.is_available:
    response = await local_provider.generate_response(request)
else:
    response = await cloud_provider.generate_response(request)
```

---

This simplified LLM system provides **maximum reliability** through provider redundancy while maintaining **cost efficiency** through local-first processing and **ease of use** through a single-purpose interface.