# services/azure_ocr_service.py
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
import logging

logger = logging.getLogger(__name__)

class AzureOCRService:
    def __init__(self):
        # Use your Azure endpoint and key
        endpoint = "https://mycg-documentai.cognitiveservices.azure.com/"  # You need to create this
        key = "your-document-intelligence-key"  # Get from Azure portal
        
        try:
            self.client = DocumentAnalysisClient(
                endpoint=endpoint,
                credential=AzureKeyCredential(key)
            )
            self.available = True
        except Exception as e:
            logger.warning(f"Azure Document Intelligence not configured: {e}")
            self.available = False
    
    async def extract_text(self, file_path: str):
        if not self.available:
            return {"text": "Azure OCR not available", "confidence": 0}
        
        try:
            with open(file_path, "rb") as f:
                poller = self.client.begin_analyze_document(
                    "prebuilt-read", document=f
                )
                result = poller.result()
            
            text = ""
            for page in result.pages:
                for line in page.lines:
                    text += line.content + "\n"
            
            return {"text": text, "confidence": 0.9}
        except Exception as e:
            logger.error(f"Azure OCR failed: {e}")
            return {"text": "", "confidence": 0}