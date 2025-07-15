from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class DocumentProcessingRequest(BaseModel):
    file_url: str
    file_type: str
    document_type: str  # bank_statement, invoice, gst_notice, etc.
    user_id: str
    processing_options: Optional[Dict[str, Any]] = {}

class OCRResult(BaseModel):
    extracted_text: str
    confidence: float
    processing_time: float
    method_used: str  # tesseract, google_vision, easyocr

class TransactionData(BaseModel):
    date: Optional[str] = None
    description: str
    amount: Optional[float] = None
    transaction_type: Optional[str] = None  # debit, credit
    category: Optional[str] = None
    confidence: float

class BankStatementParsing(BaseModel):
    transactions: List[TransactionData]
    account_details: Dict[str, Any]
    summary: Dict[str, Any]
    parsing_confidence: float

class InvoiceData(BaseModel):
    invoice_number: Optional[str] = None
    date: Optional[str] = None
    vendor_name: Optional[str] = None
    vendor_gstin: Optional[str] = None
    total_amount: Optional[float] = None
    tax_amount: Optional[float] = None
    line_items: List[Dict[str, Any]] = []
    confidence: float

class AIQueryRequest(BaseModel):
    query: str
    context: Optional[str] = None
    user_id: str
    query_type: str = "general"  # gst, tax, compliance, general

class AIQueryResponse(BaseModel):
    answer: str
    confidence: str
    sources: List[str] = []
    follow_up_questions: List[str] = []
    query_id: str

class NoticeAnalysisRequest(BaseModel):
    notice_text: str
    notice_type: str  # gst, income_tax, tds
    user_id: str

class NoticeAnalysis(BaseModel):
    notice_type: str
    urgency: str  # high, medium, low
    key_points: List[str]
    required_actions: List[str]
    due_date_mentioned: bool
    extracted_due_date: Optional[str] = None
    suggested_response: str
    confidence: float

class WhatsAppMessage(BaseModel):
    from_number: str
    message_body: str
    media_url: Optional[str] = None
    timestamp: datetime

class WhatsAppResponse(BaseModel):
    reply_message: str
    action_type: str
    requires_processing: bool = False
    processing_data: Optional[Dict[str, Any]] = None