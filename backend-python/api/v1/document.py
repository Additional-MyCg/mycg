from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from typing import Dict, Any
import asyncio

from services.ocr_service import OCRService
from services.document_processor import DocumentProcessor
from services.ai_service import AIService
from utils.file_handler import FileHandler
from models.ai_models import DocumentProcessingRequest, OCRResult, BankStatementParsing, InvoiceData
from config.settings import settings
import httpx

router = APIRouter(prefix="/document", tags=["document-processing"])

@router.post("/process", response_model=Dict[str, Any])
async def process_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    document_type: str = "auto",
    user_id: str = "anonymous",
    ocr_method: str = "auto"
):
    """Process uploaded document with OCR and AI analysis"""
    
    try:
        # Save uploaded file
        file_handler = FileHandler()
        file_info = await file_handler.save_upload_file(file, user_id)
        
        # Upload to Azure if configured
        azure_url = None
        if file_handler.blob_service_client:
            azure_url = await file_handler.upload_to_azure(
                file_info["file_path"], 
                f"documents/{user_id}/{file_info['filename']}"
            )
            file_info["azure_url"] = azure_url
        
        # Start processing in background
        background_tasks.add_task(
            process_document_background,
            file_info,
            document_type,
            user_id,
            ocr_method
        )
        
        return {
            "message": "Document uploaded successfully",
            "processing_id": file_info["filename"],
            "status": "processing",
            "estimated_time": "1-2 minutes"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Upload failed: {str(e)}")

async def process_document_background(
    file_info: Dict[str, Any],
    document_type: str,
    user_id: str,
    ocr_method: str
):
    """Background task for document processing"""
    
    ocr_service = OCRService()
    doc_processor = DocumentProcessor()
    ai_service = AIService()
    file_handler = FileHandler()
    
    processing_result = {
        "success": False,
        "error": None,
        "data": {}
    }
    
    try:
        # Convert PDF to image if needed
        file_path = await file_handler.convert_to_image(file_info["file_path"])
        
        # Step 1: OCR Processing
        ocr_result = await ocr_service.extract_text_from_image(file_path, ocr_method)
        
        # Step 2: Document Processing based on type
        if document_type == "auto":
            document_type = await detect_document_type(ocr_result.extracted_text)
        
        processed_data = None
        if document_type == "bank_statement":
            processed_data = await doc_processor.parse_bank_statement(ocr_result.extracted_text)
        elif document_type == "invoice":
            processed_data = await doc_processor.parse_invoice(ocr_result.extracted_text)
        
        # Step 3: AI Enhancement
        enhanced_data = None
        if processed_data and document_type == "bank_statement":
            enhanced_data = await enhance_bank_statement_with_ai(processed_data, ai_service)
        
        processing_result.update({
            "success": True,
            "data": {
                "ocr_result": ocr_result.dict(),
                "document_type": document_type,
                "processed_data": processed_data.dict() if processed_data else None,
                "enhanced_data": enhanced_data,
                "file_info": file_info
            }
        })
        
        # Send results to Node.js backend
        await send_results_to_backend(user_id, processing_result)
        
    except Exception as e:
        processing_result.update({
            "success": False,
            "error": str(e)
        })
        
        # Send error to backend
        await send_results_to_backend(user_id, processing_result)
    
    finally:
        # Cleanup temporary files
        await file_handler.cleanup_temp_file(file_info["file_path"])
        if file_path != file_info["file_path"]:
            await file_handler.cleanup_temp_file(file_path)

async def detect_document_type(text: str) -> str:
    """Auto-detect document type from extracted text"""
    text_lower = text.lower()
    
    # Bank statement indicators
    if any(word in text_lower for word in ['statement', 'account', 'balance', 'transaction', 'bank']):
        return "bank_statement"
    
    # Invoice indicators
    elif any(word in text_lower for word in ['invoice', 'bill', 'gstin', 'tax invoice']):
        return "invoice"
    
    # GST notice indicators
    elif any(word in text_lower for word in ['gst', 'notice', 'department', 'compliance']):
        return "gst_notice"
    
    return "other"

async def enhance_bank_statement_with_ai(statement_data: BankStatementParsing, ai_service: AIService) -> Dict[str, Any]:
    """Enhance bank statement data with AI categorization"""
    
    enhanced_transactions = []
    
    for transaction in statement_data.transactions:
        if transaction.amount:
            # Get AI categorization
            ai_category = await ai_service.categorize_transaction(
                transaction.description,
                transaction.amount
            )
            
            enhanced_transaction = {
                **transaction.dict(),
                "ai_category": ai_category.get("category"),
                "ai_confidence": ai_category.get("confidence"),
                "is_business_expense": ai_category.get("is_business_expense"),
                "gst_applicable": ai_category.get("gst_applicable"),
                "suggested_gst_rate": ai_category.get("suggested_gst_rate"),
                "tags": ai_category.get("tags", [])
            }
            
            enhanced_transactions.append(enhanced_transaction)
    
    return {
        "enhanced_transactions": enhanced_transactions,
        "ai_summary": {
            "total_business_expenses": sum(t["amount"] for t in enhanced_transactions if t.get("is_business_expense")),
            "gst_applicable_amount": sum(t["amount"] for t in enhanced_transactions if t.get("gst_applicable")),
            "categories_found": list(set(t.get("ai_category") for t in enhanced_transactions if t.get("ai_category")))
        }
    }

async def send_results_to_backend(user_id: str, results: Dict[str, Any]):
    """Send processing results to Node.js backend"""
    
    if not settings.node_backend_url:
        return
    
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{settings.node_backend_url}/api/ai/document-processed",
                json={
                    "user_id": user_id,
                    "results": results
                },
                headers={
                    "Authorization": f"Bearer {settings.node_backend_api_key}",
                    "Content-Type": "application/json"
                },
                timeout=30
            )
    except Exception as e:
        print(f"Failed to send results to backend: {e}")

@router.get("/status/{processing_id}")
async def get_processing_status(processing_id: str):
    """Get document processing status"""
    # In a real implementation, you'd check Redis or database
    return {
        "processing_id": processing_id,
        "status": "completed",
        "message": "Check your Node.js backend for results"
    }