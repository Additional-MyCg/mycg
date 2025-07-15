import openai
import asyncio
from typing import Dict, Any, List
import json
import re
from config.settings import settings
from models.ai_models import AIQueryResponse, NoticeAnalysis

class AIService:
    def __init__(self):
        ai_config = settings.get_ai_config()
        
        openai.api_key = ai_config["openai_api_key"]
        self.model = ai_config["default_model"]
        self.max_tokens = ai_config["max_tokens"]
        self.temperature = ai_config["temperature"]
        self.timeout = ai_config["timeout"]
        self.max_retries = ai_config["max_retries"]
    
    async def categorize_transaction(self, description: str, amount: float) -> Dict[str, Any]:
        """Categorize transaction using AI"""
        
        prompt = f"""
        Analyze this transaction and provide categorization:
        
        Description: {description}
        Amount: ₹{amount}
        
        Respond with JSON containing:
        - category: specific category (e.g., "Office Supplies", "Travel - Taxi", "Food - Restaurant")
        - transaction_type: "income" or "expense"
        - confidence: 0.0 to 1.0
        - tags: array of relevant tags
        - is_business_expense: boolean
        - gst_applicable: boolean (if likely GST applicable)
        - suggested_gst_rate: 0, 5, 12, 18, or 28
        """
        
        try:
            response = await self._call_openai(prompt, max_tokens=200)
            result = json.loads(response)
            return result
            
        except Exception as e:
            # Fallback categorization
            return {
                "category": "Miscellaneous",
                "transaction_type": "expense",
                "confidence": 0.3,
                "tags": ["uncategorized"],
                "is_business_expense": False,
                "gst_applicable": False,
                "suggested_gst_rate": 0
            }
    def reload_config(self, changed_fields):
        """Reload AI configuration when settings change"""
        if any(field in changed_fields for field in ['openai_api_key', 'default_ai_model', 'max_tokens', 'temperature']):
            logger.info("🤖 Reloading AI service configuration...")
            ai_config = settings.get_ai_config()
            
            openai.api_key = ai_config["openai_api_key"]
            self.model = ai_config["default_model"]
            self.max_tokens = ai_config["max_tokens"]
            self.temperature = ai_config["temperature"]
            self.timeout = ai_config["timeout"]
            self.max_retries = ai_config["max_retries"]
            
            logger.info("✅ AI service configuration reloaded")
    async def answer_gst_query(self, query: str, context: str = "") -> AIQueryResponse:
        """Answer GST/compliance related queries"""
        
        prompt = f"""
        You are a GST and tax compliance expert for Indian businesses. 
        Answer this query clearly and practically:
        
        Query: {query}
        Context: {context}
        
        Provide:
        1. Direct, actionable answer
        2. Relevant GST section/rule if applicable
        3. Important notes or exceptions
        4. Practical next steps
        
        Keep response under 300 words and focus on practical advice.
        """
        
        try:
            answer = await self._call_openai(prompt, max_tokens=400)
            
            # Generate follow-up questions
            follow_ups = await self._generate_follow_up_questions(query, answer)
            
            return AIQueryResponse(
                answer=answer,
                confidence="high",
                sources=["GST Act", "AI Analysis"],
                follow_up_questions=follow_ups,
                query_id=f"gst_{hash(query) % 10000}"
            )
            
        except Exception as e:
            return AIQueryResponse(
                answer="I apologize, but I'm unable to process your GST query at the moment. Please try again later or contact our support team.",
                confidence="low",
                sources=[],
                follow_up_questions=[],
                query_id="error_001"
            )
    
    async def analyze_notice(self, notice_text: str, notice_type: str) -> NoticeAnalysis:
        """Analyze government notice and suggest response"""
        
        prompt = f"""
        Analyze this {notice_type} notice and provide structured analysis:
        
        Notice Content: {notice_text}
        
        Provide JSON response with:
        - urgency: "high", "medium", or "low"
        - key_points: array of main issues (max 5)
        - required_actions: array of specific actions needed (max 5)
        - due_date_mentioned: boolean
        - extracted_due_date: "YYYY-MM-DD" format if found
        - suggested_response: brief response strategy (2-3 sentences)
        - confidence: 0.0 to 1.0
        """
        
        try:
            response = await self._call_openai(prompt, max_tokens=500)
            data = json.loads(response)
            
            return NoticeAnalysis(
                notice_type=notice_type,
                urgency=data.get("urgency", "medium"),
                key_points=data.get("key_points", []),
                required_actions=data.get("required_actions", []),
                due_date_mentioned=data.get("due_date_mentioned", False),
                extracted_due_date=data.get("extracted_due_date"),
                suggested_response=data.get("suggested_response", "Consult with compliance expert"),
                confidence=data.get("confidence", 0.5)
            )
            
        except Exception as e:
            return NoticeAnalysis(
                notice_type=notice_type,
                urgency="medium",
                key_points=["Unable to analyze automatically"],
                required_actions=["Manual review required"],
                due_date_mentioned=False,
                suggested_response="Please consult with a tax compliance expert for proper analysis",
                confidence=0.1
            )
    
    async def generate_reply_draft(self, notice_text: str, analysis: NoticeAnalysis) -> str:
        """Generate reply draft for government notice"""
        
        prompt = f"""
        Generate a professional reply draft for this government notice:
        
        Notice Summary:
        - Type: {analysis.notice_type}
        - Urgency: {analysis.urgency}
        - Key Points: {', '.join(analysis.key_points)}
        - Required Actions: {', '.join(analysis.required_actions)}
        
        Create a formal, professional reply addressing the notice concerns.
        Include proper formatting, reference numbers, and request for clarification if needed.
        Keep it concise but comprehensive.
        """
        
        try:
            reply_draft = await self._call_openai(prompt, max_tokens=600)
            return reply_draft
        except Exception as e:
            return "Unable to generate reply draft. Please consult with a compliance expert."
    
    async def suggest_recurring_entries(self, transaction_history: List[Dict]) -> List[Dict[str, Any]]:
        """Analyze transaction history to suggest recurring entries"""
        
        # Prepare transaction data for analysis
        transaction_text = "\n".join([
            f"Date: {t.get('date', 'N/A')}, Description: {t.get('description', 'N/A')}, Amount: ₹{t.get('amount', 0)}"
            for t in transaction_history[-50:]  # Last 50 transactions
        ])
        
        prompt = f"""
        Analyze these transactions to identify recurring patterns:
        
        {transaction_text}
        
        Identify transactions that appear to be recurring (monthly, quarterly, etc.) and respond with JSON:
        [
            {{
                "description": "pattern description",
                "amount": estimated_amount,
                "frequency": "monthly/quarterly/yearly",
                "category": "suggested category",
                "confidence": 0.0 to 1.0,
                "next_due_estimate": "YYYY-MM-DD"
            }}
        ]
        
        Only include patterns with confidence > 0.7. Max 5 suggestions.
        """
        
        try:
            response = await self._call_openai(prompt, max_tokens=500)
            suggestions = json.loads(response)
            return suggestions if isinstance(suggestions, list) else []
        except Exception as e:
            return []
    
    async def _call_openai(self, prompt: str, max_tokens: int = None) -> str:
        try:
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant specializing in Indian GST, tax compliance, and accounting. Always provide accurate, actionable advice."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens or self.max_tokens,
                temperature=self.temperature,
                timeout=self.timeout
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    async def _generate_follow_up_questions(self, original_query: str, answer: str) -> List[str]:
        """Generate follow-up questions based on the query and answer"""
        
        prompt = f"""
        Based on this GST/tax query and answer, suggest 2-3 relevant follow-up questions:
        
        Original Query: {original_query}
        Answer: {answer}
        
        Generate practical follow-up questions that users might have. Return as JSON array of strings.
        """
        
        try:
            response = await self._call_openai(prompt, max_tokens=150)
            questions = json.loads(response)
            return questions[:3] if isinstance(questions, list) else []
        except:
            return [
                "What documents do I need for this?",
                "What are the penalties if not complied?",
                "Can you explain this in simpler terms?"
            ]
