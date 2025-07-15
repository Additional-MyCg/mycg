from fastapi import APIRouter, Request, Form, BackgroundTasks
from services.whatsapp_ai import WhatsAppAIService
from models.ai_models import WhatsAppMessage
from datetime import datetime
import httpx
from config.settings import settings

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])

@router.post("/webhook")
async def whatsapp_webhook(
    background_tasks: BackgroundTasks,
    request: Request,
    From: str = Form(...),
    Body: str = Form(default=""),
    MediaUrl0: str = Form(default="")
):
    """Handle incoming WhatsApp messages"""
    
    try:
        # Create message object
        message = WhatsAppMessage(
            from_number=From.replace("whatsapp:", ""),
            message_body=Body,
            media_url=MediaUrl0 if MediaUrl0 else None,
            timestamp=datetime.now()
        )
        
        # Process message with AI
        whatsapp_service = WhatsAppAIService()
        response = await whatsapp_service.process_incoming_message(message)
        
        # Send immediate reply
        await whatsapp_service.send_message(message.from_number, response.reply_message)
        
        # Handle background processing if needed
        if response.requires_processing:
            background_tasks.add_task(
                handle_whatsapp_processing,
                message,
                response.processing_data
            )
        
        # Log interaction to backend
        await log_whatsapp_interaction(message, response)
        
        return {"status": "success", "message": "Message processed"}
        
    except Exception as e:
        print(f"WhatsApp webhook error: {e}")
        return {"status": "error", "message": str(e)}

async def handle_whatsapp_processing(message: WhatsAppMessage, processing_data: dict):
    """Handle background processing for WhatsApp messages"""
    
    whatsapp_service = WhatsAppAIService()
    
    try:
        action = processing_data.get("action")
        
        if action == "document_processing":
            # Download and process media
            await process_whatsapp_document(message, processing_data, whatsapp_service)
            
        elif action == "nil_filing":
            # Forward NIL filing request to backend
            await forward_nil_filing_request(message, processing_data, whatsapp_service)
            
        elif action == "status_check":
            # Get status from backend and reply
            await handle_status_check(message, processing_data, whatsapp_service)
            
    except Exception as e:
        await whatsapp_service.send_message(
            message.from_number,
            f"❌ Processing failed: {str(e)}. Please try again or contact support."
        )

async def process_whatsapp_document(message: WhatsAppMessage, processing_data: dict, whatsapp_service):
    """Process document uploaded via WhatsApp"""
    
    try:
        # Update user about processing start
        await whatsapp_service.send_processing_update(
            message.from_number, "document_processing", "started"
        )
        
        # Download media file
        media_url = processing_data.get("media_url")
        if media_url:
            # Download file (implementation depends on Twilio media handling)
            file_content = await download_whatsapp_media(media_url)
            
            # Send to document processing service
            processing_result = await send_to_document_processor(
                file_content, message.from_number
            )
            
            if processing_result.get("success"):
                await whatsapp_service.send_processing_update(
                    message.from_number, 
                    "document_processing", 
                    "success",
                    processing_result.get("data", {})
                )
            else:
                await whatsapp_service.send_processing_update(
                    message.from_number, "document_processing", "error"
                )
    
    except Exception as e:
        await whatsapp_service.send_processing_update(
            message.from_number, "document_processing", "error"
        )

async def forward_nil_filing_request(message: WhatsAppMessage, processing_data: dict, whatsapp_service):
    """Forward NIL filing request to Node.js backend"""
    
    try:
        if not settings.node_backend_url:
            raise Exception("Backend service not configured")
        
        # Send NIL filing request to backend
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.node_backend_url}/api/gst/nil-filing-request",
                json={
                    "user_phone": message.from_number,
                    "source": "whatsapp",
                    "timestamp": message.timestamp.isoformat()
                },
                headers={"Authorization": f"Bearer {settings.node_backend_api_key}"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                await whatsapp_service.send_processing_update(
                    message.from_number, "nil_filing", "success", result
                )
            else:
                await whatsapp_service.send_processing_update(
                    message.from_number, "nil_filing", "error"
                )
                
    except Exception as e:
        await whatsapp_service.send_processing_update(
            message.from_number, "nil_filing", "error"
        )

async def handle_status_check(message: WhatsAppMessage, processing_data: dict, whatsapp_service):
    """Handle GST status check request"""
    
    try:
        if not settings.node_backend_url:
            raise Exception("Backend service not configured")
        
        # Get status from backend
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.node_backend_url}/api/gst/status-by-phone/{message.from_number}",
                headers={"Authorization": f"Bearer {settings.node_backend_api_key}"},
                timeout=15
            )
            
            if response.status_code == 200:
                status_data = response.json()
                status_message = format_status_message(status_data)
                await whatsapp_service.send_message(message.from_number, status_message)
            else:
                await whatsapp_service.send_message(
                    message.from_number,
                    "❌ Unable to fetch your GST status. Please check your registration or contact support."
                )
                
    except Exception as e:
        await whatsapp_service.send_message(
            message.from_number,
            "❌ Status check failed. Please try again later."
        )

def format_status_message(status_data: dict) -> str:
    """Format GST status data into WhatsApp message"""
    
    return f"""
📊 *GST Filing Status*

🏢 Business: {status_data.get('business_name', 'N/A')}
🆔 GSTIN: {status_data.get('gstin', 'Not registered')}

📋 *Current Period Status:*
• GSTR-1: {status_data.get('gstr1_status', 'Unknown')}
• GSTR-3B: {status_data.get('gstr3b_status', 'Unknown')}

📅 Next Due: {status_data.get('next_due_date', 'N/A')}
💰 Liability: ₹{status_data.get('liability', 0):,.2f}

🔗 Complete filing: mycg.app
    """.strip()

async def download_whatsapp_media(media_url: str) -> bytes:
    """Download media file from WhatsApp"""
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(media_url, timeout=30)
            return response.content
    except Exception as e:
        raise Exception(f"Failed to download media: {e}")

async def send_to_document_processor(file_content: bytes, user_phone: str) -> dict:
    """Send document to processing service"""
    
    # This would integrate with your document processing endpoint
    # For now, return a mock response
    return {
        "success": True,
        "data": {
            "transaction_count": 5,
            "total_amount": 25000.50
        }
    }

async def log_whatsapp_interaction(message: WhatsAppMessage, response):
    """Log WhatsApp interaction to backend"""
    
    if not settings.node_backend_url:
        return
    
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{settings.node_backend_url}/api/whatsapp/interaction-log",
                json={
                    "from_number": message.from_number,
                    "message_body": message.message_body,
                    "has_media": bool(message.media_url),
                    "response_action": response.action_type,
                    "timestamp": message.timestamp.isoformat()
                },
                headers={"Authorization": f"Bearer {settings.node_backend_api_key}"},
                timeout=5
            )
    except Exception as e:
        print(f"Failed to log WhatsApp interaction: {e}")

@router.post("/send-message")
async def send_whatsapp_message(to_number: str, message: str):
    """Send WhatsApp message programmatically"""
    
    try:
        whatsapp_service = WhatsAppAIService()
        success = await whatsapp_service.send_message(to_number, message)
        
        if success:
            return {"status": "sent", "to": to_number}
        else:
            return {"status": "failed", "error": "Message sending failed"}
            
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.post("/send-notification")
async def send_notification(
    to_number: str, 
    notification_type: str,
    data: dict = None
):
    """Send formatted notification via WhatsApp"""
    
    try:
        whatsapp_service = WhatsAppAIService()
        
        # Format notification based on type
        if notification_type == "gst_reminder":
            message = f"""
🔔 *GST Filing Reminder*

Hi! Your GST return is due on {data.get('due_date', 'N/A')}.

📋 Quick Actions:
• Reply 'NIL' for NIL filing
• Reply 'STATUS' to check current status
• Visit mycg.app to complete filing

Need help? Reply 'HELP'
            """.strip()
            
        elif notification_type == "document_processed":
            message = f"""
✅ *Document Processed*

Your {data.get('document_type', 'document')} has been processed!

📊 Summary:
• {data.get('transaction_count', 0)} transactions found
• Total amount: ₹{data.get('total_amount', 0):,.2f}

Check your MyCG app for details.
            """.strip()
            
        elif notification_type == "compliance_alert":
            message = f"""
⚠️ *Compliance Alert*

{data.get('alert_message', 'Important compliance update')}

📅 Action required by: {data.get('deadline', 'N/A')}

Visit mycg.app for more details.
            """.strip()
            
        else:
            message = data.get('message', 'Notification from MyCG')
        
        success = await whatsapp_service.send_message(to_number, message)
        
        return {
            "status": "sent" if success else "failed",
            "to": to_number,
            "type": notification_type
        }
        
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/webhook")
async def whatsapp_webhook_verification(
    hub_mode: str = None,
    hub_verify_token: str = None,
    hub_challenge: str = None
):
    """Verify WhatsApp webhook (for initial setup)"""
    
    # Verify token (you should set this in your environment)
    verify_token = settings.whatsapp_verify_token or "mycg_verify_token"
    
    if hub_mode == "subscribe" and hub_verify_token == verify_token:
        return int(hub_challenge)
    else:
        return {"error": "Verification failed"}

@router.get("/health")
async def whatsapp_health_check():
    """Check WhatsApp service health"""
    
    health_status = {
        "service": "WhatsApp AI",
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }
    
    # Check Twilio configuration
    if settings.twilio_account_sid and settings.twilio_auth_token:
        health_status["twilio"] = {"configured": True}
        
        # Optional: Test Twilio connection
        try:
            from twilio.rest import Client
            client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
            # You could test the connection here
            health_status["twilio"]["connection"] = "ok"
        except Exception as e:
            health_status["twilio"]["connection"] = "error"
            health_status["status"] = "degraded"
    else:
        health_status["twilio"] = {"configured": False}
        health_status["status"] = "degraded"
    
    # Check backend connectivity
    if settings.node_backend_url:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.node_backend_url}/health",
                    timeout=5
                )
                health_status["backend"] = {
                    "status": "connected" if response.status_code == 200 else "error"
                }
        except Exception as e:
            health_status["backend"] = {"status": "disconnected"}
            health_status["status"] = "degraded"
    
    return health_status