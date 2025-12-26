#!/bin/bash
# Check All Services Status

echo "========================================="
echo "Service Status Check"
echo "========================================="
echo ""

# Check Docker containers
echo "1. Docker Containers:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "gml-|NAME" || echo "No containers found"

echo ""
echo "2. Service Connectivity:"

# PostgreSQL
echo -n "   PostgreSQL (5432): "
if docker exec gml-postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo "✅ Running"
elif nc -zv localhost 5432 > /dev/null 2>&1; then
    echo "✅ Port open"
else
    echo "❌ Not accessible"
fi

# Redis
echo -n "   Redis (6379): "
if docker exec gml-redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Running"
elif nc -zv localhost 6379 > /dev/null 2>&1; then
    echo "✅ Port open"
else
    echo "❌ Not accessible"
fi

# Qdrant
echo -n "   Qdrant (6333): "
if curl -s http://localhost:6333/health > /dev/null 2>&1; then
    echo "✅ Running (Web UI available)"
else
    echo "❌ Not accessible"
fi

# MinIO
echo -n "   MinIO (9000): "
if curl -s http://localhost:9000/minio/health/live > /dev/null 2>&1; then
    echo "✅ Running"
else
    echo "❌ Not accessible"
fi

echo -n "   MinIO Console (9001): "
if curl -s http://localhost:9001 > /dev/null 2>&1; then
    echo "✅ Running (Web UI available)"
else
    echo "❌ Not accessible"
fi

# Backend API
echo -n "   Backend API (8000): "
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Running (Web UI: http://localhost:8000/api/docs)"
else
    echo "❌ Not accessible"
fi

# Frontend
echo -n "   Frontend (3000): "
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Running (Web UI: http://localhost:3000)"
else
    echo "❌ Not accessible"
fi

echo ""
echo "========================================="
echo "Web Interfaces (Browser Accessible)"
echo "========================================="
echo "✅ Frontend:        http://localhost:3000"
echo "✅ Backend API Docs: http://localhost:8000/api/docs"
echo "✅ MinIO Console:   http://localhost:9001"
echo "✅ Qdrant Dashboard: http://localhost:6333/dashboard"
echo ""
echo "⚠️  PostgreSQL (5432) and Redis (6379) are NOT web services"
echo "   They are database servers - use database clients to connect"
echo ""
echo "To verify they work, check the backend health endpoint:"
echo "   curl http://localhost:8000/api/v1/health/detailed"

