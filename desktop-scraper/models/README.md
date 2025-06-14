# Model Files

This directory will contain the TinyLlama model files for offline inference.

## Model Requirements

- TinyLlama 1.1B parameter model
- ONNX format for cross-platform compatibility
- INT8 quantization for reduced memory usage
- Target size: <500MB

## Model Location

In production, place the following files here:
- `tinyllama-web-scraper-quantized.onnx` - Main model file
- `tokenizer.json` - Tokenizer configuration
- `config.json` - Model configuration

For development, the system will use mock inference.