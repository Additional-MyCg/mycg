# 🚀 Microservice Architecture

A complete microservice setup with React frontend, Node.js backend, Python backend, PostgreSQL databases, and Nginx reverse proxy.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   React App     │    │  Nginx Proxy    │
│   (Port 3001)   │◄───┤   (Port 80)     │
└─────────────────┘    └─────────────────┘
                                │
                    ┌───────────┼───────────┐
                    │                       │
        ┌─────────────────┐    ┌─────────────────┐
        │   Node.js API   │    │  Python API     │
        │   (Port 5001)   │    │  (Port 8001)    │
        └─────────────────┘    └─────────────────┘
                 │                       │
        ┌─────────────────┐    ┌─────────────────┐
        │  PostgreSQL     │    │  PostgreSQL     │
        │  (Port 5433)    │    │  (Port 5434)    │
        └─────────────────┘    └─────────────────┘
```

## 🚦 Quick Start

### Option 1: Automatic Setup
```bash
# Make the startup script executable and run it
./start.sh
```

### Option 2: Manual Setup
```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode
docker-compose up --build -d
```

## 🌐 Access Points

- **Main Application**: http://localhost
- **Direct Service Access**:
  - React Frontend: http://localhost:3001
  - Node.js Backend: http://localhost:5001
  - Python Backend: http://localhost:8001

## 🔗 API Endpoints

### Node.js Service
- `GET /health` - Health check
- `GET /users` - Get all users
- `POST /users` - Create new user

### Python Service
- `GET /health` - Health check
- `GET /products` - Get all products
- `POST /products` - Create new product

### Via Nginx Proxy
- `GET /api/node/health` - Node.js health
- `GET /api/node/users` - Get users
- `GET /api/python/health` - Python health
- `GET /api/python/products` - Get products

## 💾 Database Access

```bash
# Connect to Node.js database
docker exec -it postgres-node psql -U nodeuser -d nodedb

# Connect to Python database
docker exec -it postgres-python psql -U pythonuser -d pythondb
```

## 🛠️ Management Scripts

```bash
# Start all services
./start.sh

# Stop all services
./stop.sh

# View logs (all services)
./logs.sh

# View logs (specific service)
./logs.sh frontend
./logs.sh backend-node
./logs.sh backend-python
```

## 🔧 Development

### File Structure
```
├── docker-compose.yml       # Main orchestration file
├── nginx/
│   └── nginx.conf          # Reverse proxy configuration
├── frontend-react/         # React application
├── backend-node/          # Node.js + Express + PostgreSQL
├── backend-python/        # Python + Flask + PostgreSQL
├── start.sh              # Quick start script
├── stop.sh               # Stop script
└── logs.sh               # Log viewing script
```

### Making Changes

The setup includes volume mounting for development:
- React: Changes auto-reload
- Node.js: Uses nodemon for auto-restart
- Python: Flask debug mode enabled

### Port Configuration

All external ports are configured to avoid common conflicts:
- Nginx: 80 (main access point)
- React: 3001 (instead of 3000)
- Node.js: 5001 (instead of 5000 - avoids macOS AirPlay)
- Python: 8001 (instead of 8000)
- PostgreSQL Node: 5433 (instead of 5432)
- PostgreSQL Python: 5434

## 🔍 Troubleshooting

### Common Issues

1. **Port conflicts**: All ports are configured to avoid common conflicts
2. **Docker not running**: Ensure Docker Desktop is running
3. **Database connection issues**: Wait for health checks to pass

### Useful Commands

```bash
# Check container status
docker-compose ps

# View specific service logs
docker-compose logs backend-node

# Restart specific service
docker-compose restart frontend

# Clean everything and restart
docker-compose down && docker system prune -f && docker-compose up --build
```

## 🚀 Next Steps

1. Add authentication and authorization
2. Implement API versioning
3. Add monitoring and logging
4. Set up CI/CD pipelines
5. Add more microservices
6. Implement message queues
7. Add caching layer
8. Set up SSL certificates

## 📝 License

All rights are reserved to MyCG.AI