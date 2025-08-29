import os
import aiofiles
from typing import Optional, Dict
import uuid
from fastapi import UploadFile
from PIL import Image
from config.settings import settings
import asyncio
import logging

logger = logging.getLogger(__name__)

# With:
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    import mimetypes  # Fallback
    
class FileHandler:
    def __init__(self):
        self.upload_dir = "temp_uploads"
        
        # Use file configuration from settings
        file_config = settings.get_file_config()
        self.max_file_size = file_config["max_size"]
        self.allowed_types = set(file_config["allowed_types"])
        self.retention_hours = file_config["retention_hours"]
        
        # Azure Blob Storage client configuration
        self.blob_service_client = None
        self.container_client = None
        
        if settings.azure_storage_account:
            self._init_azure_client()
    
    def _init_azure_client(self):
        """Initialize Azure Blob Storage client"""
        try:
            from azure.storage.blob import BlobServiceClient
            
            azure_config = settings.get_azure_config()
            
            # Initialize with connection string or account key
            if azure_config["connection_string"]:
                self.blob_service_client = BlobServiceClient.from_connection_string(
                    azure_config["connection_string"]
                )
            elif azure_config["account_name"] and azure_config["account_key"]:
                account_url = f"https://{azure_config['account_name']}.blob.core.windows.net"
                if azure_config["endpoint"]:
                    account_url = azure_config["endpoint"]
                
                self.blob_service_client = BlobServiceClient(
                    account_url=account_url,
                    credential=azure_config["account_key"]
                )
            
            if self.blob_service_client:
                self.container_client = self.blob_service_client.get_container_client(
                    azure_config["container_name"]
                )
                logger.info(f"Azure Blob Storage initialized: {azure_config['container_name']}")
                
        except Exception as e:
            logger.error(f"Failed to initialize Azure Blob Storage: {e}")
            self.blob_service_client = None
            self.container_client = None
    
    async def save_upload_file(self, upload_file: UploadFile, user_id: str = None) -> Dict[str, any]:
        """Save uploaded file temporarily for processing"""
        
        # Validate file
        await self._validate_file(upload_file)
        
        # Generate unique filename
        file_extension = os.path.splitext(upload_file.filename)[1]
        unique_filename = f"{user_id or 'temp'}_{uuid.uuid4()}{file_extension}"
        
        # Create upload directory if not exists
        os.makedirs(self.upload_dir, exist_ok=True)
        file_path = os.path.join(self.upload_dir, unique_filename)
        
        # Save file locally for processing
        async with aiofiles.open(file_path, 'wb') as f:
            content = await upload_file.read()
            await f.write(content)
        
        # Get file type
        try:
            if MAGIC_AVAILABLE:
                file_type = magic.from_file(file_path, mime=True)
            else:
                file_type = upload_file.content_type or mimetypes.guess_type(file_path)[0]
        except:
            file_type = upload_file.content_type
        
        return {
            "filename": unique_filename,
            "original_filename": upload_file.filename,
            "file_path": file_path,
            "file_size": len(content),
            "mime_type": file_type,
            "user_id": user_id
        }
    
    async def upload_to_azure(self, file_path: str, blob_name: str) -> Optional[str]:
        """Upload file to Azure Blob Storage and return URL"""
        if not self.container_client:
            logger.warning("Azure Blob Storage not configured")
            return None
        
        try:
            # Upload file to Azure Blob Storage
            with open(file_path, 'rb') as data:
                blob_client = self.container_client.get_blob_client(blob_name)
                blob_client.upload_blob(data, overwrite=True)
            
            # Generate URL
            azure_config = settings.get_azure_config()
            if azure_config["endpoint"]:
                blob_url = f"{azure_config['endpoint']}/{azure_config['container_name']}/{blob_name}"
            else:
                blob_url = f"https://{azure_config['account_name']}.blob.core.windows.net/{azure_config['container_name']}/{blob_name}"
            
            logger.info(f"File uploaded to Azure: {blob_name}")
            return blob_url
            
        except Exception as e:
            logger.error(f"Azure upload failed: {e}")
            return None
    
    async def download_from_azure(self, blob_name: str, local_path: str) -> bool:
        """Download file from Azure Blob Storage"""
        if not self.container_client:
            return False
        
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            
            with open(local_path, 'wb') as download_file:
                blob_data = blob_client.download_blob()
                download_file.write(blob_data.readall())
            
            logger.info(f"File downloaded from Azure: {blob_name}")
            return True
            
        except Exception as e:
            logger.error(f"Azure download failed: {e}")
            return False
    
    async def delete_from_azure(self, blob_name: str) -> bool:
        """Delete file from Azure Blob Storage"""
        if not self.container_client:
            return False
        
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            blob_client.delete_blob()
            
            logger.info(f"File deleted from Azure: {blob_name}")
            return True
            
        except Exception as e:
            logger.error(f"Azure delete failed: {e}")
            return False
    
    async def cleanup_temp_file(self, file_path: str) -> bool:
        """Delete temporary file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            return True
        except Exception as e:
            logger.error(f"File cleanup failed: {e}")
            return False
    
    async def convert_to_image(self, file_path: str) -> str:
        """Convert PDF to image for OCR processing"""
        if file_path.lower().endswith('.pdf'):
            try:
                from pdf2image import convert_from_path
                pages = convert_from_path(file_path, first_page=1, last_page=1)
                if pages:
                    image_path = file_path.replace('.pdf', '_page1.jpg')
                    pages[0].save(image_path, 'JPEG')
                    return image_path
            except Exception as e:
                logger.error(f"PDF conversion failed: {e}")
        
        return file_path  # Return original if not PDF or conversion failed
    
    async def _validate_file(self, upload_file: UploadFile) -> None:
        """Validate uploaded file"""
        
        # Check file size
        content = await upload_file.read()
        if len(content) > self.max_file_size:
            raise ValueError(f"File too large. Maximum size: {self.max_file_size/1024/1024}MB")
        
        # Reset file pointer
        await upload_file.seek(0)
        
        # Check MIME type
        if upload_file.content_type not in self.allowed_types:
            raise ValueError(f"File type not allowed: {upload_file.content_type}")
    
    async def create_azure_container_if_not_exists(self) -> bool:
        """Create Azure container if it doesn't exist"""
        if not self.blob_service_client:
            return False
        
        try:
            azure_config = settings.get_azure_config()
            container_name = azure_config["container_name"]
            
            # Create container if it doesn't exist
            container_client = self.blob_service_client.get_container_client(container_name)
            
            if not container_client.exists():
                container_client.create_container(public_access="blob")
                logger.info(f"Created Azure container: {container_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create Azure container: {e}")
            return False