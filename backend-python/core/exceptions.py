from fastapi import HTTPException, status

class MyCGAIException(Exception):
    """Base exception for MyCG AI application"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class DocumentProcessingException(MyCGAIException):
    """Exception for document processing errors"""
    def __init__(self, message: str = "Document processing failed"):
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY)

class OCRException(MyCGAIException):
    """Exception for OCR processing errors"""
    def __init__(self, message: str = "OCR processing failed"):
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY)

class AIServiceException(MyCGAIException):
    """Exception for AI service errors"""
    def __init__(self, message: str = "AI service unavailable"):
        super().__init__(message, status.HTTP_503_SERVICE_UNAVAILABLE)

class WhatsAppException(MyCGAIException):
    """Exception for WhatsApp service errors"""
    def __init__(self, message: str = "WhatsApp service error"):
        super().__init__(message, status.HTTP_400_BAD_REQUEST)

class FileProcessingException(MyCGAIException):
    """Exception for file processing errors"""
    def __init__(self, message: str = "File processing failed"):
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY)

class BackendConnectionException(MyCGAIException):
    """Exception for backend connection errors"""
    def __init__(self, message: str = "Backend service unavailable"):
        super().__init__(message, status.HTTP_503_SERVICE_UNAVAILABLE)

class ValidationException(MyCGAIException):
    """Exception for validation errors"""
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, status.HTTP_400_BAD_REQUEST)