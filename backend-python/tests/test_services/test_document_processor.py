import pytest
from services.document_processor import DocumentProcessor

class TestDocumentProcessor:
    
    @pytest.fixture
    def doc_processor(self):
        return DocumentProcessor()
    
    @pytest.mark.asyncio
    async def test_parse_bank_statement(self, doc_processor):
        """Test bank statement parsing"""
        
        sample_text = """
        Account Statement
        Account Number: 1234567890
        
        Date        Description                 Amount
        01/01/2024  Opening Balance            10000.00
        02/01/2024  ATM Withdrawal Dr          2000.00
        03/01/2024  Salary Credit Cr          50000.00
        """
        
        result = await doc_processor.parse_bank_statement(sample_text)
        
        assert len(result.transactions) > 0
        assert result.summary["total_transactions"] > 0
        assert "account_number" in result.account_details
    
    @pytest.mark.asyncio
    async def test_parse_invoice(self, doc_processor):
        """Test invoice parsing"""
        
        sample_text = """
        TAX INVOICE
        Invoice No: INV-2024-001
        Date: 01/01/2024
        
        From: ABC Company
        GSTIN: 29ABCDE1234F1Z5
        
        Total Amount: Rs. 11,800.00
        GST (18%): Rs. 1,800.00
        """
        
        result = await doc_processor.parse_invoice(sample_text)
        
        assert result.invoice_number == "INV-2024-001"
        assert result.vendor_gstin == "29ABCDE1234F1Z5"
        assert result.total_amount == 11800.00
        assert result.confidence > 0
    
    def test_auto_categorize_transaction(self, doc_processor):
        """Test automatic transaction categorization"""
        
        test_cases = [
            ("Payment to Swiggy", "food"),
            ("Petrol Pump Payment", "fuel"),
            ("Electricity Bill", "utilities"),
            ("Amazon Purchase", "shopping"),
            ("Unknown Payment", "miscellaneous")
        ]
        
        for description, expected_category in test_cases:
            category = doc_processor._auto_categorize_transaction(description)
            assert category == expected_category
    
    def test_extract_amounts(self, doc_processor):
        """Test amount extraction from text"""
        
        test_text = "Total: Rs. 1,250.50 GST: Rs. 225.09"
        amounts = doc_processor._extract_amounts(test_text)
        
        assert amounts.get("total") == 1250.50
    
    def test_extract_date(self, doc_processor):
        """Test date extraction from text"""
        
        test_cases = [
            "Date: 01/01/2024",
            "Invoice Date: 1st Jan 2024",
            "2024-01-01"
        ]
        
        for text in test_cases:
            date = doc_processor._extract_date(text)
            assert date is not None