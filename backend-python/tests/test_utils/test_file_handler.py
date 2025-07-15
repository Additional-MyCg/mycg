import pytest
import tempfile
import os
from unittest.mock import patch, Mock
from utils.file_handler import FileHandler
from fastapi import UploadFile
import io

class TestFileHandler:
    
    @pytest.fixture
    def file_handler(self):
        return FileHandler()
    
    @pytest.mark.asyncio
    async def test_save_upload_file_success(self, file_handler):
        """Test successful file upload"""
        
        file_content = b"Sample PDF content"
        upload_file = UploadFile(
            filename="test.pdf",
            file=io.BytesIO(file_content),
            content_type="application/pdf"
        )
        
        with patch('magic.from_file') as mock_magic:
            mock_magic.return_value = "application/pdf"
            
            result = await file_handler.save_upload_file(upload_file, "user123")
            
            assert result["original_filename"] == "test.pdf"
            assert result["mime_type"] == "application/pdf"
            assert result["user_id"] == "user123"
            assert os.path.exists(result["file_path"])
            
            # Clean up
            os.unlink(result["file_path"])
    
    @pytest.mark.asyncio
    async def test_save_upload_file_invalid_type(self, file_handler):
        """Test file upload with invalid type"""
        
        file_content = b"Text file content"
        upload_file = UploadFile(
            filename="test.txt",
            file=io.BytesIO(file_content),
            content_type="text/plain"
        )
        
        with pytest.raises(ValueError, match="File type not allowed"):
            await file_handler.save_upload_file(upload_file)
    
    @pytest.mark.asyncio
    async def test_save_upload_file_too_large(self, file_handler):
        """Test file upload with oversized file"""
        
        # Create file larger than limit
        large_content = b"x" * (file_handler.max_file_size + 1)
        upload_file = UploadFile(
            filename="large.pdf",
            file=io.BytesIO(large_content),
            content_type="application/pdf"
        )
        
        with pytest.raises(ValueError, match="File too large"):
            await file_handler.save_upload_file(upload_file)
    
    @pytest.mark.asyncio
    async def test_convert_to_image_pdf(self, file_handler, sample_pdf_file):
        """Test PDF to image conversion"""
        
        with patch('pdf2image.convert_from_path') as mock_convert:
            # Mock PDF conversion
            mock_page = Mock()
            mock_convert.return_value = [mock_page]
            
            result = await file_handler.convert_to_image(sample_pdf_file)
            
            # Should return converted image path
            assert result.endswith('.jpg')
    
    @pytest.mark.asyncio
    async def test_convert_to_image_non_pdf(self, file_handler, sample_image_file):
        """Test image file pass-through"""
        
        result = await file_handler.convert_to_image(sample_image_file)
        
        # Should return original path for non-PDF
        assert result == sample_image_file
    
    @pytest.mark.asyncio
    async def test_upload_to_s3_success(self, file_handler, sample_pdf_file):
        """Test successful S3 upload"""
        
        with patch.object(file_handler, 's3_client') as mock_s3:
            mock_s3.upload_file.return_value = None
            
            result = await file_handler.upload_to_s3(sample_pdf_file, "test/file.pdf")
            
            assert result.startswith("https://")
            assert "test/file.pdf" in result
    
    @pytest.mark.asyncio
    async def test_upload_to_s3_no_client(self, file_handler, sample_pdf_file):
        """Test S3 upload without configured client"""
        
        file_handler.s3_client = None
        
        result = await file_handler.upload_to_s3(sample_pdf_file, "test/file.pdf")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cleanup_temp_file_success(self, file_handler):
        """Test successful file cleanup"""
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        
        # File should exist
        assert os.path.exists(temp_path)
        
        # Cleanup should succeed
        result = await file_handler.cleanup_temp_file(temp_path)
        
        assert result == True
        assert not os.path.exists(temp_path)
    
    @pytest.mark.asyncio
    async def test_cleanup_temp_file_not_exists(self, file_handler):
        """Test cleanup of non-existent file"""
        
        result = await file_handler.cleanup_temp_file("/nonexistent/file.pdf")
        
        assert result == True  # Should return True even if file doesn't exist