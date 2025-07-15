from pydantic import BaseModel
from typing import Optional, Any, Dict, List
from datetime import datetime

class BaseResponse(BaseModel):
    """Base response model"""
    success: bool
    message: str
    timestamp: datetime = datetime.now()
    request_id: Optional[str] = None

class SuccessResponse(BaseResponse):
    """Success response model"""
    success: bool = True
    data: Optional[Any] = None

class ErrorResponse(BaseResponse):
    """Error response model"""
    success: bool = False
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class ProcessingResponse(BaseModel):
    """Processing status response"""
    processing_id: str
    status: str  # processing, completed, failed
    progress: Optional[int] = None  # 0-100
    estimated_completion: Optional[datetime] = None
    results: Optional[Dict[str, Any]] = None

class HealthResponse(BaseModel):
    """Health check response"""
    status: str  # healthy, degraded, unhealthy
    timestamp: datetime
    service: str
    version: str
    uptime: Optional[str] = None
    dependencies: Optional[Dict[str, Any]] = None

class AIQueryResponseModel(BaseModel):
    """AI query response model"""
    query_id: str
    answer: str
    confidence: str
    processing_time: Optional[float] = None
    sources: List[str] = []
    follow_up_questions: List[str] = []

class DocumentProcessingResponse(BaseModel):
    """Document processing response"""
    document_id: str
    original_filename: str
    document_type: str
    processing_status: str
    ocr_confidence: Optional[float] = None
    extracted_data: Optional[Dict[str, Any]] = None
    ai_insights: Optional[Dict[str, Any]] = None