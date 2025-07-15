import pytesseract
import easyocr
from PIL import Image
import cv2
import numpy as np
from google.cloud import vision
import io
import time
from typing import Dict, Any, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor
from config.settings import settings
from models.ai_models import OCRResult

class OCRService:
    def __init__(self):
        # Get file processing configuration
        self.file_config = settings.get_file_config()
        self.max_file_size = self.file_config["max_size"]
        self.allowed_types = self.file_config["allowed_types"]
        
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.easyocr_reader = easyocr.Reader(['en'])
        
        # Initialize Google Vision if API key is provided
        self.google_vision_client = None
        if settings.google_vision_api_key:
            from google.cloud import vision
            self.google_vision_client = vision.ImageAnnotatorClient()
    
    async def extract_text_from_image(self, image_path: str, method: str = "auto") -> OCRResult:
        """Extract text from image using specified OCR method"""
        start_time = time.time()
        
        if method == "auto":
            method = await self._choose_best_method(image_path)
        
        try:
            if method == "google_vision" and self.google_vision_client:
                result = await self._google_vision_ocr(image_path)
            elif method == "easyocr":
                result = await self._easyocr_extraction(image_path)
            else:  # Default to tesseract
                result = await self._tesseract_ocr(image_path)
            
            processing_time = time.time() - start_time
            
            return OCRResult(
                extracted_text=result["text"],
                confidence=result["confidence"],
                processing_time=processing_time,
                method_used=method
            )
            
        except Exception as e:
            # Fallback to tesseract if other methods fail
            if method != "tesseract":
                return await self.extract_text_from_image(image_path, "tesseract")
            else:
                raise Exception(f"All OCR methods failed: {str(e)}")
    
    async def _tesseract_ocr(self, image_path: str) -> Dict[str, Any]:
        """Extract text using Tesseract OCR"""
        def _process():
            # Load and preprocess image
            image = cv2.imread(image_path)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply preprocessing for better OCR
            gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            gray = cv2.medianBlur(gray, 3)
            
            # Extract text with confidence
            data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)
            text = pytesseract.image_to_string(gray, lang='eng')
            
            # Calculate average confidence
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            return {
                "text": text.strip(),
                "confidence": avg_confidence / 100.0
            }
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _process)
    
    async def _easyocr_extraction(self, image_path: str) -> Dict[str, Any]:
        """Extract text using EasyOCR"""
        def _process():
            results = self.easyocr_reader.readtext(image_path)
            
            text_parts = []
            confidences = []
            
            for (bbox, text, confidence) in results:
                text_parts.append(text)
                confidences.append(confidence)
            
            full_text = ' '.join(text_parts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            return {
                "text": full_text,
                "confidence": avg_confidence
            }
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _process)
    
    async def _google_vision_ocr(self, image_path: str) -> Dict[str, Any]:
        """Extract text using Google Vision API"""
        def _process():
            with io.open(image_path, 'rb') as image_file:
                content = image_file.read()
            
            image = vision.Image(content=content)
            response = self.google_vision_client.text_detection(image=image)
            texts = response.text_annotations
            
            if texts:
                full_text = texts[0].description
                # Google Vision doesn't provide confidence scores directly
                confidence = 0.9  # Assume high confidence for Google Vision
            else:
                full_text = ""
                confidence = 0.0
            
            return {
                "text": full_text,
                "confidence": confidence
            }
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _process)
    
    async def _choose_best_method(self, image_path: str) -> str:
        """Choose the best OCR method based on image characteristics"""
        # Simple heuristic: use Google Vision if available, otherwise EasyOCR for complex images
        if self.google_vision_client:
            return "google_vision"
        
        # Analyze image complexity
        image = cv2.imread(image_path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Calculate image variance (complexity measure)
        variance = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        if variance > 500:  # Complex image
            return "easyocr"
        else:  # Simple image
            return "tesseract"