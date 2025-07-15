import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock, AsyncMock
import json
import io

class TestDocumentAPI:
    
    def test_process_document_success(self, client, sample_pdf_file):
        """Test successful document processing"""
        
        with patch('services.ocr_service.OCRService') as mock_ocr, \
             patch('services.document_processor.DocumentProcessor') as mock_processor, \
             patch('services.ai_service.AIService') as mock_ai:
            
            # Mock OCR result
            mock_ocr_instance = mock_ocr.return_value
            mock_ocr_instance.extract_text_from_image = AsyncMock(return_value=Mock(
                extracted_text="Sample bank statement text",
                confidence=0.9,
                processing_time=1.2,
                method_used="tesseract"
            ))
            
            # Mock document processor
            mock_processor_instance = mock_processor.return_value
            mock_processor_instance.parse_bank_statement = AsyncMock(return_value=Mock(
                transactions=[],
                account_details={},
                summary={"total_transactions": 0},
                parsing_confidence=0.8
            ))
            
            with open(sample_pdf_file, 'rb') as f:
                response = client.post(
                    "/api/v1/document/process",
                    files={"file": ("test.pdf", f, "application/pdf")},
                    data={"user_id": "test_user", "document_type": "bank_statement"}
                )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "processing"
            assert "processing_id" in data
    
    def test_process_document_invalid_file_type(self, client):
        """Test document processing with invalid file type"""
        
        # Create a text file (not allowed)
        file_content = b"This is a text file"
        
        response = client.post(
            "/api/v1/document/process",
            files={"file": ("test.txt", io.BytesIO(file_content), "text/plain")},
            data={"user_id": "test_user"}
        )
        
        assert response.status_code == 400
        assert "not allowed" in response.json()["detail"]
    
    def test_process_document_file_too_large(self, client):
        """Test document processing with oversized file"""
        
        # Create a large file (>10MB)
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
        
        response = client.post(
            "/api/v1/document/process",
            files={"file": ("large.pdf", io.BytesIO(large_content), "application/pdf")},
            data={"user_id": "test_user"}
        )
        
        assert response.status_code == 400
        assert "too large" in response.json()["detail"]
    
    def test_get_processing_status(self, client):
        """Test getting processing status"""
        
        response = client.get("/api/v1/document/status/test_processing_id")
        
        assert response.status_code == 200
        data = response.json()
        assert "processing_id" in data
        assert "status" in data