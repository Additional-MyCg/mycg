import pytest
from unittest.mock import patch, Mock, AsyncMock
from services.ocr_service import OCRService

class TestOCRService:
    
    @pytest.fixture
    def ocr_service(self):
        return OCRService()
    
    @pytest.mark.asyncio
    async def test_tesseract_ocr(self, ocr_service, sample_image_file):
        """Test Tesseract OCR extraction"""
        
        with patch('pytesseract.image_to_string') as mock_tesseract, \
             patch('pytesseract.image_to_data') as mock_data:
            
            mock_tesseract.return_value = "Sample extracted text"
            mock_data.return_value = {'conf': ['90', '85', '88']}
            
            result = await ocr_service._tesseract_ocr(sample_image_file)
            
            assert result["text"] == "Sample extracted text"
            assert result["confidence"] > 0
    
    @pytest.mark.asyncio
    async def test_easyocr_extraction(self, ocr_service, sample_image_file):
        """Test EasyOCR extraction"""
        
        with patch.object(ocr_service, 'easyocr_reader') as mock_reader:
            mock_reader.readtext.return_value = [
                ([(0, 0), (100, 0), (100, 50), (0, 50)], "Sample text", 0.9),
                ([(0, 60), (150, 60), (150, 110), (0, 110)], "More text", 0.85)
            ]
            
            result = await ocr_service._easyocr_extraction(sample_image_file)
            
            assert "Sample text More text" in result["text"]
            assert result["confidence"] > 0.8
    
    @pytest.mark.asyncio
    async def test_extract_text_auto_method(self, ocr_service, sample_image_file):
        """Test automatic OCR method selection"""
        
        with patch.object(ocr_service, '_choose_best_method') as mock_choose, \
             patch.object(ocr_service, '_tesseract_ocr') as mock_tesseract:
            
            mock_choose.return_value = "tesseract"
            mock_tesseract.return_value = {"text": "Test text", "confidence": 0.9}
            
            result = await ocr_service.extract_text_from_image(sample_image_file, "auto")
            
            assert result.extracted_text == "Test text"
            assert result.method_used == "tesseract"
            assert result.confidence == 0.9
    
    @pytest.mark.asyncio
    async def test_ocr_fallback_on_error(self, ocr_service, sample_image_file):
        """Test OCR fallback when primary method fails"""
        
        with patch.object(ocr_service, '_google_vision_ocr') as mock_vision, \
             patch.object(ocr_service, '_tesseract_ocr') as mock_tesseract:
            
            # Google Vision fails
            mock_vision.side_effect = Exception("Vision API error")
            
            # Tesseract succeeds
            mock_tesseract.return_value = {"text": "Fallback text", "confidence": 0.8}
            
            result = await ocr_service.extract_text_from_image(sample_image_file, "google_vision")
            
            assert result.extracted_text == "Fallback text"
            assert result.method_used == "tesseract"