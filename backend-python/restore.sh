#!/bin/bash

if [ -z "$1" ]; then
    echo "❌ Usage: ./restore.sh <backup_directory>"
    echo "📁 Available backups:"
    ls -la backups/ 2>/dev/null || echo "No backups found"
    exit 1
fi

backup_dir="$1"

if [ ! -d "$backup_dir" ]; then
    echo "❌ Backup directory not found: $backup_dir"
    exit 1
fi

echo "🔄 Restoring MyCG AI Service from backup..."
echo "📍 Backup: $backup_dir"
echo ""

# Confirm restoration
read -p "⚠️  This will overwrite current configuration. Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Restoration cancelled"
    exit 1
fi

# Stop current services
echo "🛑 Stopping current services..."
docker-compose down

# Restore configuration files
echo "📁 Restoring configuration..."
if [ -f "$backup_dir/.env" ]; then
    cp "$backup_dir/.env" .
    echo "✅ .env restored"
fi

if [ -f "$backup_dir/docker-compose.yml" ]; then
    cp "$backup_dir/docker-compose.yml" .
    echo "✅ docker-compose.yml restored"
fi

if [ -d "$backup_dir/nginx" ]; then
    rm -rf nginx
    cp -r "$backup_dir/nginx" .
    echo "✅ nginx configuration restored"
fi

# Restore application code
echo "💻 Restoring application code..."
if [ -f "$backup_dir/app_code.tar.gz" ]; then
    tar -xzf "$backup_dir/app_code.tar.gz"
    echo "✅ Application code restored"
fi

# Restore Redis data
echo "🗃️  Restoring Redis data..."
if [ -f "$backup_dir/dump.rdb" ]; then
    # Start Redis container
    docker-compose up -d redis
    sleep 10
    
    # Copy Redis data
    docker cp "$backup_dir/dump.rdb" $(docker ps -q -f name=redis):/data/
    docker-compose restart redis
    echo "✅ Redis data restored"
fi

# Restore logs
echo "📄 Restoring logs..."
if [ -f "$backup_dir/logs.tar.gz" ]; then
    tar -xzf "$backup_dir/logs.tar.gz"
    echo "✅ Logs restored"
fi

# Start services
echo "▶️  Starting services..."
docker-compose up -d

# Wait and health check
echo "⏳ Waiting for services..."
sleep 30

health_response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/api/v1/health)
if [ "$health_response" -eq 200 ]; then
    echo "✅ Restoration complete! Service is healthy."
else
    echo "⚠️  Service started but health check failed (HTTP $health_response)"
    echo "📋 Check logs: docker-compose logs mycg-ai"
fi

echo ""
echo "🌐 Service: http://localhost:8001"
echo "🩺 Health: http://localhost:8001/api/v1/health"