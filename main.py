#!/usr/bin/env python3
"""
Main entry point for the Intelligent Web Scraping Agent
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from iwsa.core.engine import ScrapingEngine
from iwsa.config.settings import Settings
from iwsa.utils.logger import setup_logging


async def main():
    """Main application entry point"""
    
    # Setup logging
    logger = setup_logging()
    logger.info("Starting Intelligent Web Scraping Agent v1.0.0")
    
    try:
        # Load configuration
        settings = Settings()
        
        # Get user prompt from environment or command line
        prompt = os.getenv('PROMPT') or (sys.argv[1] if len(sys.argv) > 1 else None)
        
        if not prompt:
            logger.error("No prompt provided. Set PROMPT environment variable or pass as argument")
            print("Usage: python main.py \"Your scraping prompt here\"")
            print("Or set PROMPT environment variable")
            print("\nExample: python main.py \"Scrape product listings from example-store.com\"")
            print("\nFor more options, use: python -m iwsa.cli --help")
            sys.exit(1)
        
        # Initialize scraping engine
        engine = ScrapingEngine(settings)
        
        # Process the scraping request
        logger.info(f"Processing prompt: {prompt[:100]}...")
        print(f"🤖 Processing: {prompt}")
        print("📊 Analyzing website structure...")
        
        result = await engine.process_request(prompt)
        
        if result.success:
            logger.info(f"Scraping completed successfully. Extracted {result.total_records} records")
            print(f"✅ Success! Extracted {result.total_records} records from {result.pages_processed} pages")
            
            if result.export_url:
                print(f"📊 Google Sheets: {result.export_url}")
            
            if result.file_paths:
                print(f"📁 Files created: {', '.join(result.file_paths)}")
            
            print(f"⏱️  Processing time: {result.processing_time:.2f} seconds")
            
            # Display summary statistics
            if result.extraction_result and result.extraction_result.metadata:
                quality_info = result.extraction_result.metadata.get('quality_assessment', {})
                if quality_info:
                    quality_score = quality_info.get('quality_score', 0)
                    print(f"🎯 Data quality score: {quality_score:.2f}")
            
        else:
            logger.error(f"Scraping failed: {result.error}")
            print(f"❌ Scraping failed: {result.error}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        print("\n⏹️  Scraping interrupted by user")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        print(f"💥 Fatal error: {str(e)}")
        
        # Provide helpful error messages
        if "API key" in str(e).lower():
            print("\n💡 Tip: Make sure to set your LLM API key:")
            print("   export OPENAI_API_KEY=your-openai-key")
            print("   export CLAUDE_API_KEY=your-claude-key")
        elif "mongodb" in str(e).lower():
            print("\n💡 Tip: Make sure MongoDB is configured:")
            print("   export MONGODB_URI=mongodb://localhost:27017")
        elif "connection" in str(e).lower():
            print("\n💡 Tip: Check your internet connection and firewall settings")
        
        sys.exit(1)
    
    logger.info("IWSA execution completed")


if __name__ == "__main__":
    asyncio.run(main())