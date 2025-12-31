#!/bin/bash

# Quick Fix for Frontend Tailwind Plugin Error
# SynthetIQ Signals CDP

echo "🔧 Fixing frontend Tailwind CSS plugin error..."
echo ""

# Stop frontend container
echo "1️⃣  Stopping frontend container..."
docker-compose stop frontend

# Rebuild frontend with no cache
echo "2️⃣  Rebuilding frontend (this will install missing dependencies)..."
docker-compose build --no-cache frontend

# Start frontend
echo "3️⃣  Starting frontend..."
docker-compose up -d frontend

# Wait for it to be ready
echo "4️⃣  Waiting for frontend to be ready..."
sleep 5

# Check status
echo "5️⃣  Checking frontend status..."
docker-compose logs --tail=20 frontend

echo ""
echo "✅ Fix complete!"
echo ""
echo "Test the frontend:"
echo "  open http://localhost:5173"
echo ""
echo "If you still see errors, check logs:"
echo "  docker-compose logs -f frontend"
echo ""
