# TinyLlama Web Scraping Fine-tuning

This directory contains the complete training pipeline for fine-tuning TinyLlama 1.1B model specifically for web scraping tasks.

## 🎯 Overview

The training system fine-tunes TinyLlama to excel at:
- **CSS Selector Generation** - Creating precise selectors for data extraction
- **Pagination Detection** - Identifying and handling different pagination patterns
- **Filter Strategies** - Understanding form interactions and search filters
- **Error Handling** - Gracefully managing malformed HTML and missing elements

## 📁 File Structure

```
training/
├── train_tinyllama.py          # Main training script with LoRA fine-tuning
├── dataset_preparation.py      # Synthetic dataset generation
├── evaluation.py              # Comprehensive model evaluation
├── requirements.txt           # Training dependencies
├── run_training.sh            # Complete training pipeline
├── configs/
│   └── training_config.json   # Training hyperparameters
├── datasets/                  # Generated training data
├── models/                    # Fine-tuned model outputs
└── evaluation_results/        # Evaluation reports and metrics
```

## 🚀 Quick Start

### 1. Run Complete Pipeline

The easiest way to start training:

```bash
./run_training.sh
```

This will:
- Setup Python environment
- Install dependencies  
- Generate training dataset
- Fine-tune the model
- Evaluate performance
- Deploy to desktop app

### 2. Manual Step-by-Step

If you prefer manual control:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate dataset
python dataset_preparation.py --num-examples 2000

# 3. Train model
python train_tinyllama.py --config configs/training_config.json --convert-onnx

# 4. Evaluate model
python evaluation.py --model-path ./models/tinyllama-webscraping-finetuned \
                    --test-dataset ./datasets/webscraping_dataset_validation.jsonl
```

## 🔧 Configuration

### Training Parameters

Key parameters in `configs/training_config.json`:

```json
{
  "num_epochs": 3,
  "batch_size": 4,
  "learning_rate": 2e-4,
  "lora_rank": 16,
  "max_seq_length": 2048
}
```

### Hardware Optimization

The training script automatically optimizes for your hardware:

- **CUDA GPU**: Full batch size, FP16 training
- **Apple Silicon**: Reduced batch size, MPS acceleration  
- **CPU**: Minimal batch size, increased gradient accumulation

## 📊 Dataset

### Synthetic Data Generation

The `dataset_preparation.py` script creates diverse training examples:

- **E-commerce Products** - Various HTML structures for product pages
- **Job Listings** - Different layouts for job posting sites
- **Pagination Patterns** - Numbered, infinite scroll, load more buttons
- **Filter Interfaces** - Price ranges, category dropdowns, search forms
- **Error Cases** - Missing elements, malformed HTML
- **Edge Cases** - Deeply nested structures, complex selectors

### Dataset Statistics

Default generation creates:
- 2000 synthetic examples
- 80% training, 10% validation, 10% test split
- Multiple task types and domains
- Balanced difficulty levels

## 🎯 Training Approach

### LoRA Fine-tuning

Uses Parameter-Efficient Fine-tuning with LoRA:
- **Rank**: 16 (adjustable)
- **Target Modules**: All attention layers
- **Memory Efficient**: <2GB GPU memory required
- **Fast Training**: 2-4 hours on modern GPU

### Training Strategy

1. **Task-Specific Prompts** - Formatted for web scraping context
2. **Multi-Task Learning** - CSS selectors, pagination, filters
3. **Progressive Difficulty** - From simple to complex examples
4. **Error Resilience** - Training on malformed/incomplete HTML

## 📈 Evaluation Metrics

### Automatic Evaluation

The evaluation script measures:

- **Syntax Accuracy** - Valid CSS selector format
- **Functionality** - Selectors work on HTML
- **Content Relevance** - Extracted data quality
- **Response Quality** - JSON structure, completeness
- **Task-Specific Metrics** - Per domain performance

### Performance Targets

Target metrics for successful training:

| Metric | Target | Description |
|--------|---------|-------------|
| Syntax Accuracy | >90% | Valid CSS selector syntax |
| Functionality | >85% | Selectors work on HTML |
| Content Accuracy | >80% | Relevant data extraction |
| Response Quality | >95% | Well-formed JSON output |

## 🔄 Model Deployment

### Automatic Deployment

The training pipeline automatically:
1. Converts model to ONNX format
2. Copies to desktop app models directory
3. Updates model configuration

### Manual Deployment

```bash
# Copy ONNX model to desktop app
cp -r models/tinyllama-1.1b-onnx/* ../desktop-scraper/models/tinyllama-1.1b-onnx/
```

## 📊 Monitoring & Logging

### Weights & Biases Integration

Training automatically logs to W&B:
- Loss curves and metrics
- Hardware utilization
- Hyperparameter tracking
- Model comparisons

### Local Logging

Structured logs include:
- Training progress
- Evaluation metrics
- Error handling
- Performance statistics

## 🛠️ Troubleshooting

### Common Issues

**Out of Memory**
```bash
# Reduce batch size
./run_training.sh --dataset-size 1000
```

**CUDA Errors**
```bash
# Force CPU training
export CUDA_VISIBLE_DEVICES=""
./run_training.sh
```

**Dataset Generation Fails**
```bash
# Generate smaller dataset
python dataset_preparation.py --num-examples 500
```

### Performance Optimization

**Faster Training**
- Use GPU with >8GB VRAM
- Increase batch size in config
- Use FP16 training (enabled by default)

**Better Quality**
- Increase dataset size
- Train for more epochs
- Adjust LoRA rank

## 🔍 Advanced Usage

### Custom Dataset

Replace synthetic data with real-world examples:

```python
# Create custom dataset in JSONL format
{
  "instruction": "Extract product data from this HTML",
  "input": "<div class='product'>...</div>",
  "output": {"selectors": {"title": [".product-title"]}}
}
```

### Hyperparameter Tuning

Create custom training config:

```json
{
  "learning_rate": 1e-4,
  "lora_rank": 32,
  "num_epochs": 5,
  "batch_size": 8
}
```

### Multi-GPU Training

For distributed training:

```bash
torchrun --nproc_per_node=2 train_tinyllama.py --config configs/training_config.json
```

## 📚 Additional Resources

- [TinyLlama Model Card](https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v1.0)
- [LoRA Paper](https://arxiv.org/abs/2106.09685)
- [PEFT Documentation](https://huggingface.co/docs/peft)
- [Transformers Training Guide](https://huggingface.co/docs/transformers/training)

## 🤝 Contributing

To improve the training pipeline:

1. Add new task types to dataset generation
2. Implement additional evaluation metrics
3. Optimize for new hardware platforms
4. Create domain-specific fine-tuning configs

## 📄 License

This training code is part of the IWSA project and follows the same license terms.