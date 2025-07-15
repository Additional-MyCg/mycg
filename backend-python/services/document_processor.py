import re
import json
from typing import Dict, Any, List
import pandas as pd
from datetime import datetime
from models.ai_models import BankStatementParsing, InvoiceData, TransactionData
from typing import Optional, List, Dict, Any  # Add whatever other types you're using
class DocumentProcessor:
    def __init__(self):
        self.date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            r'\b\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4}\b',
            r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b'
        ]
        
        self.amount_patterns = [
            r'₹\s*([0-9,]+\.?[0-9]*)',
            r'Rs\.?\s*([0-9,]+\.?[0-9]*)',
            r'\b([0-9,]+\.[0-9]{2})\b',
            r'\b([0-9,]+)\b'
        ]
    
    async def parse_bank_statement(self, extracted_text: str) -> BankStatementParsing:
        """Parse bank statement text and extract transaction details"""
        
        lines = extracted_text.split('\n')
        transactions = []
        account_details = {}
        
        # Extract account details
        account_details = await self._extract_account_details(extracted_text)
        
        # Parse transactions
        for line in lines:
            line = line.strip()
            if not line or len(line) < 10:
                continue
            
            transaction = await self._parse_transaction_line(line)
            if transaction:
                transactions.append(transaction)
        
        # Calculate summary
        total_debits = sum(t.amount for t in transactions if t.transaction_type == 'debit' and t.amount)
        total_credits = sum(t.amount for t in transactions if t.transaction_type == 'credit' and t.amount)
        
        summary = {
            "total_transactions": len(transactions),
            "total_debits": total_debits,
            "total_credits": total_credits,
            "net_amount": total_credits - total_debits
        }
        
        # Calculate overall confidence
        valid_transactions = [t for t in transactions if t.amount is not None]
        parsing_confidence = len(valid_transactions) / len(transactions) if transactions else 0
        
        return BankStatementParsing(
            transactions=transactions,
            account_details=account_details,
            summary=summary,
            parsing_confidence=parsing_confidence
        )
    
    async def parse_invoice(self, extracted_text: str) -> InvoiceData:
        """Parse invoice text and extract relevant details"""
        
        invoice_data = InvoiceData(confidence=0.0)
        
        # Extract invoice number
        invoice_patterns = [
            r'invoice\s*#?\s*:?\s*(\w+)',
            r'inv\s*#?\s*:?\s*(\w+)',
            r'bill\s*#?\s*:?\s*(\w+)'
        ]
        
        for pattern in invoice_patterns:
            match = re.search(pattern, extracted_text, re.IGNORECASE)
            if match:
                invoice_data.invoice_number = match.group(1)
                break
        
        # Extract date
        invoice_data.date = self._extract_date(extracted_text)
        
        # Extract vendor details
        invoice_data.vendor_name = self._extract_vendor_name(extracted_text)
        invoice_data.vendor_gstin = self._extract_gstin(extracted_text)
        
        # Extract amounts
        amounts = self._extract_amounts(extracted_text)
        if amounts:
            invoice_data.total_amount = amounts.get('total', 0)
            invoice_data.tax_amount = amounts.get('tax', 0)
        
        # Extract line items
        invoice_data.line_items = await self._extract_line_items(extracted_text)
        
        # Calculate confidence based on extracted fields
        fields_found = sum([
            1 if invoice_data.invoice_number else 0,
            1 if invoice_data.date else 0,
            1 if invoice_data.vendor_name else 0,
            1 if invoice_data.total_amount else 0
        ])
        
        invoice_data.confidence = fields_found / 4.0
        
        return invoice_data
    
    async def _extract_account_details(self, text: str) -> Dict[str, Any]:
        """Extract account details from statement"""
        details = {}
        
        # Account number
        acc_pattern = r'account\s*no\.?\s*:?\s*(\d+)'
        match = re.search(acc_pattern, text, re.IGNORECASE)
        if match:
            details['account_number'] = match.group(1)
        
        # Bank name
        bank_patterns = [
            r'(hdfc|icici|sbi|axis|kotak|pnb|bob|canara)',
            r'([A-Z\s]+BANK)'
        ]
        
        for pattern in bank_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                details['bank_name'] = match.group(1)
                break
        
        # Statement period
        period_pattern = r'statement\s+period\s*:?\s*(.+?)(?:\n|$)'
        match = re.search(period_pattern, text, re.IGNORECASE)
        if match:
            details['statement_period'] = match.group(1).strip()
        
        return details
    
    async def _parse_transaction_line(self, line: str) -> Optional[TransactionData]:
        """Parse a single transaction line"""
        
        # Look for date pattern
        date_match = None
        for pattern in self.date_patterns:
            date_match = re.search(pattern, line)
            if date_match:
                break
        
        if not date_match:
            return None
        
        # Extract amount
        amount = self._extract_amount_from_line(line)
        if not amount:
            return None
        
        # Determine transaction type
        transaction_type = "debit" if any(word in line.lower() for word in ['dr', 'debit', 'withdrawal', 'paid']) else "credit"
        
        # Extract description (remove date and amount)
        description = line
        description = re.sub(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', '', description)
        description = re.sub(r'₹?\s*[0-9,]+\.?[0-9]*', '', description)
        description = ' '.join(description.split())
        
        # Auto-categorize
        category = self._auto_categorize_transaction(description)
        
        return TransactionData(
            date=date_match.group(),
            description=description,
            amount=amount,
            transaction_type=transaction_type,
            category=category,
            confidence=0.8 if amount and date_match else 0.5
        )
    
    def _extract_date(self, text: str) -> Optional[str]:
        """Extract date from text"""
        for pattern in self.date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group()
        return None
    
    def _extract_vendor_name(self, text: str) -> Optional[str]:
        """Extract vendor name from invoice"""
        vendor_patterns = [
            r'from\s*:?\s*([A-Za-z\s]+?)(?:\n|tax|gst)',
            r'vendor\s*:?\s*([A-Za-z\s]+?)(?:\n|$)',
            r'bill\s+to\s*:?\s*([A-Za-z\s]+?)(?:\n|$)'
        ]
        
        for pattern in vendor_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                vendor_name = match.group(1).strip()
                if len(vendor_name) > 3:
                    return vendor_name
        
        return None
    
    def _extract_gstin(self, text: str) -> Optional[str]:
        """Extract GSTIN from text"""
        gstin_pattern = r'gstin\s*:?\s*([A-Z0-9]{15})'
        match = re.search(gstin_pattern, text, re.IGNORECASE)
        return match.group(1) if match else None
    
    def _extract_amounts(self, text: str) -> Dict[str, float]:
        """Extract various amounts from invoice"""
        amounts = {}
        
        # Total amount patterns
        total_patterns = [
            r'total\s*:?\s*₹?\s*([0-9,]+\.?[0-9]*)',
            r'grand\s+total\s*:?\s*₹?\s*([0-9,]+\.?[0-9]*)',
            r'amount\s+payable\s*:?\s*₹?\s*([0-9,]+\.?[0-9]*)'
        ]
        
        for pattern in total_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amounts['total'] = float(match.group(1).replace(',', ''))
                break
        
        # Tax amount patterns
        tax_patterns = [
            r'(?:gst|tax)\s*:?\s*₹?\s*([0-9,]+\.?[0-9]*)',
            r'(?:cgst|sgst|igst)\s*:?\s*₹?\s*([0-9,]+\.?[0-9]*)'
        ]
        
        tax_amounts = []
        for pattern in tax_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                tax_amounts.append(float(match.replace(',', '')))
        
        if tax_amounts:
            amounts['tax'] = sum(tax_amounts)
        
        return amounts
    
    def _extract_amount_from_line(self, line: str) -> Optional[float]:
        """Extract amount from a single line"""
        for pattern in self.amount_patterns:
            match = re.search(pattern, line)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    return float(amount_str)
                except ValueError:
                    continue
        return None
    
    def _auto_categorize_transaction(self, description: str) -> str:
        """Auto-categorize transaction based on description"""
        description_lower = description.lower()
        
        categories = {
            'food': ['restaurant', 'food', 'cafe', 'hotel', 'dining', 'swiggy', 'zomato'],
            'fuel': ['petrol', 'diesel', 'fuel', 'gas', 'hp', 'ioc', 'bpcl'],
            'utilities': ['electricity', 'water', 'gas', 'phone', 'internet', 'broadband'],
            'transport': ['uber', 'ola', 'taxi', 'metro', 'bus', 'auto'],
            'shopping': ['amazon', 'flipkart', 'mall', 'store', 'purchase'],
            'medical': ['hospital', 'pharmacy', 'doctor', 'medical', 'clinic'],
            'education': ['school', 'college', 'university', 'course', 'training'],
            'entertainment': ['movie', 'cinema', 'netflix', 'spotify', 'game']
        }
        
        for category, keywords in categories.items():
            if any(keyword in description_lower for keyword in keywords):
                return category
        
        return 'miscellaneous'
    
    async def _extract_line_items(self, text: str) -> List[Dict[str, Any]]:
        """Extract line items from invoice"""
        # This is a simplified implementation
        # In practice, you'd need more sophisticated parsing
        lines = text.split('\n')
        line_items = []
        
        for line in lines:
            if re.search(r'\d+\.?\d*\s*₹', line):  # Line with quantity and amount
                line_items.append({
                    "description": line.strip(),
                    "quantity": 1,
                    "amount": self._extract_amount_from_line(line) or 0
                })
        
        return line_items[:10]  # Return max 10 items