import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock
import tempfile
import os
from main import app
from config.settings import settings

@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)

@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    mock = Mock()
    mock.ping.return_value = True
    mock.get.return_value = None
    mock.set.return_value = True
    return mock

@pytest.fixture
def mock_openai():
    """Mock OpenAI client"""
    mock = AsyncMock()
    mock.ChatCompletion.acreate.return_value = Mock(
        choices=[Mock(message=Mock(content='{"category": "Test", "confidence": 0.9}'))]
    )
    return mock

@pytest.fixture
def sample_pdf_file():
    """Create a sample PDF file for testing"""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        f.write(b'%PDF-1.4 sample pdf content')
        yield f.name
    os.unlink(f.name)

@pytest.fixture
def sample_image_file():
    """Create a sample image file for testing"""
    from PIL import Image
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        img = Image.new('RGB', (100, 100), color='white')
        img.save(f.name, 'JPEG')
        yield f.name
    os.unlink(f.name)

@pytest.fixture
def mock_settings():
    """Mock settings for testing"""
    test_settings = settings.copy()
    test_settings.openai_api_key = "test-key"
    test_settings.node_backend_url = "http://test-backend"
    return test_settings