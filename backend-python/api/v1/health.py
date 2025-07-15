from fastapi import APIRouter
from datetime import datetime
import psutil
import redis
from config.settings import settings
import httpx
import asyncio

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "MyCG AI Service",
        "version": "1.0.0",
        "uptime": get_uptime()
    }

@router.get("/detailed")
async def detailed_health_check():
    """Detailed health check with dependencies"""
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "MyCG AI Service",
        "version": "1.0.0",
        "uptime": get_uptime(),
        "dependencies": {},
        "system": {},
        "ai_services": {}
    }
    
    # Check Redis connection
    try:
        redis_config = settings.get_redis_config()
        redis_client = redis.from_url(**redis_config)
        start_time = datetime.now()
        redis_client.ping()
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        health_status["dependencies"]["redis"] = {
            "status": "healthy", 
            "response_time_ms": round(response_time, 2),
            "config": {
                "db": redis_config["db"],
                "max_connections": redis_config["max_connections"]
            }
        }
    except Exception as e:
        health_status["dependencies"]["redis"] = {"status": "unhealthy", "error": str(e)}
    
    # Check Node.js backend
    if settings.node_backend_url:
        try:
            async with httpx.AsyncClient() as client:
                start_time = datetime.now()
                response = await client.get(
                    f"{settings.node_backend_url}/health",
                    headers={"Authorization": f"Bearer {settings.node_backend_api_key}"},
                    timeout=5
                )
                response_time = (datetime.now() - start_time).total_seconds() * 1000
                
                if response.status_code == 200:
                    health_status["dependencies"]["node_backend"] = {
                        "status": "healthy",
                        "response_time_ms": round(response_time, 2)
                    }
                else:
                    health_status["dependencies"]["node_backend"] = {
                        "status": "unhealthy",
                        "http_status": response.status_code
                    }
                    health_status["status"] = "degraded"
        except Exception as e:
            health_status["dependencies"]["node_backend"] = {"status": "unhealthy", "error": str(e)}
            health_status["status"] = "degraded"
    else:
        health_status["dependencies"]["node_backend"] = {"status": "not_configured"}
    
    # System metrics
    try:
        health_status["system"] = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
        }
    except Exception as e:
        health_status["system"] = {"error": str(e)}
    
    # Check AI services
    health_status["ai_services"] = await check_ai_services_status()
    
    return health_status

@router.get("/ai-services")
async def check_ai_services():
    """Check AI services availability"""
    return await check_ai_services_status()

async def check_ai_services_status():
    """Check AI services availability"""
    
    services_status = {}
    
    # Check if we're using Azure OpenAI
    if settings.use_azure_openai and settings.azure_openai_api_key:
        try:
            from openai import AzureOpenAI
            client = AzureOpenAI(
                api_key=settings.azure_openai_api_key,
                api_version=settings.azure_openai_api_version,
                azure_endpoint=settings.azure_openai_endpoint
            )
            
            # Test with a simple completion
            start_time = datetime.now()
            response = client.chat.completions.create(
                model=settings.azure_openai_deployment_name,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            services_status["azure_openai"] = {
                "status": "healthy",
                "model": settings.azure_openai_deployment_name,
                "endpoint": settings.azure_openai_endpoint,
                "response_time_ms": round(response_time, 2)
            }
        except Exception as e:
            services_status["azure_openai"] = {"status": "error", "error": str(e)}
    
    # Test regular OpenAI only if not using Azure
    elif settings.openai_api_key and not settings.use_azure_openai:
        try:
            import openai
            openai.api_key = settings.openai_api_key
            
            # Test with a simple completion
            start_time = datetime.now()
            response = await openai.ChatCompletion.acreate(
                model="gpt-4o",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5,
                timeout=10
            )
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            services_status["openai"] = {
                "status": "healthy",
                "model": settings.default_ai_model,
                "response_time_ms": round(response_time, 2)
            }
        except Exception as e:
            services_status["openai"] = {"status": "error", "error": str(e)}
    else:
        services_status["openai"] = {"status": "not_configured"}
        services_status["azure_openai"] = {"status": "not_configured"}
    
    # OCR Services
    services_status["ocr"] = {
        "tesseract": check_tesseract_availability(),
        "easyocr": check_easyocr_availability(),
        "google_vision": "configured" if settings.google_vision_api_key else "not_configured"
    }
    
    # WhatsApp Service
    if settings.twilio_account_sid and settings.twilio_auth_token:
        try:
            from twilio.rest import Client
            client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
            services_status["whatsapp"] = {"status": "configured"}
        except Exception as e:
            services_status["whatsapp"] = {"status": "error", "error": str(e)}
    else:
        services_status["whatsapp"] = {"status": "not_configured"}
    
    return services_status

def check_tesseract_availability():
    """Check if Tesseract is available"""
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        return "available"
    except:
        return "not_available"

def check_easyocr_availability():
    """Check if EasyOCR is available"""
    try:
        import easyocr
        return "available"
    except:
        return "not_available"

def get_uptime():
    """Get application uptime"""
    import psutil
    import os
    try:
        process = psutil.Process(os.getpid())
        create_time = datetime.fromtimestamp(process.create_time())
        uptime = datetime.now() - create_time
        return str(uptime).split('.')[0]  # Remove microseconds
    except:
        return "unknown"

@router.get("/metrics")
async def get_metrics():
    """Get detailed application metrics"""
    
    metrics = {
        "timestamp": datetime.now().isoformat(),
        "system": {},
        "application": {},
        "ai_usage": {}
    }
    
    # System metrics
    try:
        cpu_times = psutil.cpu_times()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        metrics["system"] = {
            "cpu": {
                "percent": psutil.cpu_percent(interval=1),
                "count": psutil.cpu_count(),
                "user_time": cpu_times.user,
                "system_time": cpu_times.system
            },
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "used": memory.used,
                "percent": memory.percent
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": (disk.used / disk.total) * 100
            }
        }
    except Exception as e:
        metrics["system"]["error"] = str(e)
    
    # Application metrics (would be tracked in a real app)
    metrics["application"] = {
        "total_documents_processed": 0,  # Would track this
        "total_ai_queries": 0,  # Would track this
        "total_whatsapp_messages": 0,  # Would track this
        "average_processing_time": 0,  # Would calculate this
        "error_rate": 0  # Would calculate this
    }
    
    return metrics