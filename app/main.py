from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse, Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
import time
from chat_api import router as chat_router
from config import get_config
from logger import logger

# Initialize configuration
config = get_config()

# Validate environment on startup
try:
    config.validate_required_keys()
except ValueError as e:
    logger.error_logger.error(f"Configuration error: {e}")
    raise

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Self-Hosted Chatbot Engine",
    description="AI-powered chatbot with embeddable widget",
    version="1.0.0"
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS for widget integration
allowed_origins = config.allowed_origins.split(",") if config.allowed_origins != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error_logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

@app.get("/widget/widget.js")
async def serve_widget_js(request: Request):
    """Serve widget JS with proper cache headers"""
    from fastapi.responses import FileResponse
    
    response = FileResponse(
        "widget/widget.js",
        media_type="application/javascript",
        headers={
            "Cache-Control": f"public, max-age=3600, s-maxage=3600",
            "ETag": f'"widget-{config.widget_version}"',
            "Vary": "Accept-Encoding"
        }
    )
    
    # Check if client has current version
    if_none_match = request.headers.get("if-none-match")
    if if_none_match == f'"widget-{config.widget_version}"':
        return Response(status_code=304)
    
    return response

@app.get("/widget/widget.css")
async def serve_widget_css(request: Request):
    """Serve widget CSS with proper cache headers"""
    from fastapi.responses import FileResponse
    
    response = FileResponse(
        "widget/widget.css",
        media_type="text/css",
        headers={
            "Cache-Control": f"public, max-age=3600, s-maxage=3600",
            "ETag": f'"widget-css-{config.widget_version}"',
            "Vary": "Accept-Encoding"
        }
    )
    
    # Check if client has current version
    if_none_match = request.headers.get("if-none-match")
    if if_none_match == f'"widget-css-{config.widget_version}"':
        return Response(status_code=304)
    
    return response

# Include chat API routes
app.include_router(chat_router)

@app.get("/")
async def root():
    return {
        "message": "Chatbot Engine Running",
        "widget_url": "/widget/widget.js",
        "version": "1.0.0",
        "status": "healthy"
    }

@app.get("/health")
@limiter.limit("10/minute")
async def health_check(request: Request):
    """Comprehensive health endpoint for monitoring"""
    try:
        from operational_safety import observability_metrics
        
        # Basic health checks
        health_status = {
            "status": "healthy",
            "timestamp": time.time(),
            "config_valid": True,
            "services": {
                "grok_api": bool(config.grok_api_key),
                "gemini_api": bool(config.gemini_api_key),
                "knowledge_system": os.path.exists(config.knowledge_dir),
                "rules_system": os.path.exists(config.rules_dir)
            },
            "metrics": observability_metrics.get_metrics()
        }
        
        # Test knowledge loading
        try:
            from knowledge_manager import KnowledgeManager
            km = KnowledgeManager()
            knowledge = km.load_all_knowledge()
            health_status["services"]["knowledge_load_test"] = len(knowledge) >= 0
        except Exception:
            health_status["services"]["knowledge_load_test"] = False
        
        # Test rules loading
        try:
            from rule_engine import RuleEngine
            re = RuleEngine()
            rules = re.load_rules()
            health_status["services"]["rules_load_test"] = len(rules) > 0
        except Exception:
            health_status["services"]["rules_load_test"] = False
        
        # Check if all services are available
        all_healthy = all(health_status["services"].values())
        if not all_healthy:
            health_status["status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        logger.error_logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host=config.host, 
        port=config.port,
        log_level="info"
    )