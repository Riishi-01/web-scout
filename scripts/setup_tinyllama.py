#!/usr/bin/env python3
"""
TinyLlama Model Setup Script
Downloads and converts TinyLlama model for local inference
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from typing import Optional

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = ['transformers', 'torch', 'optimum[onnxruntime]']
    missing_packages = []
    
    for package in required_packages:
        try:
            if 'optimum' in package:
                import optimum
            elif package == 'transformers':
                import transformers
            elif package == 'torch':
                import torch
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nInstall with:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    
    return True

def download_and_convert_model(model_output_dir: str, model_id: str = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"):
    """Download and convert TinyLlama model to ONNX format"""
    
    print(f"🤖 Setting up TinyLlama model: {model_id}")
    print(f"📁 Output directory: {model_output_dir}")
    
    try:
        from optimum.onnxruntime import ORTModelForCausalLM
        from transformers import AutoTokenizer
        
        # Create output directory
        os.makedirs(model_output_dir, exist_ok=True)
        
        print("⬇️  Downloading and converting model...")
        print("   This may take several minutes...")
        
        # Convert model to ONNX
        ort_model = ORTModelForCausalLM.from_pretrained(
            model_id, 
            export=True,
            use_cache=False  # Reduce memory usage
        )
        
        # Download tokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        
        print("💾 Saving model and tokenizer...")
        
        # Save to output directory
        ort_model.save_pretrained(model_output_dir)
        tokenizer.save_pretrained(model_output_dir)
        
        print("✅ Model setup completed successfully!")
        print(f"📁 Model saved to: {model_output_dir}")
        
        # List created files
        files = os.listdir(model_output_dir)
        print("📋 Created files:")
        for file in sorted(files):
            file_path = os.path.join(model_output_dir, file)
            size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            print(f"   - {file} ({size:.1f} MB)")
        
        return True
        
    except Exception as e:
        print(f"❌ Model setup failed: {str(e)}")
        return False

def verify_model(model_dir: str):
    """Verify the model can be loaded"""
    print("\n🔍 Verifying model setup...")
    
    try:
        import onnxruntime as ort
        
        # Look for ONNX model file
        model_file = None
        for filename in ['model.onnx', 'model_quantized.onnx']:
            potential_path = os.path.join(model_dir, filename)
            if os.path.exists(potential_path):
                model_file = potential_path
                break
        
        if not model_file:
            print("❌ No ONNX model file found")
            return False
        
        # Try to load the model
        session = ort.InferenceSession(model_file, providers=['CPUExecutionProvider'])
        
        # Get model info
        input_info = session.get_inputs()[0]
        output_info = session.get_outputs()[0]
        
        print("✅ Model verification successful!")
        print(f"   Input: {input_info.name} {input_info.shape}")
        print(f"   Output: {output_info.name} {output_info.shape}")
        
        return True
        
    except Exception as e:
        print(f"❌ Model verification failed: {str(e)}")
        return False

def update_config(model_dir: str):
    """Update configuration to use the new model"""
    env_file = Path("../.env")
    
    if env_file.exists():
        print(f"\n⚙️  Updating configuration in {env_file}")
        
        # Read current config
        with open(env_file, 'r') as f:
            lines = f.readlines()
        
        # Update model path
        updated = False
        for i, line in enumerate(lines):
            if line.startswith('TINYLLAMA_MODEL_PATH='):
                lines[i] = f'TINYLLAMA_MODEL_PATH={model_dir}\n'
                updated = True
                break
        
        if not updated:
            lines.append(f'TINYLLAMA_MODEL_PATH={model_dir}\n')
        
        # Write updated config
        with open(env_file, 'w') as f:
            f.writelines(lines)
        
        print("✅ Configuration updated")
    else:
        print(f"\n⚠️  .env file not found. Set TINYLLAMA_MODEL_PATH={model_dir}")

def main():
    """Main setup function"""
    print("🚀 TinyLlama Model Setup")
    print("=" * 50)
    
    # Check if we're in the right directory
    project_root = Path(__file__).parent.parent
    models_dir = project_root / "models" / "tinyllama-1.1b-onnx"
    
    print(f"📁 Project root: {project_root}")
    print(f"📁 Models directory: {models_dir}")
    
    # Check dependencies
    print("\n1️⃣ Checking dependencies...")
    if not check_dependencies():
        print("❌ Please install required packages first")
        sys.exit(1)
    
    print("✅ All dependencies available")
    
    # Download and convert model
    print("\n2️⃣ Setting up TinyLlama model...")
    if not download_and_convert_model(str(models_dir)):
        print("❌ Model setup failed")
        sys.exit(1)
    
    # Verify model
    print("\n3️⃣ Verifying model...")
    if not verify_model(str(models_dir)):
        print("❌ Model verification failed")
        sys.exit(1)
    
    # Update configuration
    print("\n4️⃣ Updating configuration...")
    update_config(str(models_dir))
    
    print("\n🎉 TinyLlama setup completed successfully!")
    print("\n📋 Next steps:")
    print("   1. Test the model: python examples/llm_strategy_example.py")
    print("   2. Run a scraping task with local inference")
    print("   3. Monitor performance and adjust TINYLLAMA_THREADS as needed")
    
    print(f"\n💰 Cost savings: Local inference = $0.00 per request")
    print(f"⚡ Performance: Expected 0.5-2s response times")
    print(f"🔒 Privacy: All processing happens locally")

if __name__ == "__main__":
    main()