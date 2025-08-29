from twilio.rest import Client
from typing import Dict, Any
import re
from config.settings import settings
from models.ai_models import WhatsAppMessage, WhatsAppResponse
from services.ai_service import AIService
import logging
from twilio.rest import Client

logger = logging.getLogger(__name__)

class WhatsAppAIService:
    def __init__(self):
        # Initialize Twilio client if credentials are available
        if settings.twilio_account_sid and settings.twilio_auth_token:
            self.client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        else:
            self.client = None
            logger.warning("WhatsApp service not configured - missing Twilio credentials")
        
        self.whatsapp_number = settings.whatsapp_number
        self.ai_service = AIService()
        
        # Store rate limiting info
        self.rate_limit = settings.rate_limit_whatsapp
        logger.info(f"WhatsApp service initialized with rate limit: {self.rate_limit}/min")
    
    async def process_incoming_message(self, message: WhatsAppMessage) -> WhatsAppResponse:
        """Process incoming WhatsApp message with AI"""
        
        message_lower = message.message_body.lower().strip()
        
        # Handle specific commands first
        if message_lower in ['nil', 'nil filing']:
            return WhatsAppResponse(
                reply_message="📋 NIL Filing request received. I'll forward this to your accounting system for processing. You'll receive confirmation shortly.",
                action_type="nil_filing",
                requires_processing=True,
                processing_data={"user_phone": message.from_number, "action": "nil_filing"}
            )
        
        elif message_lower in ['status', 'gst status']:
            return WhatsAppResponse(
                reply_message="📊 Checking your GST filing status... Please wait while I fetch the latest information.",
                action_type="status_check",
                requires_processing=True,
                processing_data={"user_phone": message.from_number, "action": "status_check"}
            )
        
        elif message_lower in ['help', 'menu']:
            return WhatsAppResponse(
                reply_message=self._get_help_message(),
                action_type="help",
                requires_processing=False
            )
        
        elif message.media_url:
            return WhatsAppResponse(
                reply_message="📄 Document received! Processing with AI... I'll extract the data and create ledger entries. This usually takes 1-2 minutes.",
                action_type="document_upload",
                requires_processing=True,
                processing_data={
                    "user_phone": message.from_number,
                    "media_url": message.media_url,
                    "action": "document_processing"
                }
            )
        
        # Handle AI queries
        elif len(message.message_body) > 10:  # Assume it's a question
            try:
                ai_response = await self.ai_service.answer_gst_query(
                    query=message.message_body,
                    context="WhatsApp chat"
                )
                
                reply_message = f"🤖 {ai_response.answer}\n\n"
                if ai_response.follow_up_questions:
                    reply_message += "❓ Related questions:\n"
                    for i, q in enumerate(ai_response.follow_up_questions[:2], 1):
                        reply_message += f"{i}. {q}\n"
                
                return WhatsAppResponse(
                    reply_message=reply_message,
                    action_type="ai_query",
                    requires_processing=False
                )
            
            except Exception as e:
                return WhatsAppResponse(
                    reply_message="🤖 I'm having trouble processing your question right now. Please try again or contact our support team.",
                    action_type="error",
                    requires_processing=False
                )
        
        # Default response
        return WhatsAppResponse(
            reply_message="👋 Hi! I'm your MyCG AI assistant. Send 'HELP' to see what I can do, or ask me any GST/tax question!",
            action_type="default",
            requires_processing=False
        )
    
    async def send_message(self, to_number: str, message: str) -> bool:
        """Send WhatsApp message"""
        if not self.client:
            return False
        
        try:
            message = self.client.messages.create(
                body=message,
                from_=f'whatsapp:{self.whatsapp_number}',
                to=f'whatsapp:{to_number}'
            )
            return True
        except Exception as e:
            print(f"WhatsApp send error: {e}")
            return False
    
    async def send_processing_update(self, to_number: str, processing_type: str, status: str, data: Dict = None):
        """Send processing status update"""
        
        messages = {
            "document_processing": {
                "started": "🔄 Starting document analysis...",
                "ocr_complete": "✅ Text extraction complete. Analyzing transactions...",
                "ai_complete": "🤖 AI analysis complete. Creating ledger entries...",
                "success": f"✅ Processing complete!\n📊 Found {data.get('transaction_count', 0)} transactions\n💰 Total amount: ₹{data.get('total_amount', 0):,.2f}\n\n📱 Check your MyCG app for details.",
                "error": "❌ Document processing failed. Please try uploading again or contact support."
            },
            "nil_filing": {
                "started": "📋 Processing NIL filing...",
                "success": f"✅ NIL filing completed!\n📄 Reference: {data.get('reference_no', 'N/A')}\n📅 Filed on: {data.get('filing_date', 'N/A')}",
                "error": "❌ NIL filing failed. Please try again or contact support."
            }
        }
        
        message_text = messages.get(processing_type, {}).get(status, "Processing update...")
        await self.send_message(to_number, message_text)
    
    def _get_help_message(self) -> str:
        return """
🤖 MyCG AI Assistant - Commands:

📋 *Filing & Status:*
• Send 'NIL' - File NIL GST return
• Send 'STATUS' - Check filing status

📄 *Documents:*
• Upload bank statements - Auto-create entries
• Upload invoices - Extract & categorize
• Upload notices - AI analysis & reply

❓ *Ask Questions:*
• "Can I claim home office expenses?"
• "What's the GST rate for software?"
• "How to file GSTR-1?"

🔗 *Quick Links:*
• MyCG App: mycg.app
• Support: support@mycg.app

Just type your question or upload a document!
        """