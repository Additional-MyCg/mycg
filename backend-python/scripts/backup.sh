#!/bin/bash

echo "💾 Creating backup of MyCG AI Service..."

# Create backup directory with timestamp
backup_dir="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$backup_dir"

# Backup configuration files
echo "📁 Backing up configuration..."
cp .env "$backup_dir/" 2>/dev/null || echo "⚠️  .env file not found"
cp docker-compose.yml "$backup_dir/"
cp -r nginx "$backup_dir/" 2>/dev/null || echo "⚠️  nginx directory not found"

# Backup application code
echo "💻 Backing up application code..."
tar -czf "$backup_dir/app_code.tar.gz" \
  --exclude='temp_uploads' \
  --exclude='logs' \
  --exclude='__pycache__' \
  --exclude='.git' \
  --exclude='backups' \
  .

# Backup Redis data (if running in Docker)
echo "🗃️  Backing up Redis data..."
if docker ps | grep -q redis; then
    docker exec $(docker ps -q -f name=redis) redis-cli BGSAVE
    sleep 5
    docker cp $(docker ps -q -f name=redis):/data/dump.rdb "$backup_dir/"
    echo "✅ Redis data backed up"
else
    echo "⚠️  Redis container not running, skipping data backup"
fi

# Backup logs
echo "📄 Backing up logs..."
if [ -d "logs" ]; then
    tar -czf "$backup_dir/logs.tar.gz" logs/
    echo "✅ Logs backed up"
else
    echo "⚠️  No logs directory found"
fi

# Create backup manifest
echo "📋 Creating backup manifest..."
cat > "$backup_dir/manifest.txt" << EOF
MyCG AI Service Backup
Created: $(date)
Hostname: $(hostname)
Version: $(git describe --tags 2>/dev/null || echo "unknown")
Docker Images:
$(docker images | grep mycg-ai || echo "No mycg-ai images found")

Contents:
- Application code (app_code.tar.gz)
- Configuration files (.env, docker-compose.yml, nginx/)
- Redis data (dump.rdb)
- Logs (logs.tar.gz)
EOF

# Calculate backup size
backup_size=$(du -sh "$backup_dir" | cut -f1)
echo ""
echo "✅ Backup complete!"
echo "📍 Location: $backup_dir"
echo "📏 Size: $backup_size"
echo ""
echo "📤 To restore from this backup:"
echo "   ./restore.sh $backup_dir"