# TinyLlama Model Setup

This directory contains the TinyLlama model files for local inference in the web scraping system.

## 🎯 **Model Purpose**

The TinyLlama 1.1B model provides local AI inference for:
- **HTML analysis** → Scraping strategy generation
- **CSS selector** generation
- **Pagination strategy** detection
- **Filter identification** and interaction logic

## 📋 **Required Files**

For the system to use local TinyLlama inference, place these files in this directory:

### **Core Model Files**
```
models/
├── tinyllama-1.1b-onnx/
│   ├── model.onnx              # Main ONNX model file
│   ├── tokenizer.json          # Tokenizer configuration
│   ├── config.json             # Model configuration
│   └── special_tokens_map.json # Special tokens mapping
```

### **Expected Model Specifications**
- **Model**: TinyLlama 1.1B parameters
- **Format**: ONNX for cross-platform compatibility
- **Quantization**: INT8 (recommended for speed)
- **Size**: ~300-500MB
- **Memory**: <1.5GB RAM usage
- **Performance**: 0.5-2s response time

## 🚀 **Setup Options**

### **Option 1: Download Pre-converted Model (Recommended)**

```bash
# Example download command (adjust URL as needed)
cd models/
wget https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v1.0-ONNX/resolve/main/model.onnx
mkdir -p tinyllama-1.1b-onnx
mv model.onnx tinyllama-1.1b-onnx/
```

### **Option 2: Convert from HuggingFace**

```bash
# Install conversion tools
pip install optimum[onnxruntime] transformers

# Convert TinyLlama to ONNX
python -c "
from optimum.onnxruntime import ORTModelForCausalLM
from transformers import AutoTokenizer

model_id = 'TinyLlama/TinyLlama-1.1B-Chat-v1.0'
ort_model = ORTModelForCausalLM.from_pretrained(model_id, export=True)
tokenizer = AutoTokenizer.from_pretrained(model_id)

ort_model.save_pretrained('./models/tinyllama-1.1b-onnx')
tokenizer.save_pretrained('./models/tinyllama-1.1b-onnx')
"
```

### **Option 3: Use Without Local Model (Cloud Only)**

If you don't want local inference, the system automatically falls back to cloud providers:

```bash
# In .env file, configure cloud providers
PRIMARY_LLM_PROVIDER=openai
OPENAI_API_KEY=your_key_here
```

## ⚙️ **Configuration**

### **Environment Variables**

```bash
# Model location
TINYLLAMA_MODEL_PATH=./models/tinyllama-1.1b-onnx

# Performance tuning
TINYLLAMA_THREADS=4              # Match your CPU cores
TINYLLAMA_MAX_MEMORY=1.5GB       # Available RAM
TINYLLAMA_QUANTIZATION=int8      # Speed vs accuracy
TINYLLAMA_BATCH_SIZE=1           # Concurrent requests

# Routing preferences
PRIMARY_LLM_PROVIDER=tinyllama   # Use local first
LOCAL_COMPLEXITY_THRESHOLD=0.3   # Local vs cloud routing
ENABLE_HYBRID_ROUTING=true       # Enable smart routing
```

### **Performance Optimization**

```bash
# For speed (recommended)
TINYLLAMA_QUANTIZATION=int8
TINYLLAMA_THREADS=8

# For accuracy
TINYLLAMA_QUANTIZATION=fp16
TINYLLAMA_MAX_MEMORY=2GB

# For low-resource systems
TINYLLAMA_THREADS=2
TINYLLAMA_MAX_MEMORY=1GB
```

## 🔍 **Verification**

### **Check Model Loading**

```python
from iwsa.config import Settings
from iwsa.llm.providers import TinyLlamaProvider

settings = Settings()
provider = TinyLlamaProvider(settings)

if provider.is_available:
    print("✅ TinyLlama model loaded successfully")
    print(f"Model path: {provider.model_path}")
    print(f"Threads: {provider.inference_threads}")
else:
    print("❌ TinyLlama model not available")
    print("System will use cloud providers as fallback")
```

### **Test Inference**

```python
from iwsa.llm.hub import LLMHub

hub = LLMHub(settings)
strategy = await hub.generate_scraping_strategy(
    html_content="<div class='item'><h1>Test</h1></div>",
    url="https://example.com",
    user_intent="Extract items"
)

print(f"Provider used: {strategy.provider_used}")
print(f"Response time: {strategy.response_time:.2f}s")
print(f"Cost: ${strategy.cost:.4f}")
```

## 🚨 **Troubleshooting**

### **Model Not Loading**

```bash
# Check file exists
ls -la models/tinyllama-1.1b-onnx/

# Check ONNX Runtime installation
pip install onnxruntime

# Check memory availability
free -h

# Test with verbose logging
LOG_LEVEL=DEBUG python examples/llm_strategy_example.py
```

### **Common Issues**

| Issue | Symptoms | Solution |
|-------|----------|----------|
| Model file missing | "TinyLlama model not found" | Download/convert model files |
| ONNX Runtime error | "ONNX Runtime not available" | `pip install onnxruntime` |
| Memory error | Model loading fails | Increase `TINYLLAMA_MAX_MEMORY` |
| Slow performance | High response times | Increase `TINYLLAMA_THREADS` |
| Path error | Model path not found | Check `TINYLLAMA_MODEL_PATH` |

### **Fallback Behavior**

If TinyLlama fails to load, the system automatically uses:
1. **OpenAI** (if API key provided)
2. **Claude** (if API key provided)  
3. **HuggingFace** (free tier, always available)

## 📊 **Performance Expectations**

### **With Local TinyLlama**
- **Response Time**: 0.5-2s
- **Cost**: $0.00 per request
- **Accuracy**: 70-85% for web scraping tasks
- **Availability**: 100% (offline capable)

### **With Cloud Fallback**
- **Response Time**: 2-10s
- **Cost**: $0.01-0.05 per request
- **Accuracy**: 85-95% for web scraping tasks
- **Availability**: 99%+ (internet dependent)

## 🔒 **Security Notes**

- Model files are local and don't send data to external services
- No API keys required for local inference
- All processing happens on your machine
- Suitable for sensitive/private web scraping tasks

## 📈 **System Requirements**

### **Minimum Requirements**
- **RAM**: 2GB available
- **Storage**: 1GB free space
- **CPU**: 2+ cores
- **OS**: Windows/macOS/Linux

### **Recommended Requirements**
- **RAM**: 4GB+ available
- **Storage**: 2GB+ free space
- **CPU**: 4+ cores with AVX support
- **OS**: 64-bit system

---

**Note**: The system is designed to work seamlessly whether you use local TinyLlama or cloud providers. Local inference provides cost savings and privacy, while cloud providers offer higher accuracy for complex scenarios.