#!/usr/bin/env python3
"""
Local Web Scraper Startup Script
Simple launcher for the privacy-first local web scraping interface
"""

import subprocess
import sys
import os
import time
import webbrowser
from pathlib import Path

def check_requirements():
    """Check if all requirements are met"""
    print("🔍 Checking requirements...")
    
    # Check if we're in the right directory
    if not Path("web_server.py").exists():
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    # Check if virtual environment exists
    if not Path("venv").exists() and not Path(".venv").exists():
        print("⚠️  No virtual environment found. Creating one...")
        subprocess.run([sys.executable, "-m", "venv", "venv"])
        print("✅ Virtual environment created")
    
    # Check if requirements are installed
    try:
        import fastapi
        import uvicorn
        print("✅ Required packages found")
    except ImportError:
        print("📦 Installing required packages...")
        subprocess.run([sys.executable, "-m", "pip", "install", "fastapi", "uvicorn", "websockets"])
        print("✅ Packages installed")

def build_frontend():
    """Build the React frontend if needed"""
    print("🔨 Checking frontend build...")
    
    build_path = Path("desktop-scraper/build")
    if not build_path.exists():
        print("🚀 Building React frontend...")
        os.chdir("desktop-scraper")
        
        # Install npm dependencies if needed
        if not Path("node_modules").exists():
            print("📦 Installing npm dependencies...")
            subprocess.run(["npm", "install"])
        
        # Build the frontend
        subprocess.run(["npm", "run", "build:frontend"])
        os.chdir("..")
        print("✅ Frontend built successfully")
    else:
        print("✅ Frontend build found")

def start_server():
    """Start the local web server"""
    print("\n" + "="*60)
    print("🕷️  STARTING LOCAL WEB SCRAPER")
    print("="*60)
    print("🔒 100% Local Processing - Privacy First")
    print("🤖 AI-Powered with Local Models")
    print("🌐 Web Interface: http://localhost:8000")
    print("="*60)
    
    # Change to project directory
    os.chdir(Path(__file__).parent)
    
    # Start the server
    subprocess.run([sys.executable, "web_server.py"])

def main():
    """Main entry point"""
    try:
        print("🚀 Local Web Scraper Launcher")
        print("Privacy-First Web Scraping with AI\n")
        
        check_requirements()
        build_frontend()
        start_server()
        
    except KeyboardInterrupt:
        print("\n👋 Local Web Scraper stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()