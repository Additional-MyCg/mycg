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