import re
from typing import Optional, List
from pydantic import validator

class Validators:
    
    @staticmethod
    def validate_phone_number(phone: str) -> bool:
        """Validate phone number format"""
        if not phone:
            return False
        
        # Remove all non-digit characters
        clean_phone = re.sub(r'\D', '', phone)
        
        # Check for Indian phone number patterns
        patterns = [
            r'^91[6-9]\d{9}$',  # +91 format
            r'^[6-9]\d{9}$',    # 10 digit format
        ]
        
        for pattern in patterns:
            if re.match(pattern, clean_phone):
                return True
        
        return False
    
    @staticmethod
    def validate_gstin(gstin: str) -> bool:
        """Validate GSTIN format"""
        if not gstin or len(gstin) != 15:
            return False
        
        # GSTIN pattern: 2 digits (state) + 10 alphanumeric + 1 digit + 1 alphabet + 1 alphanumeric
        pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z][Z0-9]$'
        return bool(re.match(pattern, gstin.upper()))
    
    @staticmethod
    def validate_file_type(filename: str, allowed_types: List[str]) -> bool:
        """Validate file type based on extension"""
        if not filename:
            return False
        
        file_extension = filename.lower().split('.')[-1]
        allowed_extensions = [ext.split('/')[-1] for ext in allowed_types]
        
        return file_extension in allowed_extensions
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe storage"""
        # Remove or replace dangerous characters
        filename = re.sub(r'[^\w\s\-_.]', '', filename)
        filename = re.sub(r'[\s]+', '_', filename)
        return filename[:100]  # Limit length
    
    @staticmethod
    def validate_amount(amount: str) -> bool:
        """Validate amount format"""
        try:
            float_amount = float(amount.replace(',', ''))
            return float_amount >= 0
        except (ValueError, AttributeError):
            return False
    
    @staticmethod
    def extract_numbers(text: str) -> List[float]:
        """Extract all numbers from text"""
        pattern = r'-?\d+\.?\d*'
        matches = re.findall(pattern, text)
        
        numbers = []
        for match in matches:
            try:
                numbers.append(float(match))
            except ValueError:
                continue
        
        return numbers