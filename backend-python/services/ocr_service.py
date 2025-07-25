import time
from typing import Dict, Any, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor
from config.settings import settings
from models.ai_models import OCRResult

# Lazy imports to handle dependency issues gracefully
pytesseract = None
easyocr = None
Image = None
cv2 = None
np = None
vision = None

def _safe_import():
    """Safely import dependencies with error handling"""
    global pytesseract, easyocr, Image, cv2, np, vision
    
    try:
        import pytesseract as _pytesseract
        pytesseract = _pytesseract
    except ImportError as e:
        print(f"Warning: pytesseract import failed: {e}")
    
    try:
        import easyocr as _easyocr
        easyocr = _easyocr
    except ImportError as e:
        print(f"Warning: easyocr import failed: {e}")
    
    try:
        from PIL import Image as _Image
        Image = _Image
    except ImportError as e:
        print(f"Warning: PIL import failed: {e}")
    
    try:
        import cv2 as _cv2
        cv2 = _cv2
    except ImportError as e:
        print(f"Warning: cv2 import failed: {e}")
    
    try:
        import numpy as _np
        np = _np
    except ImportError as e:
        print(f"Warning: numpy import failed: {e}")
    
    try:
        from google.cloud import vision as _vision
        vision = _vision
    except ImportError as e:
        print(f"Warning: google.cloud.vision import failed: {e}")

class OCRService:
    def __init__(self):
        # Try to import dependencies
        _safe_import()
        
        # Get file processing configuration
        self.file_config = settings.get_file_config()
        self.max_file_size = self.file_config["max_size"]
        self.allowed_types = self.file_config["allowed_types"]
        
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Initialize EasyOCR if available
        self.easyocr_reader = None
        if easyocr:
            try:
                self.easyocr_reader = easyocr.Reader(['en'])
            except Exception as e:
                print(f"Warning: EasyOCR initialization failed: {e}")
        
        # Initialize Google Vision if API key is provided
        self.google_vision_client = None
        if vision and settings.google_vision_api_key:
            try:
                self.google_vision_client = vision.ImageAnnotatorClient()
            except Exception as e:
                print(f"Warning: Google Vision client initialization failed: {e}")
    
    def _check_dependencies(self, method: str) -> bool:
        """Check if required dependencies are available for the method"""
        if method == "tesseract":
            return pytesseract is not None and cv2 is not None and np is not None
        elif method == "easyocr":
            return self.easyocr_reader is not None
        elif method == "google_vision":
            return self.google_vision_client is not None
        return False
    
    async def extract_text_from_image(self, image_path: str, method: str = "auto") -> OCRResult:
        """Extract text from image using specified OCR method"""
        start_time = time.time()
        
        # Check if any OCR method is available
        available_methods = []
        if self._check_dependencies("tesseract"):
            available_methods.append("tesseract")
        if self._check_dependencies("easyocr"):
            available_methods.append("easyocr")
        if self._check_dependencies("google_vision"):
            available_methods.append("google_vision")
        
        if not available_methods:
            return OCRResult(
                extracted_text="OCR services unavailable due to dependency issues. Please check installation.",
                confidence=0.0,
                processing_time=time.time() - start_time,
                method_used="none"
            )
        
        if method == "auto":
            method = await self._choose_best_method(image_path, available_methods)
        
        # Fallback to available method if requested method is not available
        if not self._check_dependencies(method):
            method = available_methods[0]
        
        try:
            if method == "google_vision" and self._check_dependencies("google_vision"):
                result = await self._google_vision_ocr(image_path)
            elif method == "easyocr" and self._check_dependencies("easyocr"):
                result = await self._easyocr_extraction(image_path)
            elif method == "tesseract" and self._check_dependencies("tesseract"):
                result = await self._tesseract_ocr(image_path)
            else:
                # Try any available method
                for fallback_method in available_methods:
                    try:
                        if fallback_method == "tesseract":
                            result = await self._tesseract_ocr(image_path)
                        elif fallback_method == "easyocr":
                            result = await self._easyocr_extraction(image_path)
                        elif fallback_method == "google_vision":
                            result = await self._google_vision_ocr(image_path)
                        method = fallback_method
                        break
                    except Exception as e:
                        print(f"Fallback method {fallback_method} failed: {e}")
                        continue
                else:
                    raise Exception("All available OCR methods failed")
            
            processing_time = time.time() - start_time
            
            return OCRResult(
                extracted_text=result["text"],
                confidence=result["confidence"],
                processing_time=processing_time,
                method_used=method
            )
            
        except Exception as e:
            # Return error result instead of crashing
            return OCRResult(
                extracted_text=f"OCR extraction failed: {str(e)}",
                confidence=0.0,
                processing_time=time.time() - start_time,
                method_used=method
            )
    
    async def _tesseract_ocr(self, image_path: str) -> Dict[str, Any]:
        """Extract text using Tesseract OCR"""
        if not self._check_dependencies("tesseract"):
            raise Exception("Tesseract dependencies not available")
        
        def _process():
            # Load and preprocess image
            image = cv2.imread(image_path)
            if image is None:
                raise Exception(f"Could not load image: {image_path}")
            
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
        if not self._check_dependencies("easyocr"):
            raise Exception("EasyOCR dependencies not available")
        
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
        if not self._check_dependencies("google_vision"):
            raise Exception("Google Vision dependencies not available")
        
        def _process():
            import io
            with io.open(image_path, 'rb') as image_file:
                content = image_file.read()
            
            image = vision.Image(content=content)
            response = self.google_vision_client.text_detection(image=image)
            texts = response.text_annotations
            
            if response.error.message:
                raise Exception(f"Google Vision API error: {response.error.message}")
            
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
    
    async def _choose_best_method(self, image_path: str, available_methods: list) -> str:
        """Choose the best OCR method based on image characteristics"""
        # Simple heuristic: use Google Vision if available, otherwise EasyOCR for complex images
        if "google_vision" in available_methods:
            return "google_vision"
        
        # If cv2 and np are available, analyze image complexity
        if cv2 and np and "easyocr" in available_methods and "tesseract" in available_methods:
            try:
                image = cv2.imread(image_path)
                if image is not None:
                    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                    
                    # Calculate image variance (complexity measure)
                    variance = cv2.Laplacian(gray, cv2.CV_64F).var()
                    
                    if variance > 500:  # Complex image
                        return "easyocr"
                    else:  # Simple image
                        return "tesseract"
            except Exception:
                pass
        
        # Return first available method as fallback
        return available_methods[0] if available_methods else "tesseract"