from models.ai_models import AIQueryRequest, AIQueryResponse
# from models.notice_analysis import NoticeAnalysisRequest, NoticeAnalysis
from config import settings
import httpx
from models.ai_models import NoticeAnalysisRequest, NoticeAnalysis

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
        print(f"Failed to log query: {e}")

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
        print(f"Failed to send notice analysis: {e}")

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
        print(f"Failed to send reply draft: {e}")

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
        print(f"Failed to fetch transaction history: {e}")
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
        print(f"Failed to send recurring suggestions: {e}")