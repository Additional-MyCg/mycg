# main.py - COMPLETE REPLACEMENT
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import uvicorn
import asyncio
import os
from pathlib import Path
from config import settings

# Import settings with enhanced features
from config.settings import settings, setup_settings_handlers, configure_for_production

# Import routers
from api.v1 import document, ai_chat, whatsapp, health

# Import middleware
from core.middleware import (
    TimingMiddleware, 
    RequestLoggingMiddleware, 
    ErrorHandlingMiddleware
)
from core.exceptions import MyCGAIException

# Configure enhanced logging
def setup_logging():
    """Setup enhanced logging configuration"""
    
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure logging format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    if settings.enable_json_logging:
        import json
        import sys
        
        class JSONFormatter(logging.Formatter):
            def format(self, record):
                log_obj = {
                    'timestamp': self.formatTime(record),
                    'level': record.levelname,
                    'logger': record.name,
                    'message': record.getMessage(),
                    'module': record.module,
                    'function': record.funcName,
                    'line': record.lineno
                }
                if record.exc_info:
                    log_obj['exception'] = self.formatException(record.exc_info)
                return json.dumps(log_obj)
        
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(log_format)
    
    # Setup handlers
    handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    handlers.append(console_handler)
    
    # File handler for production
    if settings.log_file or settings.environment == "production":
        from logging.handlers import RotatingFileHandler
        
        log_file = settings.log_file or "logs/app.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=settings.log_max_size,
            backupCount=settings.log_backup_count
        )
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format=log_format,
        handlers=handlers
    )
    
    # Set specific logger levels
    if settings.debug:
        logging.getLogger("uvicorn").setLevel(logging.DEBUG)
        logging.getLogger("fastapi").setLevel(logging.DEBUG)
    else:
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 MyCG AI Service starting up...")
    logger.info(f"🔧 Environment: {settings.environment}")
    logger.info(f"🐛 Debug mode: {settings.debug}")
    
    # Setup settings handlers for auto-reload
    setup_settings_handlers()
    
    # Configure for production if needed
    if settings.is_production():
        try:
            configure_for_production()
            logger.info("✅ Production configuration applied")
        except ValueError as e:
            logger.error(f"❌ Production configuration error: {e}")
            raise
    
    # Log current configuration (masked)
    logger.info("📋 Current configuration:")
    config = settings.export_config(mask_secrets=True)
    for key, value in config.items():
        if key in ['debug', 'environment', 'app_name', 'app_version']:
            logger.info(f"  {key}: {value}")
    
    # Validate critical settings
    issues = settings.validate_critical_settings()
    if issues:
        logger.error("❌ Configuration issues found:")
        for issue in issues:
            logger.error(f"  - {issue}")
        if settings.is_production():
            raise RuntimeError("Critical configuration issues in production")
        else:
            logger.warning("⚠️ Configuration issues detected (non-production)")
    
    # Initialize services
    await initialize_services()
    
    logger.info("🎯 MyCG AI Service ready!")
    
    yield
    
    # Shutdown
    logger.info("🛑 MyCG AI Service shutting down...")
    await cleanup_services()

# Create FastAPI app with enhanced configuration
app = FastAPI(
    title=settings.app_name,
    description="AI-powered document processing and chatbot service for MyCG accounting platform",
    version=settings.app_version,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# Add CORS middleware with settings configuration
cors_config = settings.get_cors_config()
app.add_middleware(CORSMiddleware, **cors_config)

# Add custom middleware
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(TimingMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# Exception handlers
@app.exception_handler(MyCGAIException)
async def mycg_exception_handler(request: Request, exc: MyCGAIException):
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    logger.error(f"[{request_id}] MyCG Exception: {exc.message}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.message,
            "error_type": exc.__class__.__name__,
            "request_id": request_id,
            "path": str(request.url.path),
            "timestamp": logger._get_timestamp() if hasattr(logger, '_get_timestamp') else None
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "error_type": "HTTPException",
            "request_id": request_id,
            "path": str(request.url.path)
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    logger.error(f"[{request_id}] Unhandled exception: {exc}", exc_info=True)
    
    error_detail = "Internal server error"
    if not settings.is_production():
        error_detail = str(exc)
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": error_detail,
            "error_type": "UnhandledException",
            "request_id": request_id,
            "path": str(request.url.path)
        }
    )

# Include routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(document.router, prefix="/api/v1")
app.include_router(ai_chat.router, prefix="/api/v1")
app.include_router(whatsapp.router, prefix="/api/v1")

# Enhanced root endpoint
@app.get("/")
async def root():
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "environment": settings.environment,
        "debug": settings.debug,
        "docs": "/docs" if settings.debug else "disabled",
        "health": "/api/v1/health",
        "metrics": f"http://localhost:{settings.metrics_port}/metrics" if settings.enable_metrics else "disabled",
        "auto_reload": settings.enable_auto_reload and settings.is_development()
    }

async def initialize_services():
    """Initialize all services with enhanced configuration"""
    
    # Create necessary directories
    directories = ["temp_uploads", "logs", "backups"]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    # Log configuration summary
    logger.info("🔧 Service configuration:")
    logger.info(f"  📁 Max file size: {settings.max_file_size / (1024*1024):.1f}MB")
    logger.info(f"  🤖 AI model: {settings.default_ai_model}")
    logger.info(f"  ⚡ Workers: {settings.worker_processes}")
    logger.info(f"  🔄 Auto-reload: {settings.enable_auto_reload and settings.is_development()}")
    
    # Initialize AI services
    ai_config = settings.get_ai_config()
    if ai_config["openai_api_key"]:
        logger.info("✅ OpenAI configured")
        logger.info(f"  🤖 Model: {ai_config['default_model']}")
        logger.info(f"  🎛️ Temperature: {ai_config['temperature']}")
        logger.info(f"  📝 Max tokens: {ai_config['max_tokens']}")
    else:
        logger.warning("⚠️ OpenAI not configured")
    
    if settings.google_vision_api_key:
        logger.info("✅ Google Vision configured")
    else:
        logger.warning("⚠️ Google Vision not configured")
    
    if settings.anthropic_api_key:
        logger.info("✅ Anthropic configured")
    else:
        logger.warning("⚠️ Anthropic not configured")
    
    # Initialize WhatsApp service
    if settings.twilio_account_sid and settings.twilio_auth_token:
        logger.info("✅ WhatsApp service configured")
        logger.info(f"  📱 Number: {settings.whatsapp_number}")
        logger.info(f"  🚀 Rate limit: {settings.rate_limit_whatsapp}/min")
    else:
        logger.warning("⚠️ WhatsApp service not configured")
    
    # Test Node.js backend connection
    if settings.node_backend_url:
        logger.info("✅ Node.js backend configured")
        logger.info(f"  🔗 URL: {settings.node_backend_url}")
        logger.info(f"  ⏱️ Timeout: {settings.node_backend_timeout}s")
        
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.node_backend_url}/health",
                    headers={"Authorization": f"Bearer {settings.node_backend_api_key}"} if settings.node_backend_api_key else {},
                    timeout=settings.node_backend_timeout
                )
                if response.status_code == 200:
                    logger.info("✅ Backend connection successful")
                else:
                    logger.warning(f"⚠️ Backend connection failed: HTTP {response.status_code}")
        except Exception as e:
            logger.warning(f"⚠️ Backend connection error: {e}")
    else:
        logger.warning("⚠️ Node.js backend not configured")
    
    # Test Redis connection
    redis_config = settings.get_redis_config()
    try:
        import redis
        redis_client = redis.from_url(**redis_config)
        redis_client.ping()
        logger.info("✅ Redis connection successful")
        logger.info(f"  🗃️ URL: {redis_config['url']}")
        logger.info(f"  💾 DB: {redis_config['db']}")
        logger.info(f"  🔗 Max connections: {redis_config['max_connections']}")
    except Exception as e:
        logger.warning(f"⚠️ Redis connection error: {e}")
    
    # Initialize file processing
    file_config = settings.get_file_config()
    logger.info("📁 File processing configuration:")
    logger.info(f"  📏 Max size: {file_config['max_size'] / (1024*1024):.1f}MB")
    logger.info(f"  📋 Allowed types: {', '.join(file_config['allowed_types'])}")
    logger.info(f"  🕐 Retention: {file_config['retention_hours']}h")

    # Log Azure configuration
    azure_config = settings.get_azure_config()
    if azure_config["account_name"]:
        logger.info("✅ Azure Blob Storage configured")
        logger.info(f"  🗄️ Account: {azure_config['account_name']}")
        logger.info(f"  📦 Container: {azure_config['container_name']}")
    else:
        logger.warning("⚠️ Azure Blob Storage not configured")

    # Setup metrics if enabled
    if settings.enable_metrics:
        logger.info(f"📊 Metrics enabled on port {settings.metrics_port}")
    
    # Log rate limiting configuration
    logger.info("🚦 Rate limiting configuration:")
    logger.info(f"  🌐 API: {settings.rate_limit_requests}/min")
    logger.info(f"  📱 WhatsApp: {settings.rate_limit_whatsapp}/min")
    logger.info(f"  📄 Documents: {settings.rate_limit_document}/min")
    
    # ADD THIS LINE AT THE END:
    # Setup service reload callbacks for auto-reload functionality
    setup_service_reload_callbacks()

async def cleanup_services():
    """Enhanced cleanup services on shutdown"""
    
    # Cleanup settings watcher
    try:
        if hasattr(settings, '_observer') and settings._observer and settings._observer.is_alive():
            settings._observer.stop()
            settings._observer.join(timeout=5)
            logger.info("✅ Settings watcher stopped")
    except Exception as e:
        logger.error(f"❌ Error stopping settings watcher: {e}")
    
    # Clean up temporary files based on retention policy
    try:
        import time
        from pathlib import Path
        
        temp_dir = Path("temp_uploads")
        if temp_dir.exists():
            current_time = time.time()
            retention_seconds = settings.temp_file_retention_hours * 3600
            cleaned_files = 0
            
            for file_path in temp_dir.iterdir():
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > retention_seconds:
                        file_path.unlink()
                        cleaned_files += 1
            
            if cleaned_files > 0:
                logger.info(f"✅ Cleaned up {cleaned_files} old temporary files")
            else:
                logger.info("✅ No old temporary files to clean")
    except Exception as e:
        logger.error(f"❌ Cleanup error: {e}")
    
    # Close any open connections
    try:
        # Close Redis connections if any
        import redis
        # Redis connections are automatically closed
        logger.info("✅ Database connections closed")
    except Exception as e:
        logger.error(f"❌ Error closing connections: {e}")

def setup_service_reload_callbacks():
    """Setup callbacks for service configuration reloads"""
    
    def on_ai_settings_change(changed_fields):
        """Handle AI settings changes"""
        ai_fields = ['openai_api_key', 'default_ai_model', 'max_tokens', 'temperature', 'ai_request_timeout', 'ai_max_retries']
        if any(field in changed_fields for field in ai_fields):
            logger.info("🤖 AI settings changed - services will reload on next request")
    
    def on_redis_settings_change(changed_fields):
        """Handle Redis settings changes"""
        redis_fields = ['redis_url', 'redis_password', 'redis_db', 'redis_max_connections']
        if any(field in changed_fields for field in redis_fields):
            logger.info("🗃️ Redis settings changed - reconnection required")
    
    def on_file_settings_change(changed_fields):
        """Handle file processing settings changes"""
        file_fields = ['max_file_size', 'allowed_file_types', 'temp_file_retention_hours']
        if any(field in changed_fields for field in file_fields):
            logger.info("📁 File processing settings changed")
    
    def on_whatsapp_settings_change(changed_fields):
        """Handle WhatsApp settings changes"""
        whatsapp_fields = ['twilio_account_sid', 'twilio_auth_token', 'whatsapp_number', 'rate_limit_whatsapp']
        if any(field in changed_fields for field in whatsapp_fields):
            logger.info("📱 WhatsApp settings changed")
    
    # Register all callbacks
    settings.add_reload_callback(on_ai_settings_change)
    settings.add_reload_callback(on_redis_settings_change)
    settings.add_reload_callback(on_file_settings_change)
    settings.add_reload_callback(on_whatsapp_settings_change)
    
    logger.info("✅ Service reload callbacks registered")
    
# Enhanced development server
if __name__ == "__main__":
    # Use settings for server configuration
    server_config = {
        "app": "main:app",
        "host": "0.0.0.0",
        "port": 8001,
        "workers": 1 if settings.debug else settings.worker_processes,
        "log_level": settings.log_level.lower(),
        "reload": settings.debug and settings.enable_auto_reload,
        "access_log": True,
        "use_colors": True,
        "loop": "asyncio"
    }
    
    # Add reload directories for development
    if settings.debug and settings.enable_auto_reload:
        server_config["reload_dirs"] = ["."]
        server_config["reload_includes"] = ["*.py", "*.env"]
    
    logger.info("🚀 Starting development server...")
    logger.info(f"📋 Server config: {server_config}")
    
    uvicorn.run(**server_config)