FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    libmagic1 \
    poppler-utils \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgeos-dev \
    curl \
    gcc \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Set pip configurations
ENV PIP_DEFAULT_TIMEOUT=1000
ENV PIP_RETRIES=5
ENV PIP_TIMEOUT=1000

# Upgrade pip first
RUN pip install --upgrade pip

# Copy requirements
COPY requirements.txt .

# NUCLEAR APPROACH: Install everything in one go with specific compatible versions
# This ensures all packages are resolved together for compatibility
RUN pip install --no-cache-dir --timeout=1000 \
    # Core data science stack - MUST be installed together
    "numpy==1.24.3" \
    "pandas==2.1.4" \
    "scipy==1.11.4" \
    # Web framework
    "fastapi==0.104.1" \
    "uvicorn[standard]==0.24.0" \
    "pydantic>=2.5.2" \
    "pydantic-settings==2.1.0" \
    "python-multipart==0.0.6" \
    "aiofiles==23.2.0" \
    "redis==5.0.1" \
    "python-dotenv==1.0.0" \
    "python-jose[cryptography]==3.3.0" \
    "bcrypt==4.1.1" \
    "httpx==0.25.2" \
    "watchdog==3.0.0" \
    # Image processing
    "pillow==10.3.0" \
    "opencv-python==4.8.1.78" \
    # Document processing
    "pytesseract==0.3.10" \
    "pdf2image==1.16.3" \
    "PyPDF2==3.0.1" \
    "python-magic==0.4.27" \
    # ML libraries (compatible with numpy/pandas above)
    "scikit-learn==1.3.0" \
    # API clients
    "openai==1.3.7" \
    "anthropic==0.7.8" \
    "twilio==8.10.0" \
    "google-cloud-vision==3.4.5" \
    # Task queue
    "celery==5.3.4" \
    # Cloud services
    "azure-storage-blob==12.19.0" \
    "azure-identity==1.15.0" \
    "azure-core==1.29.5" \
    # System utilities
    "psutil==5.9.6"

# Install PyTorch separately (it has its own numpy dependencies)
RUN pip install --no-cache-dir --timeout=1000 --retries=5 \
    "torch==2.1.0" \
    "torchvision>=0.5" \
    --index-url https://download.pytorch.org/whl/cpu || \
    pip install --no-cache-dir --timeout=1000 --retries=5 \
    "torch==2.1.0" \
    "torchvision>=0.5"

# Install transformers (depends on torch)
RUN pip install --no-cache-dir --timeout=1000 --retries=5 "transformers==4.35.0"

# Try to install EasyOCR, but don't fail if it doesn't work
RUN pip install --no-cache-dir --timeout=1000 --retries=3 "easyocr==1.7.0" || \
    echo "EasyOCR installation failed - will be handled gracefully"

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p temp_uploads logs

# Create non-root user
RUN useradd -m -u 1000 mycg && chown -R mycg:mycg /app
USER mycg

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/api/v1/health || exit 1

# Run with single worker for now
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1"]