# api/v1/ai_chat.py
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from typing import Dict, Any, Optional
from models.ai_models import AIQueryRequest, AIQueryResponse, NoticeAnalysisRequest, NoticeAnalysis
from services.ai_service import AIService
from config.settings import settings
import httpx
import logging

logger = logging.getLogger(__name__)

# Create the router
router = APIRouter(prefix="/ai", tags=["ai-services"])

# Helper functions
async def log_query_to_backend(request: AIQueryRequest, response: AIQueryResponse):
    """Log AI query to backend for analytics"""
    if not settings.node_backend_url:
        return
    
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{settings.node_backend_url}/api/ai/query-log",
                json={
                    "user_id": request.user_id,
                    "query": request.query,
                    "query_type": request.query_type,
                    "response_confidence": response.confidence,
                    "query_id": response.query_id
                },
                headers={"Authorization": f"Bearer {settings.node_backend_api_key}"},
                timeout=10
            )
    except Exception as e:
        logger.error(f"Failed to log query: {e}")

async def send_notice_analysis_to_backend(request: NoticeAnalysisRequest, analysis: NoticeAnalysis):
    """Send notice analysis results to backend"""
    if not settings.node_backend_url:
        return
    
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{settings.node_backend_url}/api/ai/notice-analyzed",
                json={
                    "user_id": request.user_id,
                    "notice_type": request.notice_type,
                    "analysis": analysis.dict()
                },
                headers={"Authorization": f"Bearer {settings.node_backend_api_key}"},
                timeout=10
            )
    except Exception as e:
        logger.error(f"Failed to send notice analysis: {e}")

async def send_reply_draft_to_backend(notice_id: str, reply_draft: str):
    """Send generated reply draft to backend"""
    if not settings.node_backend_url:
        return
    
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{settings.node_backend_url}/api/ai/reply-generated",
                json={
                    "notice_id": notice_id,
                    "reply_draft": reply_draft
                },
                headers={"Authorization": f"Bearer {settings.node_backend_api_key}"},
                timeout=10
            )
    except Exception as e:
        logger.error(f"Failed to send reply draft: {e}")

async def fetch_transaction_history(user_id: str, limit: int):
    """Fetch transaction history from backend"""
    if not settings.node_backend_url:
        return []
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.node_backend_url}/api/transactions/history/{user_id}?limit={limit}",
                headers={"Authorization": f"Bearer {settings.node_backend_api_key}"},
                timeout=10
            )
            return response.json().get("transactions", [])
    except Exception as e:
        logger.error(f"Failed to fetch transaction history: {e}")
        return []

async def send_recurring_suggestions_to_backend(user_id: str, suggestions: list):
    """Send recurring entry suggestions to backend"""
    if not settings.node_backend_url:
        return
    
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{settings.node_backend_url}/api/ai/recurring-suggestions",
                json={
                    "user_id": user_id,
                    "suggestions": suggestions
                },
                headers={"Authorization": f"Bearer {settings.node_backend_api_key}"},
                timeout=10
            )
    except Exception as e:
        logger.error(f"Failed to send recurring suggestions: {e}")

# API Endpoints
@router.post("/query", response_model=Dict[str, Any])
async def ask_ai_question(
    request: AIQueryRequest,
    background_tasks: BackgroundTasks
):
    """Ask AI a GST/tax/compliance question"""
    try:
        ai_service = AIService()
        
        # Get AI response
        response = await ai_service.answer_gst_query(
            query=request.query,
            context=request.context or ""
        )
        
        # Log query in background
        background_tasks.add_task(
            log_query_to_backend,
            request,
            response
        )
        
        return {
            "success": True,
            "answer": response.answer,
            "confidence": response.confidence,
            "sources": response.sources,
            "follow_up_questions": response.follow_up_questions,
            "query_id": response.query_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-notice", response_model=Dict[str, Any])
async def analyze_government_notice(
    request: NoticeAnalysisRequest,
    background_tasks: BackgroundTasks
):
    """Analyze government notice and provide insights"""
    try:
        ai_service = AIService()
        
        # Analyze notice
        analysis = await ai_service.analyze_notice(
            notice_text=request.notice_text,
            notice_type=request.notice_type
        )
        
        # Send to backend in background
        background_tasks.add_task(
            send_notice_analysis_to_backend,
            request,
            analysis
        )
        
        return {
            "success": True,
            **analysis.dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-reply/{notice_id}")
async def generate_notice_reply(
    notice_id: str,
    analysis: NoticeAnalysis,
    background_tasks: BackgroundTasks
):
    """Generate reply draft for government notice"""
    try:
        ai_service = AIService()
        
        # Generate reply
        reply_draft = await ai_service.generate_reply_draft(
            notice_text="",  # Would come from database
            analysis=analysis
        )
        
        # Send to backend
        background_tasks.add_task(
            send_reply_draft_to_backend,
            notice_id,
            reply_draft
        )
        
        return {
            "notice_id": notice_id,
            "reply_draft": reply_draft,
            "status": "generated"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/suggest-recurring")
async def suggest_recurring_entries(
    background_tasks: BackgroundTasks,
    user_id: str = Query(..., description="User ID"),
    transaction_limit: int = Query(50, description="Number of transactions to analyze")
):
    """Get AI-powered suggestions for recurring transactions"""
    try:
        # Fetch transaction history
        transactions = await fetch_transaction_history(user_id, transaction_limit)
        
        if not transactions:
            return {
                "user_id": user_id,
                "suggestions": [],
                "count": 0
            }
        
        ai_service = AIService()
        suggestions = await ai_service.suggest_recurring_entries(transactions)
        
        # Send suggestions to backend
        if suggestions:
            background_tasks.add_task(
                send_recurring_suggestions_to_backend,
                user_id,
                suggestions
            )
        
        return {
            "user_id": user_id,
            "suggestions": suggestions,
            "count": len(suggestions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def ai_service_health():
    """Check AI service health"""
    return {
        "service": "AI Chat Service",
        "status": "healthy",
        "endpoints": [
            "/api/v1/ai/query",
            "/api/v1/ai/analyze-notice", 
            "/api/v1/ai/generate-reply/{notice_id}",
            "/api/v1/ai/suggest-recurring"
        ]
    }