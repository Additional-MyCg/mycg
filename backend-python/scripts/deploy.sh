#!/bin/bash

echo "🚀 Deploying MyCG AI Service..."

# Set environment to production
export ENVIRONMENT=production
export DEBUG=false

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down

# Build new images
echo "🔨 Building new images..."
docker-compose build --no-cache

# Start services
echo "▶️  Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Health check
echo "🩺 Running health checks..."
health_response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/api/v1/health)

if [ "$health_response" -eq 200 ]; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed (HTTP $health_response)"
    echo "📋 Container logs:"
    docker-compose logs --tail=50 mycg-ai
    exit 1
fi

# Test API endpoints
echo "🧪 Testing API endpoints..."

# Test document processing endpoint
doc_test=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8001/api/v1/document/process)
echo "📄 Document API: HTTP $doc_test"

# Test AI chat endpoint
ai_test=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8001/api/v1/ai/query \
  -H "Content-Type: application/json" \
  -d '{"query":"test","user_id":"test"}')
echo "🤖 AI Chat API: HTTP $ai_test"

# Test WhatsApp webhook
whatsapp_test=$(curl -s -o /dev/null -w "%{http_code}" -X GET http://localhost:8001/api/v1/whatsapp/health)
echo "📱 WhatsApp API: HTTP $whatsapp_test"

echo ""
echo "✅ Deployment complete!"
echo "🌐 Service is running at: http://localhost:8001"
echo "📚 API Documentation: http://localhost:8001/docs"
echo "🩺 Health Check: http://localhost:8001/api/v1/health"
echo ""
echo "📊 To view logs:"
echo "   docker-compose logs -f mycg-ai"
echo ""
echo "🔧 To restart services:"
echo "   docker-compose restart"