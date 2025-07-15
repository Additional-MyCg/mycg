# ==============================================
# TESTS DIRECTORY
# ==============================================

# tests/__init__.py
"""
Test suite for MyCG AI Service
"""

# tests/conftest.py
import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock
import tempfile
import os
from main import app
from config.settings import settings

@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)

@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    mock = Mock()
    mock.ping.return_value = True
    mock.get.return_value = None
    mock.set.return_value = True
    return mock

@pytest.fixture
def mock_openai():
    """Mock OpenAI client"""
    mock = AsyncMock()
    mock.ChatCompletion.acreate.return_value = Mock(
        choices=[Mock(message=Mock(content='{"category": "Test", "confidence": 0.9}'))]
    )
    return mock

@pytest.fixture
def sample_pdf_file():
    """Create a sample PDF file for testing"""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        f.write(b'%PDF-1.4 sample pdf content')
        yield f.name
    os.unlink(f.name)

@pytest.fixture
def sample_image_file():
    """Create a sample image file for testing"""
    from PIL import Image
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        img = Image.new('RGB', (100, 100), color='white')
        img.save(f.name, 'JPEG')
        yield f.name
    os.unlink(f.name)

@pytest.fixture
def mock_settings():
    """Mock settings for testing"""
    test_settings = settings.copy()
    test_settings.openai_api_key = "test-key"
    test_settings.node_backend_url = "http://test-backend"
    return test_settings

# ==============================================
# tests/test_api/__init__.py
# ==============================================
"""
API endpoint tests
"""

# ==============================================
# tests/test_api/test_document.py
# ==============================================

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

# ==============================================
# tests/test_api/test_ai_chat.py
# ==============================================

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock, AsyncMock

class TestAIChatAPI:
    
    def test_ask_ai_question_success(self, client):
        """Test successful AI query"""
        
        with patch('services.ai_service.AIService') as mock_ai:
            mock_ai_instance = mock_ai.return_value
            mock_ai_instance.answer_gst_query = AsyncMock(return_value=Mock(
                answer="GST rate for software is 18%",
                confidence="high",
                sources=["GST Act"],
                follow_up_questions=["What about export of software?"],
                query_id="gst_1234"
            ))
            
            response = client.post(
                "/api/v1/ai/query",
                json={
                    "query": "What is GST rate for software?",
                    "user_id": "test_user",
                    "query_type": "gst"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "answer" in data
            assert data["confidence"] == "high"
            assert len(data["follow_up_questions"]) > 0
    
    def test_analyze_notice_success(self, client):
        """Test successful notice analysis"""
        
        with patch('services.ai_service.AIService') as mock_ai:
            mock_ai_instance = mock_ai.return_value
            mock_ai_instance.analyze_notice = AsyncMock(return_value=Mock(
                notice_type="gst",
                urgency="high",
                key_points=["Missing GSTR-1 filing"],
                required_actions=["File GSTR-1 immediately"],
                due_date_mentioned=True,
                extracted_due_date="2024-01-20",
                suggested_response="File the return with penalty",
                confidence=0.9
            ))
            
            response = client.post(
                "/api/v1/ai/analyze-notice",
                json={
                    "notice_text": "Your GSTR-1 for Oct 2023 is pending...",
                    "notice_type": "gst",
                    "user_id": "test_user"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["urgency"] == "high"
            assert len(data["key_points"]) > 0
            assert data["due_date_mentioned"] == True
    
    def test_generate_notice_reply(self, client):
        """Test notice reply generation"""
        
        with patch('services.ai_service.AIService') as mock_ai:
            mock_ai_instance = mock_ai.return_value
            mock_ai_instance.generate_reply_draft = AsyncMock(
                return_value="Dear Sir/Madam, We acknowledge receipt of the notice..."
            )
            
            # Mock notice analysis data
            analysis_data = {
                "notice_type": "gst",
                "urgency": "high",
                "key_points": ["Missing filing"],
                "required_actions": ["File return"],
                "due_date_mentioned": True,
                "suggested_response": "File immediately",
                "confidence": 0.9
            }
            
            response = client.post(
                "/api/v1/ai/generate-reply/notice_123",
                json=analysis_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "reply_draft" in data
            assert data["status"] == "generated"
    
    def test_suggest_recurring_entries(self, client):
        """Test recurring entries suggestion"""
        
        with patch('utils.fetch_transaction_history') as mock_fetch, \
             patch('services.ai_service.AIService') as mock_ai:
            
            # Mock transaction history
            mock_fetch.return_value = [
                {"date": "2023-01-01", "description": "Office Rent", "amount": 50000},
                {"date": "2023-02-01", "description": "Office Rent", "amount": 50000}
            ]
            
            # Mock AI suggestions
            mock_ai_instance = mock_ai.return_value
            mock_ai_instance.suggest_recurring_entries = AsyncMock(return_value=[
                {
                    "description": "Office Rent",
                    "amount": 50000,
                    "frequency": "monthly",
                    "category": "Office Expenses",
                    "confidence": 0.95,
                    "next_due_estimate": "2024-02-01"
                }
            ])
            
            response = client.post(
                "/api/v1/ai/suggest-recurring?user_id=test_user&transaction_limit=50"
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["suggestions"]) > 0
            assert data["suggestions"][0]["frequency"] == "monthly"

# ==============================================
# tests/test_api/test_whatsapp.py
# ==============================================

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock, AsyncMock

class TestWhatsAppAPI:
    
    def test_whatsapp_webhook_text_message(self, client):
        """Test WhatsApp webhook with text message"""
        
        with patch('services.whatsapp_ai.WhatsAppAIService') as mock_whatsapp:
            mock_instance = mock_whatsapp.return_value
            mock_instance.process_incoming_message = AsyncMock(return_value=Mock(
                reply_message="Hello! How can I help you?",
                action_type="default",
                requires_processing=False
            ))
            mock_instance.send_message = AsyncMock(return_value=True)
            
            response = client.post(
                "/api/v1/whatsapp/webhook",
                data={
                    "From": "whatsapp:+1234567890",
                    "Body": "Hello",
                    "MediaUrl0": ""
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
    
    def test_whatsapp_webhook_nil_filing(self, client):
        """Test WhatsApp NIL filing command"""
        
        with patch('services.whatsapp_ai.WhatsAppAIService') as mock_whatsapp:
            mock_instance = mock_whatsapp.return_value
            mock_instance.process_incoming_message = AsyncMock(return_value=Mock(
                reply_message="NIL Filing request received...",
                action_type="nil_filing",
                requires_processing=True,
                processing_data={"action": "nil_filing"}
            ))
            mock_instance.send_message = AsyncMock(return_value=True)
            
            response = client.post(
                "/api/v1/whatsapp/webhook",
                data={
                    "From": "whatsapp:+1234567890",
                    "Body": "NIL",
                    "MediaUrl0": ""
                }
            )
            
            assert response.status_code == 200
    
    def test_whatsapp_webhook_document_upload(self, client):
        """Test WhatsApp document upload"""
        
        with patch('services.whatsapp_ai.WhatsAppAIService') as mock_whatsapp:
            mock_instance = mock_whatsapp.return_value
            mock_instance.process_incoming_message = AsyncMock(return_value=Mock(
                reply_message="Document received! Processing...",
                action_type="document_upload",
                requires_processing=True,
                processing_data={"action": "document_processing", "media_url": "http://example.com/image.jpg"}
            ))
            mock_instance.send_message = AsyncMock(return_value=True)
            
            response = client.post(
                "/api/v1/whatsapp/webhook",
                data={
                    "From": "whatsapp:+1234567890",
                    "Body": "",
                    "MediaUrl0": "http://example.com/image.jpg"
                }
            )
            
            assert response.status_code == 200
    
    def test_send_whatsapp_message(self, client):
        """Test sending WhatsApp message programmatically"""
        
        with patch('services.whatsapp_ai.WhatsAppAIService') as mock_whatsapp:
            mock_instance = mock_whatsapp.return_value
            mock_instance.send_message = AsyncMock(return_value=True)
            
            response = client.post(
                "/api/v1/whatsapp/send-message?to_number=+1234567890&message=Test message"
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "sent"
    
    def test_whatsapp_health_check(self, client):
        """Test WhatsApp service health check"""
        
        response = client.get("/api/v1/whatsapp/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "status" in data