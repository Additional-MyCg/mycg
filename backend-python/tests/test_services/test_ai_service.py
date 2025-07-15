import pytest
from unittest.mock import patch, Mock, AsyncMock
from services.ai_service import AIService

class TestAIService:
    
    @pytest.fixture
    def ai_service(self):
        return AIService()
    
    @pytest.mark.asyncio
    async def test_categorize_transaction(self, ai_service):
        """Test transaction categorization"""
        
        with patch.object(ai_service, '_call_openai') as mock_openai:
            mock_openai.return_value = '{"category": "Office Supplies", "confidence": 0.9, "is_business_expense": true}'
            
            result = await ai_service.categorize_transaction("Printer purchase", 5000)
            
            assert result["category"] == "Office Supplies"
            assert result["confidence"] == 0.9
            assert result["is_business_expense"] == True
    
    @pytest.mark.asyncio
    async def test_answer_gst_query(self, ai_service):
        """Test GST query answering"""
        
        with patch.object(ai_service, '_call_openai') as mock_openai, \
             patch.object(ai_service, '_generate_follow_up_questions') as mock_followup:
            
            mock_openai.return_value = "GST rate for software services is 18%"
            mock_followup.return_value = ["What about software exports?"]
            
            result = await ai_service.answer_gst_query("What is GST rate for software?")
            
            assert "18%" in result.answer
            assert result.confidence == "high"
            assert len(result.follow_up_questions) > 0
    
    @pytest.mark.asyncio
    async def test_analyze_notice(self, ai_service):
        """Test government notice analysis"""
        
        with patch.object(ai_service, '_call_openai') as mock_openai:
            mock_response = '''{
                "urgency": "high",
                "key_points": ["Missing GSTR-1 filing"],
                "required_actions": ["File return immediately"],
                "due_date_mentioned": true,
                "extracted_due_date": "2024-01-20",
                "suggested_response": "File the return with penalty",
                "confidence": 0.9
            }'''
            mock_openai.return_value = mock_response
            
            result = await ai_service.analyze_notice("Notice text...", "gst")
            
            assert result.urgency == "high"
            assert len(result.key_points) > 0
            assert result.due_date_mentioned == True
    
    @pytest.mark.asyncio
    async def test_suggest_recurring_entries(self, ai_service):
        """Test recurring entries suggestion"""
        
        transaction_history = [
            {"date": "2023-01-01", "description": "Office Rent", "amount": 50000},
            {"date": "2023-02-01", "description": "Office Rent", "amount": 50000}
        ]
        
        with patch.object(ai_service, '_call_openai') as mock_openai:
            mock_response = '''[{
                "description": "Office Rent",
                "amount": 50000,
                "frequency": "monthly",
                "category": "Office Expenses",
                "confidence": 0.95,
                "next_due_estimate": "2024-02-01"
            }]'''
            mock_openai.return_value = mock_response
            
            result = await ai_service.suggest_recurring_entries(transaction_history)
            
            assert len(result) > 0
            assert result[0]["frequency"] == "monthly"
            assert result[0]["confidence"] > 0.9
    
    @pytest.mark.asyncio
    async def test_ai_service_error_handling(self, ai_service):
        """Test AI service error handling"""
        
        with patch.object(ai_service, '_call_openai') as mock_openai:
            mock_openai.side_effect = Exception("API Error")
            
            # Should return fallback categorization
            result = await ai_service.categorize_transaction("Test transaction", 1000)
            
            assert result["category"] == "Miscellaneous"
            assert result["confidence"] < 1.0