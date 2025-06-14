#!/usr/bin/env python3
"""
Local Web Server for Privacy-First Web Scraping Interface
Wraps the existing IWSA system with a FastAPI backend for local web UI
"""

import asyncio
import webbrowser
from pathlib import Path
import sys
import os
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from iwsa.core.engine import ScrapingEngine
from iwsa.config.settings import Settings
from iwsa.utils.logger import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Local Web Scraper",
    description="Privacy-first, local web scraping with AI",
    version="1.0.0"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
scraping_engine: Optional[ScrapingEngine] = None
active_websockets: List[WebSocket] = []

# Pydantic models for API
class ScrapingRequest(BaseModel):
    prompt: str
    max_pages: Optional[int] = 10
    output_format: str = "json"
    output_destination: Optional[str] = None

class ScrapingResponse(BaseModel):
    task_id: str
    status: str
    message: str

class TaskStatus(BaseModel):
    task_id: str
    status: str
    progress: Dict[str, Any]
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class ModelStatus(BaseModel):
    loaded: bool
    loading: bool
    model_info: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@app.on_event("startup")
async def startup_event():
    """Initialize the scraping engine on startup"""
    global scraping_engine
    try:
        logger.info("🚀 Starting Local Web Scraper Server...")
        
        # Initialize settings
        settings = Settings()
        
        # Initialize scraping engine
        scraping_engine = ScrapingEngine(settings)
        await scraping_engine.initialize()
        
        logger.info("✅ Local Web Scraper Server ready!")
        logger.info("🌐 Access the interface at: http://localhost:8000")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize scraping engine: {e}")
        scraping_engine = None

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global scraping_engine
    if scraping_engine:
        await scraping_engine.cleanup()
    logger.info("🛑 Local Web Scraper Server stopped")

# WebSocket for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_websockets.append(websocket)
    logger.info(f"WebSocket connected. Active connections: {len(active_websockets)}")
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_websockets.remove(websocket)
        logger.info(f"WebSocket disconnected. Active connections: {len(active_websockets)}")

async def broadcast_update(message: Dict[str, Any]):
    """Broadcast update to all connected WebSockets"""
    if active_websockets:
        message_str = json.dumps(message)
        disconnected = []
        
        for websocket in active_websockets:
            try:
                await websocket.send_text(message_str)
            except:
                disconnected.append(websocket)
        
        # Remove disconnected websockets
        for ws in disconnected:
            active_websockets.remove(ws)

# API Routes

@app.get("/")
async def root():
    """Serve the main React application"""
    return FileResponse('desktop-scraper/build/index.html')

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "engine_ready": scraping_engine is not None,
        "active_connections": len(active_websockets)
    }

@app.get("/api/model/status")
async def get_model_status():
    """Get AI model status"""
    if not scraping_engine:
        raise HTTPException(status_code=503, detail="Scraping engine not initialized")
    
    try:
        # Get model status from the LLM hub
        model_status = await scraping_engine.llm_hub.get_status()
        return ModelStatus(
            loaded=model_status.get("loaded", False),
            loading=model_status.get("loading", False),
            model_info=model_status.get("model_info"),
            error=model_status.get("error")
        )
    except Exception as e:
        logger.error(f"Failed to get model status: {e}")
        return ModelStatus(loaded=False, loading=False, error=str(e))

@app.post("/api/model/load")
async def load_model():
    """Load the AI model"""
    if not scraping_engine:
        raise HTTPException(status_code=503, detail="Scraping engine not initialized")
    
    try:
        await scraping_engine.llm_hub.initialize()
        await broadcast_update({
            "type": "model_loaded",
            "status": "Model loaded successfully"
        })
        return {"status": "success", "message": "Model loaded successfully"}
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load model: {e}")

@app.post("/api/scraping/preview")
async def preview_scraping(request: ScrapingRequest):
    """Preview scraping results"""
    if not scraping_engine:
        raise HTTPException(status_code=503, detail="Scraping engine not initialized")
    
    try:
        # Process the prompt to extract configuration
        config = await scraping_engine.prompt_processor.process_prompt(request.prompt)
        
        # Run reconnaissance on the first URL
        if config.get("urls"):
            recon_result = await scraping_engine.reconnaissance.analyze_site(
                config["urls"][0]
            )
            
            # Generate a preview with limited data
            preview_config = {
                **config,
                "max_pages": 1,
                "max_records": 10,
                "preview_mode": True
            }
            
            result = await scraping_engine.scrape(preview_config)
            
            # Broadcast update
            await broadcast_update({
                "type": "preview_complete",
                "data": result.get("data", [])[:10],
                "quality_score": result.get("quality_score", 0)
            })
            
            return {
                "success": True,
                "data": result.get("data", [])[:10],
                "quality_score": result.get("quality_score", 0),
                "fields": result.get("fields", []),
                "recommendations": recon_result.get("recommendations", [])
            }
        else:
            raise HTTPException(status_code=400, detail="No valid URLs found in prompt")
            
    except Exception as e:
        logger.error(f"Preview failed: {e}")
        raise HTTPException(status_code=500, detail=f"Preview failed: {e}")

@app.post("/api/scraping/start")
async def start_scraping(request: ScrapingRequest) -> ScrapingResponse:
    """Start a scraping task"""
    if not scraping_engine:
        raise HTTPException(status_code=503, detail="Scraping engine not initialized")
    
    try:
        # Process the prompt to extract configuration
        config = await scraping_engine.prompt_processor.process_prompt(request.prompt)
        
        # Update config with request parameters
        config.update({
            "max_pages": request.max_pages,
            "output_format": request.output_format,
            "output_destination": request.output_destination
        })
        
        # Start scraping task (this should be async in the background)
        task_id = await scraping_engine.start_scraping_task(config)
        
        # Broadcast update
        await broadcast_update({
            "type": "scraping_started",
            "task_id": task_id,
            "config": config
        })
        
        return ScrapingResponse(
            task_id=task_id,
            status="started",
            message="Scraping task started successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to start scraping: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start scraping: {e}")

@app.get("/api/scraping/status/{task_id}")
async def get_task_status(task_id: str) -> TaskStatus:
    """Get status of a scraping task"""
    if not scraping_engine:
        raise HTTPException(status_code=503, detail="Scraping engine not initialized")
    
    try:
        status = await scraping_engine.get_task_status(task_id)
        return TaskStatus(
            task_id=task_id,
            status=status.get("status", "unknown"),
            progress=status.get("progress", {}),
            results=status.get("results"),
            error=status.get("error")
        )
    except Exception as e:
        logger.error(f"Failed to get task status: {e}")
        raise HTTPException(status_code=404, detail="Task not found")

@app.delete("/api/scraping/stop/{task_id}")
async def stop_scraping(task_id: str):
    """Stop a scraping task"""
    if not scraping_engine:
        raise HTTPException(status_code=503, detail="Scraping engine not initialized")
    
    try:
        await scraping_engine.stop_task(task_id)
        await broadcast_update({
            "type": "scraping_stopped",
            "task_id": task_id
        })
        return {"status": "success", "message": "Task stopped successfully"}
    except Exception as e:
        logger.error(f"Failed to stop task: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop task: {e}")

@app.get("/api/scraping/history")
async def get_scraping_history():
    """Get scraping task history"""
    if not scraping_engine:
        raise HTTPException(status_code=503, detail="Scraping engine not initialized")
    
    try:
        history = await scraping_engine.get_task_history()
        return {"history": history}
    except Exception as e:
        logger.error(f"Failed to get history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get history: {e}")

@app.post("/api/export/download/{task_id}")
async def download_results(task_id: str, format: str = "json"):
    """Download scraping results in specified format"""
    if not scraping_engine:
        raise HTTPException(status_code=503, detail="Scraping engine not initialized")
    
    try:
        file_path = await scraping_engine.export_results(task_id, format)
        return FileResponse(
            file_path,
            media_type="application/octet-stream",
            filename=f"scraping_results_{task_id}.{format}"
        )
    except Exception as e:
        logger.error(f"Failed to download results: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to download results: {e}")

# Serve React static files
@app.mount("/static", StaticFiles(directory="desktop-scraper/build/static"), name="static")

# Catch-all route for React Router
@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    """Serve React app for all routes (SPA routing)"""
    return FileResponse('desktop-scraper/build/index.html')

def open_browser():
    """Open the default browser to the application"""
    try:
        webbrowser.open("http://localhost:8000")
        logger.info("🌐 Opened browser to http://localhost:8000")
    except Exception as e:
        logger.warning(f"Could not open browser automatically: {e}")

async def main():
    """Main entry point"""
    print("\n" + "="*60)
    print("🕷️  LOCAL WEB SCRAPER - PRIVACY FIRST")
    print("="*60)
    print("🔒 100% Local Processing - No Data Leaves Your Machine")
    print("🤖 AI-Powered with Local TinyLlama Model")
    print("🌐 Web Interface at: http://localhost:8000")
    print("="*60 + "\n")
    
    # Build React app if needed
    if not Path("desktop-scraper/build").exists():
        logger.info("Building React frontend...")
        os.system("cd desktop-scraper && npm run build:frontend")
    
    # Open browser after a short delay
    asyncio.create_task(asyncio.sleep(2))
    asyncio.create_task(asyncio.to_thread(open_browser))
    
    # Start the server
    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info",
        access_log=False
    )
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 Local Web Scraper stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
        sys.exit(1)