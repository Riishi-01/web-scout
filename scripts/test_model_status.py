#!/usr/bin/env python3
"""
Test TinyLlama Model Status
Checks if the model is properly loaded and working
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

async def test_model_status():
    """Test the current model status and provide diagnostics"""
    
    print("🔍 TinyLlama Model Status Check")
    print("=" * 50)
    
    try:
        from iwsa.config import Settings
        from iwsa.llm.providers import TinyLlamaProvider
        from iwsa.llm.hub import LLMHub
        
        # Initialize settings
        settings = Settings()
        print(f"📁 Model path configured: {settings.llm.tinyllama_model_path}")
        print(f"🧵 Threads configured: {settings.llm.tinyllama_threads}")
        print(f"💾 Memory limit: {settings.llm.tinyllama_max_memory}")
        
        # Test TinyLlama provider directly
        print("\n1️⃣ Testing TinyLlama Provider...")
        provider = TinyLlamaProvider(settings)
        
        if provider.is_available:
            print("✅ TinyLlama provider is available")
            print(f"   Model path: {provider.model_path}")
            print(f"   Threads: {provider.inference_threads}")
            print(f"   Session loaded: {provider.session is not None}")
        else:
            print("❌ TinyLlama provider is NOT available")
            print("   Reason: Model file not found or failed to load")
            print("   💡 Run: python scripts/setup_tinyllama.py")
        
        # Test LLM Hub
        print("\n2️⃣ Testing LLM Hub...")
        hub = LLMHub(settings)
        
        # Get provider status
        status = hub.get_provider_status()
        print("📊 Provider Status:")
        for provider_name, info in status.items():
            available = "✅" if info["available"] else "❌"
            priority = info.get("priority", -1)
            cb_state = info.get("circuit_breaker_state", "UNKNOWN")
            print(f"   {available} {provider_name.upper():<12} Priority: {priority:2d}  CB: {cb_state}")
        
        # Test strategy generation
        print("\n3️⃣ Testing Strategy Generation...")
        
        test_html = """
        <div class="products">
            <div class="product-card">
                <h3 class="product-title">Test Product</h3>
                <span class="price">$99.99</span>
                <p class="description">Product description</p>
            </div>
        </div>
        """
        
        strategy = await hub.generate_scraping_strategy(
            html_content=test_html,
            url="https://example.com/products",
            user_intent="Extract product information",
            extraction_fields=["title", "price", "description"]
        )
        
        if strategy.success:
            print("✅ Strategy generation successful!")
            print(f"   Provider used: {strategy.provider_used.upper()}")
            print(f"   Response time: {strategy.response_time:.2f}s")
            print(f"   Cost: ${strategy.cost:.4f}")
            print(f"   Confidence: {strategy.confidence_score:.2f}")
            print(f"   Selectors found: {len(strategy.selectors)}")
        else:
            print("❌ Strategy generation failed")
            print(f"   Reason: {strategy.reasoning}")
        
        # Health check
        print("\n4️⃣ Running Health Check...")
        health = await hub.health_check()
        
        print(f"🏥 Overall Health: {health['overall_health'].upper()}")
        print(f"🎯 Primary Provider: {health.get('primary_provider', 'None').upper()}")
        
        healthy_count = 0
        for provider, health_info in health["providers"].items():
            status_icon = {
                "healthy": "✅", 
                "degraded": "⚠️", 
                "unavailable": "❌", 
                "timeout": "⏱️", 
                "error": "💥"
            }.get(health_info["status"], "❓")
            
            print(f"   {status_icon} {provider.upper()}: {health_info['status']}")
            
            if "response_time" in health_info:
                print(f"      Response time: {health_info['response_time']:.2f}s")
            
            if health_info.get("error"):
                print(f"      Error: {health_info['error']}")
            
            if health_info["status"] == "healthy":
                healthy_count += 1
        
        # Summary and recommendations
        print("\n📋 SUMMARY")
        print("-" * 30)
        
        if provider.is_available:
            print("🎉 TinyLlama is working! Local inference available.")
            print(f"💰 Cost per request: $0.00")
            print(f"⚡ Expected response time: 0.5-2s")
        else:
            print("⚠️  TinyLlama not available - using cloud fallbacks")
            print(f"💰 Cost per request: $0.01-0.05 (cloud)")
            print(f"⚡ Expected response time: 2-10s")
        
        print(f"🔧 Healthy providers: {healthy_count}/{len(health['providers'])}")
        print(f"🌐 System operational: {'Yes' if healthy_count > 0 else 'No'}")
        
        # Recommendations
        print("\n💡 RECOMMENDATIONS")
        print("-" * 30)
        
        if not provider.is_available:
            print("🔧 To enable local TinyLlama:")
            print("   1. Run: python scripts/setup_tinyllama.py")
            print("   2. Or manually download ONNX model to models/tinyllama-1.1b-onnx/")
            print("   3. Ensure ONNX Runtime is installed: pip install onnxruntime")
        
        if healthy_count == 1 and provider.is_available:
            print("🌩️  Consider adding cloud provider API keys for redundancy:")
            print("   - Set OPENAI_API_KEY for high accuracy")
            print("   - Set CLAUDE_API_KEY for alternative processing")
        
        if healthy_count == 0:
            print("🚨 CRITICAL: No providers available!")
            print("   - Check internet connection for cloud providers")
            print("   - Verify API keys are correct")
            print("   - Set up local TinyLlama model")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def check_file_system():
    """Check file system setup"""
    print("\n📁 File System Check")
    print("-" * 30)
    
    project_root = Path(__file__).parent.parent
    
    # Check directories
    dirs_to_check = [
        project_root / "models",
        project_root / "models" / "tinyllama-1.1b-onnx",
        project_root / "scripts",
        project_root / "examples"
    ]
    
    for dir_path in dirs_to_check:
        if dir_path.exists():
            print(f"✅ {dir_path} exists")
            if dir_path.name == "tinyllama-1.1b-onnx":
                files = list(dir_path.iterdir())
                if files:
                    print(f"   📋 Files: {[f.name for f in files]}")
                else:
                    print("   📋 Directory is empty")
        else:
            print(f"❌ {dir_path} missing")
    
    # Check .env file
    env_file = project_root / ".env"
    if env_file.exists():
        print(f"✅ {env_file} exists")
    else:
        print(f"⚠️  {env_file} missing - using defaults")

if __name__ == "__main__":
    # Check file system first
    check_file_system()
    
    # Run async test
    success = asyncio.run(test_model_status())
    
    if success:
        print("\n🎯 Model status check completed successfully!")
    else:
        print("\n💥 Model status check failed!")
        sys.exit(1)