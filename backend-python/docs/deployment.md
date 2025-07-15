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