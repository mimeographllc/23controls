#!/bin/bash

# Quick Fix for Backend Pydantic Settings Error
# SynthetIQ Signals CDP

echo "🔧 Fixing backend Pydantic settings error..."
echo ""

# Stop backend container
echo "1️⃣  Stopping backend container..."
docker-compose stop backend

# Rebuild backend with no cache
echo "2️⃣  Rebuilding backend (this will update dependencies)..."
docker-compose build --no-cache backend

# Start backend
echo "3️⃣  Starting backend..."
docker-compose up -d backend

# Wait for it to be ready
echo "4️⃣  Waiting for backend to be ready..."
sleep 5

# Check status
echo "5️⃣  Checking backend status..."
docker-compose logs --tail=20 backend

echo ""
echo "✅ Fix complete!"
echo ""
echo "Test the backend:"
echo "  curl http://localhost:8000/health"
echo "  open http://localhost:8000/api/v1/docs"
echo ""
echo "If you still see errors, check logs:"
echo "  docker-compose logs -f backend"
echo ""
