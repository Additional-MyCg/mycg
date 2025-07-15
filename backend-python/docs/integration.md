# ==============================================
# Complete test_file_handler.py (continued)
# ==============================================

    @pytest.mark.asyncio
    async def test_cleanup_temp_file_not_exists(self, file_handler):
        """Test cleanup of non-existent file"""
        
        result = await file_handler.cleanup_temp_file("/nonexistent/file.pdf")
        
        assert result == True  # Should return True even if file doesn't exist

# ==============================================
# DOCUMENTATION FILES
# ==============================================

# docs/api.md
# MyCG AI Service - API Documentation

## Overview

The MyCG AI Service provides REST APIs for document processing, AI-powered analysis, and WhatsApp integration for accounting and GST compliance.

**Base URL**: `http://localhost:8001` (development) / `https://api.mycg.app` (production)

## Authentication

All API endpoints require authentication via API key in the header:

```bash
Authorization: Bearer your-api-key-here
```

## Document Processing APIs

### Upload Document for Processing

Process documents (bank statements, invoices, notices) with OCR and AI analysis.

**Endpoint**: `POST /api/v1/document/process`

**Content-Type**: `multipart/form-data`

**Parameters**:
- `file` (file, required): Document file (PDF, JPEG, PNG)
- `user_id` (string, required): User identifier
- `document_type` (string, optional): Document type (`auto`, `bank_statement`, `invoice`, `gst_notice`)
- `ocr_method` (string, optional): OCR method (`auto`, `tesseract`, `easyocr`, `google_vision`)

**Example Request**:
```bash
curl -X POST "http://localhost:8001/api/v1/document/process" \
  -H "Authorization: Bearer your-api-key" \
  -F "file=@bank_statement.pdf" \
  -F "user_id=user_123" \
  -F "document_type=bank_statement"
```

**Response**:
```json
{
  "message": "Document uploaded successfully",
  "processing_id": "user_123_uuid",
  "status": "processing",
  "estimated_time": "1-2 minutes"
}
```

### Get Processing Status

Check the status of document processing.

**Endpoint**: `GET /api/v1/document/status/{processing_id}`

**Example**:
```bash
curl "http://localhost:8001/api/v1/document/status/user_123_uuid" \
  -H "Authorization: Bearer your-api-key"
```

**Response**:
```json
{
  "processing_id": "user_123_uuid",
  "status": "completed",
  "message": "Check your Node.js backend for results"
}
```

## AI Services APIs

### Ask AI Question

Get answers to GST, tax, and compliance questions.

**Endpoint**: `POST /api/v1/ai/query`

**Content-Type**: `application/json`

**Request Body**:
```json
{
  "query": "What is the GST rate for software services?",
  "context": "Optional context",
  "user_id": "user_123",
  "query_type": "gst"
}
```

**Example**:
```bash
curl -X POST "http://localhost:8001/api/v1/ai/query" \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the GST rate for software services?",
    "user_id": "user_123",
    "query_type": "gst"
  }'
```

**Response**:
```json
{
  "answer": "The GST rate for software services is 18%. This applies to software development, maintenance, and support services provided by businesses.",
  "confidence": "high",
  "sources": ["GST Act", "AI Analysis"],
  "follow_up_questions": [
    "What about export of software services?",
    "Are there any exemptions for software services?"
  ],
  "query_id": "gst_1234"
}
```

### Analyze Government Notice

Analyze government notices and get actionable insights.

**Endpoint**: `POST /api/v1/ai/analyze-notice`

**Request Body**:
```json
{
  "notice_text": "Your GSTR-1 for October 2023 is pending...",
  "notice_type": "gst",
  "user_id": "user_123"
}
```

**Response**:
```json
{
  "notice_type": "gst",
  "urgency": "high",
  "key_points": [
    "Missing GSTR-1 filing for October 2023",
    "Late fee applicable"
  ],
  "required_actions": [
    "File GSTR-1 immediately",
    "Pay applicable late fees"
  ],
  "due_date_mentioned": true,
  "extracted_due_date": "2024-01-20",
  "suggested_response": "File the return immediately with applicable late fees to avoid further penalties",
  "confidence": 0.9
}
```

### Generate Notice Reply

Generate a reply draft for government notices.

**Endpoint**: `POST /api/v1/ai/generate-reply/{notice_id}`

**Request Body**: Notice analysis object

**Response**:
```json
{
  "notice_id": "notice_123",
  "reply_draft": "Dear Sir/Madam,\n\nWe acknowledge receipt of your notice dated...",
  "status": "generated"
}
```

### Suggest Recurring Entries

Get AI-powered suggestions for recurring transactions.

**Endpoint**: `POST /api/v1/ai/suggest-recurring`

**Parameters**:
- `user_id` (string, required): User identifier
- `transaction_limit` (integer, optional): Number of transactions to analyze (default: 50)

**Response**:
```json
{
  "user_id": "user_123",
  "suggestions": [
    {
      "description": "Office Rent",
      "amount": 50000,
      "frequency": "monthly",
      "category": "Office Expenses",
      "confidence": 0.95,
      "next_due_estimate": "2024-02-01"
    }
  ],
  "count": 1
}
```

## WhatsApp APIs

### Webhook Endpoint

Handle incoming WhatsApp messages (configured with Twilio).

**Endpoint**: `POST /api/v1/whatsapp/webhook`

**Content-Type**: `application/x-www-form-urlencoded`

This endpoint is automatically called by Twilio when messages are received.

### Send Message

Send WhatsApp message programmatically.

**Endpoint**: `POST /api/v1/whatsapp/send-message`

**Parameters**:
- `to_number` (string): Recipient phone number
- `message` (string): Message text

**Example**:
```bash
curl -X POST "http://localhost:8001/api/v1/whatsapp/send-message" \
  -H "Authorization: Bearer your-api-key" \
  -d "to_number=+1234567890&message=Hello from MyCG!"
```

### Send Notification

Send formatted notifications via WhatsApp.

**Endpoint**: `POST /api/v1/whatsapp/send-notification`

**Request Body**:
```json
{
  "to_number": "+1234567890",
  "notification_type": "gst_reminder",
  "data": {
    "due_date": "2024-01-20",
    "business_name": "ABC Company"
  }
}
```

**Notification Types**:
- `gst_reminder`: GST filing reminders
- `document_processed`: Document processing completion
- `compliance_alert`: Compliance alerts

## Health Check APIs

### Basic Health Check

**Endpoint**: `GET /api/v1/health`

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "service": "MyCG AI Service",
  "version": "1.0.0",
  "uptime": "2:15:30"
}
```

### Detailed Health Check

**Endpoint**: `GET /api/v1/health/detailed`

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "dependencies": {
    "redis": {"status": "healthy", "response_time_ms": 5.2},
    "node_backend": {"status": "healthy", "response_time_ms": 150.3}
  },
  "system": {
    "cpu_percent": 15.3,
    "memory_percent": 45.2,
    "disk_percent": 60.1
  },
  "ai_services": {
    "openai": {"status": "healthy"},
    "google_vision": {"status": "configured"}
  }
}
```

## Error Responses

All API endpoints return errors in a consistent format:

```json
{
  "success": false,
  "error": "Error description",
  "error_type": "ValidationException",
  "request_id": "req_abc123",
  "path": "/api/v1/document/process"
}
```

**Common HTTP Status Codes**:
- `400`: Bad Request (invalid input)
- `401`: Unauthorized (missing/invalid API key)
- `422`: Unprocessable Entity (file processing error)
- `429`: Too Many Requests (rate limit exceeded)
- `500`: Internal Server Error
- `503`: Service Unavailable (AI services down)

## Rate Limits

- General API: 10 requests/second
- WhatsApp webhook: 50 requests/second
- Document upload: 10 requests/second per user

## WebSocket Support

Real-time updates for document processing status:

```javascript
const ws = new WebSocket('ws://localhost:8001/ws/processing/{processing_id}');
ws.onmessage = (event) => {
  const status = JSON.parse(event.data);
  console.log('Processing status:', status);
};
```

---

# docs/deployment.md

# MyCG AI Service - Deployment Guide

## Prerequisites

### System Requirements

**Minimum Requirements**:
- CPU: 2 cores
- RAM: 4GB
- Storage: 20GB
- OS: Ubuntu 20.04+ / CentOS 8+ / Amazon Linux 2

**Recommended for Production**:
- CPU: 4+ cores
- RAM: 8GB+
- Storage: 50GB+ SSD
- OS: Ubuntu 22.04 LTS

### Dependencies

**System Packages**:
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y \
  python3.11 python3.11-venv python3-pip \
  tesseract-ocr tesseract-ocr-eng \
  libmagic1 poppler-utils \
  redis-server nginx \
  docker.io docker-compose

# CentOS/RHEL
sudo yum install -y \
  python311 python3-pip \
  tesseract tesseract-langpack-eng \
  file-libs poppler-utils \
  redis nginx \
  docker docker-compose
```

**Python Version**: 3.11+
**Node.js Version**: 18+ (for backend integration)

## Deployment Options

### Option 1: Docker Deployment (Recommended)

**1. Clone Repository**:
```bash
git clone 
cd mycg-ai
```

**2. Environment Setup**:
```bash
cp .env.example .env
# Edit .env with your configuration
nano .env
```

**3. Deploy with Docker**:
```bash
chmod +x scripts/*.sh
./scripts/deploy.sh
```

**4. Verify Deployment**:
```bash
curl http://localhost:8001/api/v1/health
```

### Option 2: Manual Deployment

**1. System Setup**:
```bash
# Create application user
sudo useradd -m -s /bin/bash mycg
sudo usermod -aG docker mycg

# Create application directory
sudo mkdir -p /opt/mycg-ai
sudo chown mycg:mycg /opt/mycg-ai
```

**2. Application Setup**:
```bash
# Switch to application user
sudo su - mycg
cd /opt/mycg-ai

# Clone and setup
git clone  .
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**3. Configuration**:
```bash
# Environment variables
cp .env.example .env
nano .env

# Create directories
mkdir -p temp_uploads logs
```

**4. Service Configuration**:
```bash
# Create systemd service
sudo tee /etc/systemd/system/mycg-ai.service << EOF
[Unit]
Description=MyCG AI Service
After=network.target redis.service

[Service]
Type=exec
User=mycg
Group=mycg
WorkingDirectory=/opt/mycg-ai
Environment=PATH=/opt/mycg-ai/venv/bin
ExecStart=/opt/mycg-ai/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8001 --workers 4
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable mycg-ai
sudo systemctl start mycg-ai
```

### Option 3: Kubernetes Deployment

**1. Create Namespace**:
```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: mycg-ai
```

**2. ConfigMap for Environment**:
```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: mycg-ai-config
  namespace: mycg-ai
data:
  ENVIRONMENT: "production"
  DEBUG: "false"
  REDIS_URL: "redis://redis-service:6379"
```

**3. Deployment**:
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mycg-ai
  namespace: mycg-ai
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mycg-ai
  template:
    metadata:
      labels:
        app: mycg-ai
    spec:
      containers:
      - name: mycg-ai
        image: mycg-ai:latest
        ports:
        - containerPort: 8001
        envFrom:
        - configMapRef:
            name: mycg-ai-config
        - secretRef:
            name: mycg-ai-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/v1/health
            port: 8001
          initialDelaySeconds: 5
          periodSeconds: 5
```

**4. Service**:
```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: mycg-ai-service
  namespace: mycg-ai
spec:
  selector:
    app: mycg-ai
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8001
  type: LoadBalancer
```

## Environment Configuration

### Required Environment Variables

```bash
# AI Services
OPENAI_API_KEY=sk-...
GOOGLE_VISION_API_KEY=...

# WhatsApp (Twilio)
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
WHATSAPP_NUMBER=+14155238886

# Backend Integration
NODE_BACKEND_URL=https://api.mycg.app
NODE_BACKEND_API_KEY=...

# Infrastructure
REDIS_URL=redis://localhost:6379
```

### Optional Configuration

```bash
# File Storage
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
S3_BUCKET_NAME=mycg-documents

# Security
SECRET_KEY=your-secret-key
ALLOWED_ORIGINS=https://mycg.app,https://app.mycg.app

# Performance
MAX_WORKERS=4
MAX_FILE_SIZE=10485760
```

## SSL/TLS Configuration

### Let's Encrypt with Certbot

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d api.mycg.app

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Custom SSL Certificate

```bash
# Copy certificates
sudo mkdir -p /etc/nginx/ssl
sudo cp your-cert.pem /etc/nginx/ssl/cert.pem
sudo cp your-key.pem /etc/nginx/ssl/key.pem
sudo chmod 600 /etc/nginx/ssl/key.pem
```

## Load Balancing

### Nginx Configuration

```nginx
# /etc/nginx/sites-available/mycg-ai
upstream mycg_ai_backend {
    least_conn;
    server 127.0.0.1:8001 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8002 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8003 max_fails=3 fail_timeout=30s;
}

server {
    listen 443 ssl http2;
    server_name api.mycg.app;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    location /api/ {
        proxy_pass http://mycg_ai_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Health check
        proxy_next_upstream error timeout invalid_header http_500 http_502 http_503;
        proxy_connect_timeout 5s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

### Multiple Instance Setup

```bash
# Start multiple instances
uvicorn main:app --host 0.0.0.0 --port 8001 --workers 2 &
uvicorn main:app --host 0.0.0.0 --port 8002 --workers 2 &
uvicorn main:app --host 0.0.0.0 --port 8003 --workers 2 &
```

## Monitoring & Logging

### Application Logs

```bash
# View real-time logs
tail -f /opt/mycg-ai/logs/app.log

# Docker logs
docker-compose logs -f mycg-ai

# Systemd logs
sudo journalctl -u mycg-ai -f
```

### Health Monitoring

```bash
# Create health check script
sudo tee /usr/local/bin/mycg-health-check.sh << 'EOF'
#!/bin/bash
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/api/v1/health)
if [ "$response" != "200" ]; then
    echo "Health check failed: $response"
    # Restart service
    systemctl restart mycg-ai
    # Send alert
    curl -X POST "https://hooks.slack.com/..." -d "{'text':'MyCG AI service unhealthy'}"
fi
EOF

chmod +x /usr/local/bin/mycg-health-check.sh

# Add to crontab
echo "*/5 * * * * /usr/local/bin/mycg-health-check.sh" | sudo crontab -
```

### Resource Monitoring

```bash
# Install monitoring tools
sudo apt-get install htop iotop

# Create resource monitoring script
sudo tee /usr/local/bin/mycg-monitor.sh << 'EOF'
#!/bin/bash
echo "=== $(date) ==="
echo "CPU Usage: $(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1"%"}')"
echo "Memory Usage: $(free | grep Mem | awk '{printf "%.1f%%", $3/$2 * 100.0}')"
echo "Disk Usage: $(df -h / | awk 'NR==2 {print $5}')"
echo "Active Connections: $(netstat -an | grep :8001 | grep ESTABLISHED | wc -l)"
EOF

chmod +x /usr/local/bin/mycg-monitor.sh
```

## Backup Strategy

### Automated Backup

```bash
# Daily backup script
sudo tee /usr/local/bin/mycg-daily-backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d)
BACKUP_DIR="/backup/mycg-ai/$DATE"

mkdir -p "$BACKUP_DIR"

# Backup application
tar -czf "$BACKUP_DIR/app.tar.gz" -C /opt/mycg-ai .

# Backup Redis
redis-cli BGSAVE
cp /var/lib/redis/dump.rdb "$BACKUP_DIR/"

# Backup logs
tar -czf "$BACKUP_DIR/logs.tar.gz" -C /opt/mycg-ai/logs .

# Backup configuration
cp /opt/mycg-ai/.env "$BACKUP_DIR/"

# Cleanup old backups (keep 30 days)
find /backup/mycg-ai -type d -mtime +30 -exec rm -rf {} \;

echo "Backup completed: $BACKUP_DIR"
EOF

chmod +x /usr/local/bin/mycg-daily-backup.sh

# Add to crontab (daily at 2 AM)
echo "0 2 * * * /usr/local/bin/mycg-daily-backup.sh" | sudo crontab -
```

## Security Hardening

### Firewall Configuration

```bash
# UFW (Ubuntu)
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow from 10.0.0.0/8 to any port 8001  # Internal network only
sudo ufw enable

# iptables
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8001 -s 10.0.0.0/8 -j ACCEPT
sudo iptables -A INPUT -j DROP
```

### Application Security

```bash
# Restrict file permissions
sudo chmod 600 /opt/mycg-ai/.env
sudo chmod 755 /opt/mycg-ai/logs
sudo chmod 755 /opt/mycg-ai/temp_uploads

# SELinux (if enabled)
sudo setsebool -P httpd_can_network_connect 1
sudo semanage port -a -t http_port_t -p tcp 8001
```

## Troubleshooting

### Common Issues

**Service Won't Start**:
```bash
# Check logs
sudo journalctl -u mycg-ai --no-pager -l

# Check port availability
sudo netstat -tlnp | grep :8001

# Check Python dependencies
source /opt/mycg-ai/venv/bin/activate
pip check
```

**High Memory Usage**:
```bash
# Reduce workers
# Edit /etc/systemd/system/mycg-ai.service
ExecStart=/opt/mycg-ai/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8001 --workers 2

# Restart service
sudo systemctl daemon-reload
sudo systemctl restart mycg-ai
```

**OCR Not Working**:
```bash
# Test Tesseract
tesseract --version

# Install language packs
sudo apt-get install tesseract-ocr-eng

# Check file permissions
ls -la /opt/mycg-ai/temp_uploads
```

### Performance Tuning

**Optimize for High Load**:
```bash
# Increase file descriptors
echo "mycg soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "mycg hard nofile 65536" | sudo tee -a /etc/security/limits.conf

# Optimize Redis
sudo tee -a /etc/redis/redis.conf << EOF
maxmemory 1gb
maxmemory-policy allkeys-lru
save ""
EOF

# Restart services
sudo systemctl restart redis
sudo systemctl restart mycg-ai
```

## Scaling Considerations

### Horizontal Scaling

1. **Load Balancer**: Use nginx, HAProxy, or cloud load balancers
2. **Shared Storage**: Use S3 or shared filesystem for temp files
3. **Redis Cluster**: Scale Redis for high availability
4. **Container Orchestration**: Use Kubernetes or Docker Swarm

### Vertical Scaling

1. **CPU**: 4+ cores for high OCR load
2. **Memory**: 8GB+ for AI model caching
3. **Storage**: SSD for temp file processing
4. **Network**: High bandwidth for document uploads

---

# docs/integration.md

# MyCG AI Service - Node.js Integration Guide

## Overview

This guide explains how to integrate the MyCG AI Service with your Node.js backend application. The AI service is designed to be stateless and communicates with your Node.js backend via REST APIs.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Node.js       │    │   FastAPI       │
│   (React/Vue)   │────│   Backend       │────│   AI Service    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                        │
                              ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   PostgreSQL/   │    │   Redis +       │
                       │   MongoDB       │    │   Temp Storage  │
                       └─────────────────┘    └─────────────────┘
```

## Node.js Backend Setup

### 1. Install Dependencies

```bash
npm install axios multer express-rate-limit helmet cors dotenv
```

### 2. Environment Configuration

```javascript
// config/ai-service.js
const AI_SERVICE_CONFIG = {
  baseURL: process.env.AI_SERVICE_URL || 'http://localhost:8001',
  apiKey: process.env.AI_SERVICE_API_KEY,
  timeout: 30000,
  retries: 3
};

module.exports = AI_SERVICE_CONFIG;
```

### 3. AI Service Client

```javascript
// services/aiServiceClient.js
const axios = require('axios');
const config = require('../config/ai-service');

class AIServiceClient {
  constructor() {
    this.client = axios.create({
      baseURL: config.baseURL,
      timeout: config.timeout,
      headers: {
        'Authorization': `Bearer ${config.apiKey}`,
        'Content-Type': 'application/json'
      }
    });

    // Add request/response interceptors
    this.setupInterceptors();
  }

  setupInterceptors() {
    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        console.log(`AI Service Request: ${config.method.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 503 && error.config.retries > 0) {
          error.config.retries--;
          await new Promise(resolve => setTimeout(resolve, 1000));
          return this.client.request(error.config);
        }
        return Promise.reject(error);
      }
    );
  }

  // Document processing
  async processDocument(file, userId, documentType = 'auto') {
    const formData = new FormData();
    formData.append('file', file.buffer, file.originalname);
    formData.append('user_id', userId);
    formData.append('document_type', documentType);

    try {
      const response = await this.client.post('/api/v1/document/process', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      return response.data;
    } catch (error) {
      throw new Error(`Document processing failed: ${error.message}`);
    }
  }

  // AI query
  async askAIQuestion(query, userId, context = '', queryType = 'general') {
    try {
      const response = await this.client.post('/api/v1/ai/query', {
        query,
        user_id: userId,
        context,
        query_type: queryType
      });
      return response.data;
    } catch (error) {
      throw new Error(`AI query failed: ${error.message}`);
    }
  }

  // Notice analysis
  async analyzeNotice(noticeText, noticeType, userId) {
    try {
      const response = await this.client.post('/api/v1/ai/analyze-notice', {
        notice_text: noticeText,
        notice_type: noticeType,
        user_id: userId
      });
      return response.data;
    } catch (error) {
      throw new Error(`Notice analysis failed: ${error.message}`);
    }
  }

  // WhatsApp messaging
  async sendWhatsAppMessage(toNumber, message) {
    try {
      const response = await this.client.post('/api/v1/whatsapp/send-message', null, {
        params: { to_number: toNumber, message }
      });
      return response.data;
    } catch (error) {
      throw new Error(`WhatsApp message failed: ${error.message}`);
    }
  }

  // Health check
  async checkHealth() {
    try {
      const response = await this.client.get('/api/v1/health');
      return response.data;
    } catch (error) {
      return { status: 'unhealthy', error: error.message };
    }
  }
}

module.exports = new AIServiceClient();
```

## API Integration Patterns

### 1. Document Upload & Processing

```javascript
// ==============================================
// Node.js Integration Guide (Continued)
// ==============================================

// routes/documents.js
const express = require('express');
const multer = require('multer');
const aiService = require('../services/aiServiceClient');
const Document = require('../models/Document');

const router = express.Router();
const upload = multer({ 
  limits: { fileSize: 10 * 1024 * 1024 }, // 10MB
  fileFilter: (req, file, cb) => {
    const allowedTypes = ['application/pdf', 'image/jpeg', 'image/png'];
    cb(null, allowedTypes.includes(file.mimetype));
  }
});

// Upload document for processing
router.post('/upload', upload.single('document'), async (req, res) => {
  try {
    const { userId, documentType } = req.body;
    const file = req.file;

    if (!file) {
      return res.status(400).json({ error: 'No file uploaded' });
    }

    // Create document record
    const document = await Document.create({
      userId,
      filename: file.originalname,
      fileSize: file.size,
      mimeType: file.mimetype,
      documentType: documentType || 'auto',
      status: 'processing'
    });

    // Send to AI service for processing
    const aiResponse = await aiService.processDocument(file, userId, documentType);

    // Update document with processing ID
    await document.update({
      processingId: aiResponse.processing_id,
      aiStatus: 'processing'
    });

    res.json({
      success: true,
      documentId: document.id,
      processingId: aiResponse.processing_id,
      estimatedTime: aiResponse.estimated_time
    });

  } catch (error) {
    console.error('Document upload error:', error);
    res.status(500).json({ error: error.message });
  }
});

// Webhook to receive AI processing results
router.post('/ai-processed', async (req, res) => {
  try {
    const { user_id, results } = req.body;

    if (results.success) {
      const { data } = results;
      
      // Find document by processing info
      const document = await Document.findOne({
        where: { userId: user_id, status: 'processing' }
      });

      if (document) {
        // Update document with AI results
        await document.update({
          status: 'completed',
          aiStatus: 'completed',
          extractedText: data.ocr_result?.extracted_text,
          aiInsights: data.enhanced_data,
          processingTime: data.ocr_result?.processing_time
        });

        // Create ledger entries if bank statement
        if (data.document_type === 'bank_statement' && data.enhanced_data) {
          await createLedgerEntries(user_id, data.enhanced_data.enhanced_transactions);
        }

        // Notify user
        await notifyUser(user_id, 'document_processed', {
          documentId: document.id,
          transactionCount: data.enhanced_data?.enhanced_transactions?.length || 0
        });
      }
    } else {
      // Handle processing error
      await Document.update(
        { status: 'failed', aiStatus: 'failed', errorMessage: results.error },
        { where: { userId: user_id, status: 'processing' } }
      );
    }

    res.json({ success: true });
  } catch (error) {
    console.error('AI processing webhook error:', error);
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;

// ==============================================
// 2. AI Chat Integration
// ==============================================

// routes/ai-chat.js
const express = require('express');
const aiService = require('../services/aiServiceClient');
const AIQuery = require('../models/AIQuery');

const router = express.Router();

// Ask AI question
router.post('/query', async (req, res) => {
  try {
    const { query, userId, context, queryType = 'general' } = req.body;

    // Validate input
    if (!query || !userId) {
      return res.status(400).json({ error: 'Query and userId are required' });
    }

    // Get AI response
    const aiResponse = await aiService.askAIQuestion(query, userId, context, queryType);

    // Log query for analytics
    await AIQuery.create({
      userId,
      query,
      queryType,
      response: aiResponse.answer,
      confidence: aiResponse.confidence,
      queryId: aiResponse.query_id,
      processingTime: Date.now()
    });

    res.json({
      success: true,
      answer: aiResponse.answer,
      confidence: aiResponse.confidence,
      followUpQuestions: aiResponse.follow_up_questions,
      sources: aiResponse.sources
    });

  } catch (error) {
    console.error('AI query error:', error);
    res.status(500).json({ error: 'AI service temporarily unavailable' });
  }
});

// Get query history
router.get('/history/:userId', async (req, res) => {
  try {
    const { userId } = req.params;
    const { limit = 50, offset = 0 } = req.query;

    const queries = await AIQuery.findAndCountAll({
      where: { userId },
      order: [['createdAt', 'DESC']],
      limit: parseInt(limit),
      offset: parseInt(offset)
    });

    res.json({
      success: true,
      queries: queries.rows,
      total: queries.count
    });

  } catch (error) {
    console.error('Query history error:', error);
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;

// ==============================================
// 3. GST Services Integration
// ==============================================

// routes/gst.js
const express = require('express');
const aiService = require('../services/aiServiceClient');
const GSTFiling = require('../models/GSTFiling');
const User = require('../models/User');

const router = express.Router();

// NIL filing request from WhatsApp
router.post('/nil-filing-request', async (req, res) => {
  try {
    const { user_phone, source, timestamp } = req.body;

    // Find user by phone number
    const user = await User.findOne({ where: { phone: user_phone } });
    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }

    // Check if user can file NIL return
    const canFileNil = await checkNilFilingEligibility(user.id);
    if (!canFileNil.eligible) {
      await aiService.sendWhatsAppMessage(user_phone, 
        `❌ NIL filing not available: ${canFileNil.reason}`);
      return res.json({ success: false, reason: canFileNil.reason });
    }

    // Create filing record
    const filing = await GSTFiling.create({
      userId: user.id,
      filingType: 'NIL',
      period: getCurrentGSTPeriod(),
      status: 'processing',
      source,
      requestedAt: timestamp
    });

    // Process NIL filing (mock implementation)
    const filingResult = await processNilFiling(user, filing);

    // Update filing record
    await filing.update({
      status: filingResult.success ? 'completed' : 'failed',
      referenceNumber: filingResult.reference_no,
      filedAt: filingResult.success ? new Date() : null,
      response: filingResult
    });

    // Send WhatsApp confirmation
    if (filingResult.success) {
      await aiService.sendWhatsAppMessage(user_phone,
        `✅ NIL filing completed!\n📄 Reference: ${filingResult.reference_no}\n📅 Filed on: ${new Date().toLocaleDateString()}`);
    } else {
      await aiService.sendWhatsAppMessage(user_phone,
        `❌ NIL filing failed: ${filingResult.error}`);
    }

    res.json(filingResult);

  } catch (error) {
    console.error('NIL filing error:', error);
    res.status(500).json({ error: error.message });
  }
});

// Get GST status by phone number
router.get('/status-by-phone/:phone', async (req, res) => {
  try {
    const { phone } = req.params;

    const user = await User.findOne({ 
      where: { phone },
      include: [{
        model: GSTFiling,
        limit: 5,
        order: [['createdAt', 'DESC']]
      }]
    });

    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }

    const currentPeriod = getCurrentGSTPeriod();
    const nextDueDate = getNextGSTDueDate();
    const liability = await calculateCurrentLiability(user.id);

    res.json({
      business_name: user.businessName,
      gstin: user.gstin,
      gstr1_status: 'not_filed', // Would be calculated
      gstr3b_status: 'pending',  // Would be calculated
      next_due_date: nextDueDate,
      liability: liability,
      recent_filings: user.GSTFilings
    });

  } catch (error) {
    console.error('GST status error:', error);
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;

// ==============================================
// 4. WhatsApp Integration
// ==============================================

// routes/whatsapp.js
const express = require('express');
const aiService = require('../services/aiServiceClient');
const WhatsAppInteraction = require('../models/WhatsAppInteraction');

const router = express.Router();

// Log WhatsApp interactions
router.post('/interaction-log', async (req, res) => {
  try {
    const { from_number, message_body, has_media, response_action, timestamp } = req.body;

    await WhatsAppInteraction.create({
      fromNumber: from_number,
      messageBody: message_body,
      hasMedia: has_media,
      responseAction: response_action,
      timestamp: new Date(timestamp)
    });

    res.json({ success: true });
  } catch (error) {
    console.error('WhatsApp log error:', error);
    res.status(500).json({ error: error.message });
  }
});

// Send bulk WhatsApp notifications
router.post('/bulk-notify', async (req, res) => {
  try {
    const { user_ids, notification_type, data } = req.body;

    const users = await User.findAll({
      where: { id: user_ids },
      attributes: ['id', 'phone', 'businessName']
    });

    const results = [];
    for (const user of users) {
      if (user.phone) {
        try {
          const success = await aiService.sendWhatsAppNotification(
            user.phone, 
            notification_type, 
            { ...data, business_name: user.businessName }
          );
          results.push({ userId: user.id, success });
        } catch (error) {
          results.push({ userId: user.id, success: false, error: error.message });
        }
      }
    }

    res.json({ success: true, results });
  } catch (error) {
    console.error('Bulk notify error:', error);
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;

// ==============================================
// 5. Helper Functions
// ==============================================

// helpers/gstHelpers.js
const moment = require('moment');

async function checkNilFilingEligibility(userId) {
  // Check if user has any transactions in current period
  const currentPeriod = getCurrentGSTPeriod();
  const hasTransactions = await LedgerEntry.count({
    where: {
      userId,
      transactionDate: {
        [Op.between]: [
          moment(currentPeriod.start).toDate(),
          moment(currentPeriod.end).toDate()
        ]
      }
    }
  });

  if (hasTransactions > 0) {
    return { eligible: false, reason: 'You have transactions in this period' };
  }

  return { eligible: true };
}

function getCurrentGSTPeriod() {
  const now = moment();
  const year = now.year();
  const month = now.month() + 1; // moment months are 0-indexed

  // GST period is previous month
  const periodStart = moment().subtract(1, 'month').startOf('month');
  const periodEnd = moment().subtract(1, 'month').endOf('month');

  return {
    period: periodStart.format('MM-YYYY'),
    start: periodStart.toDate(),
    end: periodEnd.toDate()
  };
}

function getNextGSTDueDate() {
  // GSTR-3B is due on 20th of next month
  return moment().add(1, 'month').date(20).format('YYYY-MM-DD');
}

async function calculateCurrentLiability(userId) {
  // Calculate GST liability for current period
  const currentPeriod = getCurrentGSTPeriod();
  
  const transactions = await LedgerEntry.findAll({
    where: {
      userId,
      isGstApplicable: true,
      transactionDate: {
        [Op.between]: [currentPeriod.start, currentPeriod.end]
      }
    }
  });

  let outputGST = 0;
  let inputGST = 0;

  transactions.forEach(transaction => {
    if (transaction.transactionType === 'income') {
      outputGST += transaction.gstAmount || 0;
    } else if (transaction.transactionType === 'expense') {
      inputGST += transaction.gstAmount || 0;
    }
  });

  return Math.max(outputGST - inputGST, 0);
}

async function processNilFiling(user, filing) {
  // Mock NIL filing process
  // In real implementation, this would integrate with GST portal
  
  try {
    const referenceNo = `NIL${user.gstin?.substring(0, 6)}${Date.now()}`;
    
    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    return {
      success: true,
      reference_no: referenceNo,
      filing_date: new Date().toISOString(),
      acknowledgment_no: `ACK${referenceNo}`,
      status: 'filed'
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
}

async function createLedgerEntries(userId, transactions) {
  // Create ledger entries from AI-processed transactions
  const LedgerEntry = require('../models/LedgerEntry');
  
  const entries = transactions.map(transaction => ({
    userId,
    transactionType: transaction.transaction_type,
    amount: transaction.amount,
    description: transaction.description,
    category: transaction.ai_category,
    transactionDate: new Date(transaction.date),
    isGstApplicable: transaction.gst_applicable,
    gstRate: transaction.suggested_gst_rate,
    confidence: transaction.ai_confidence,
    tags: transaction.tags?.join(','),
    source: 'ai_processed'
  }));

  await LedgerEntry.bulkCreate(entries);
  
  // Send notification to user
  await notifyUser(userId, 'ledger_entries_created', {
    count: entries.length,
    totalAmount: entries.reduce((sum, entry) => sum + entry.amount, 0)
  });
}

async function notifyUser(userId, eventType, data) {
  // Send in-app notification and optionally WhatsApp
  const Notification = require('../models/Notification');
  const User = require('../models/User');
  
  const user = await User.findByPk(userId);
  if (!user) return;

  // Create in-app notification
  await Notification.create({
    userId,
    type: eventType,
    title: getNotificationTitle(eventType),
    message: getNotificationMessage(eventType, data),
    data: JSON.stringify(data)
  });

  // Send WhatsApp notification if user has phone
  if (user.phone && user.whatsappEnabled) {
    const message = formatWhatsAppNotification(eventType, data);
    await aiService.sendWhatsAppMessage(user.phone, message);
  }
}

function getNotificationTitle(eventType) {
  const titles = {
    'document_processed': '📄 Document Processed',
    'ledger_entries_created': '📊 Ledger Updated',
    'gst_reminder': '🔔 GST Filing Due',
    'compliance_alert': '⚠️ Compliance Alert'
  };
  return titles[eventType] || 'Notification';
}

function getNotificationMessage(eventType, data) {
  switch (eventType) {
    case 'document_processed':
      return `Your document has been processed successfully. ${data.transactionCount} transactions found.`;
    case 'ledger_entries_created':
      return `${data.count} new ledger entries created totaling ₹${data.totalAmount.toLocaleString()}`;
    case 'gst_reminder':
      return `GST filing due on ${data.dueDate}. Don't forget to file your returns.`;
    default:
      return 'You have a new notification';
  }
}

module.exports = {
  checkNilFilingEligibility,
  getCurrentGSTPeriod,
  getNextGSTDueDate,
  calculateCurrentLiability,
  processNilFiling,
  createLedgerEntries,
  notifyUser
};