#!/bin/bash

echo "🚀 Setting up MyCG AI Service..."

# Create environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your API keys and configuration"
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p temp_uploads logs nginx/ssl

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Download required NLTK data (if using NLTK)
echo "📥 Downloading required AI models..."
python -c "
try:
    import nltk
    nltk.download('punkt')
    nltk.download('stopwords')
    print('✅ NLTK data downloaded')
except ImportError:
    print('⚠️  NLTK not installed, skipping...')
"

# Test Tesseract installation
echo "🔍 Testing Tesseract installation..."
if command -v tesseract &> /dev/null; then
    echo "✅ Tesseract is installed"
    tesseract --version
else
    echo "❌ Tesseract not found. Please install tesseract-ocr"
    echo "   Ubuntu/Debian: sudo apt-get install tesseract-ocr"
    echo "   macOS: brew install tesseract"
fi

# Test Redis connection
echo "🔍 Testing Redis connection..."
python -c "
import redis
try:
    r = redis.from_url('redis://localhost:6379')
    r.ping()
    print('✅ Redis connection successful')
except Exception as e:
    print(f'❌ Redis connection failed: {e}')
    print('   Make sure Redis is running: redis-server')
"

echo "✅ Setup complete!"
echo ""
echo "🚀 To start the development server:"
echo "   python main.py"
echo ""
echo "🐳 To start with Docker:"
echo "   docker-compose up -d"
echo ""
echo "📊 Health check:"
echo "   curl http://localhost:8001/api/v1/health"