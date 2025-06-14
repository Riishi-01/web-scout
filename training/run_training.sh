#!/bin/bash
# TinyLlama Web Scraping Fine-tuning Pipeline
# ===========================================

set -e  # Exit on any error

echo "🚀 Starting TinyLlama Web Scraping Fine-tuning Pipeline"
echo "======================================================="

# Configuration
TRAINING_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$TRAINING_DIR")"
VENV_NAME="tinyllama_training"
PYTHON_VERSION="3.9"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Check if running on Apple Silicon
check_apple_silicon() {
    if [[ $(uname -m) == "arm64" ]]; then
        export PYTORCH_ENABLE_MPS_FALLBACK=1
        info "Detected Apple Silicon - enabled MPS fallback"
        return 0
    fi
    return 1
}

# Check CUDA availability
check_cuda() {
    if command -v nvidia-smi &> /dev/null; then
        log "CUDA detected - will use GPU acceleration"
        return 0
    else
        warning "No CUDA detected - will use CPU training (slower)"
        return 1
    fi
}

# Setup Python environment
setup_environment() {
    log "Setting up Python environment..."
    
    # Check if conda is available
    if command -v conda &> /dev/null; then
        log "Using conda for environment management"
        
        # Create conda environment if it doesn't exist
        if ! conda env list | grep -q "$VENV_NAME"; then
            log "Creating conda environment: $VENV_NAME"
            conda create -n "$VENV_NAME" python="$PYTHON_VERSION" -y
        fi
        
        # Activate environment
        source "$(conda info --base)/etc/profile.d/conda.sh"
        conda activate "$VENV_NAME"
        
    elif command -v python3 &> /dev/null; then
        log "Using venv for environment management"
        
        # Create virtual environment if it doesn't exist
        if [[ ! -d "$TRAINING_DIR/venv" ]]; then
            python3 -m venv "$TRAINING_DIR/venv"
        fi
        
        # Activate virtual environment
        source "$TRAINING_DIR/venv/bin/activate"
        
    else
        error "No suitable Python environment manager found (conda or python3)"
        exit 1
    fi
    
    # Upgrade pip
    pip install --upgrade pip
    
    log "Python environment ready"
}

# Install dependencies
install_dependencies() {
    log "Installing training dependencies..."
    
    # Install PyTorch based on platform
    if check_apple_silicon; then
        log "Installing PyTorch for Apple Silicon..."
        pip install torch torchvision torchaudio
    elif check_cuda; then
        log "Installing PyTorch with CUDA support..."
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
    else
        log "Installing PyTorch CPU version..."
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
    fi
    
    # Install other requirements
    pip install -r "$TRAINING_DIR/requirements.txt"
    
    log "Dependencies installed successfully"
}

# Generate training dataset
generate_dataset() {
    log "Generating training dataset..."
    
    local dataset_path="$TRAINING_DIR/datasets/webscraping_dataset.jsonl"
    
    if [[ -f "$dataset_path" ]]; then
        warning "Dataset already exists at $dataset_path"
        read -p "Do you want to regenerate it? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log "Using existing dataset"
            return 0
        fi
    fi
    
    cd "$TRAINING_DIR"
    python dataset_preparation.py \
        --output "$dataset_path" \
        --num-examples 2000 \
        --seed 42
    
    log "Training dataset generated: $dataset_path"
}

# Run training
run_training() {
    log "Starting model fine-tuning..."
    
    cd "$TRAINING_DIR"
    
    # Set training parameters based on hardware
    local config_file="$TRAINING_DIR/configs/training_config.json"
    local batch_size=4
    local gradient_accumulation=4
    
    # Adjust for available hardware
    if check_cuda; then
        info "Using CUDA - keeping default batch size"
    elif check_apple_silicon; then
        warning "Using Apple Silicon - reducing batch size for memory efficiency"
        batch_size=2
        gradient_accumulation=8
    else
        warning "Using CPU - significantly reducing batch size"
        batch_size=1
        gradient_accumulation=16
    fi
    
    # Create run name with timestamp
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local run_name="tinyllama_webscraping_${timestamp}"
    
    python train_tinyllama.py \
        --config "$config_file" \
        --wandb-run-name "$run_name" \
        --convert-onnx
    
    log "Training completed successfully!"
}

# Run evaluation
run_evaluation() {
    log "Running model evaluation..."
    
    local model_path="$TRAINING_DIR/models/tinyllama-webscraping-finetuned"
    local test_dataset="$TRAINING_DIR/datasets/webscraping_dataset_validation.jsonl"
    local output_dir="$TRAINING_DIR/evaluation_results"
    
    if [[ ! -d "$model_path" ]]; then
        error "Trained model not found at $model_path"
        return 1
    fi
    
    cd "$TRAINING_DIR"
    python evaluation.py \
        --model-path "$model_path" \
        --test-dataset "$test_dataset" \
        --output-dir "$output_dir"
    
    log "Evaluation completed! Results saved to $output_dir"
}

# Copy model to desktop app
deploy_model() {
    log "Deploying model to desktop application..."
    
    local trained_model="$TRAINING_DIR/models/tinyllama-1.1b-onnx"
    local desktop_model_dir="$PROJECT_ROOT/desktop-scraper/models/tinyllama-1.1b-onnx"
    
    if [[ ! -d "$trained_model" ]]; then
        error "ONNX model not found at $trained_model"
        return 1
    fi
    
    # Create desktop model directory
    mkdir -p "$desktop_model_dir"
    
    # Copy model files
    cp -r "$trained_model"/* "$desktop_model_dir/"
    
    log "Model deployed to desktop application: $desktop_model_dir"
}

# Clean up function
cleanup() {
    log "Cleaning up temporary files..."
    
    # Remove any temporary directories or files
    if [[ -d "$TRAINING_DIR/wandb" ]]; then
        warning "Wandb logs found - keeping for analysis"
    fi
    
    log "Cleanup completed"
}

# Main execution
main() {
    log "Starting TinyLlama fine-tuning pipeline"
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-env)
                SKIP_ENV=true
                shift
                ;;
            --skip-dataset)
                SKIP_DATASET=true
                shift
                ;;
            --skip-training)
                SKIP_TRAINING=true
                shift
                ;;
            --skip-evaluation)
                SKIP_EVALUATION=true
                shift
                ;;
            --skip-deployment)
                SKIP_DEPLOYMENT=true
                shift
                ;;
            --dataset-size)
                DATASET_SIZE="$2"
                shift 2
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo "Options:"
                echo "  --skip-env         Skip environment setup"
                echo "  --skip-dataset     Skip dataset generation"
                echo "  --skip-training    Skip model training"
                echo "  --skip-evaluation  Skip model evaluation"
                echo "  --skip-deployment  Skip model deployment"
                echo "  --dataset-size N   Generate N training examples"
                echo "  --help            Show this help"
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Execute pipeline steps
    if [[ "$SKIP_ENV" != true ]]; then
        setup_environment
        install_dependencies
    fi
    
    if [[ "$SKIP_DATASET" != true ]]; then
        generate_dataset
    fi
    
    if [[ "$SKIP_TRAINING" != true ]]; then
        run_training
    fi
    
    if [[ "$SKIP_EVALUATION" != true ]]; then
        run_evaluation
    fi
    
    if [[ "$SKIP_DEPLOYMENT" != true ]]; then
        deploy_model
    fi
    
    cleanup
    
    log "🎉 TinyLlama fine-tuning pipeline completed successfully!"
    info "Next steps:"
    info "1. Check evaluation results in: $TRAINING_DIR/evaluation_results/"
    info "2. Test the deployed model in the desktop application"
    info "3. Monitor model performance in production"
}

# Handle interruption
trap 'error "Pipeline interrupted"; cleanup; exit 1' INT TERM

# Run main function
main "$@"