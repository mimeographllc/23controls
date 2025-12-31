#!/bin/bash

# Quick Fix Script for PostgreSQL Logical Replication Error
# SynthetIQ Signals CDP

echo "🔧 Fixing PostgreSQL logical replication error..."
echo ""

# Step 1: Stop containers
echo "1️⃣  Stopping containers..."
docker-compose down

# Step 2: Remove volumes
echo "2️⃣  Removing PostgreSQL volume..."
docker-compose down -v

# Step 3: Start with new configuration
echo "3️⃣  Starting containers with fixed configuration..."
docker-compose up -d --build

# Step 4: Wait for services to be healthy
echo "4️⃣  Waiting for services to be healthy..."
sleep 10

# Step 5: Check status
echo "5️⃣  Checking service status..."
docker-compose ps

echo ""
echo "✅ Fix complete!"
echo ""
echo "Verify the fix:"
echo "  docker-compose logs postgres | grep -i 'logical replication'"
echo "  (You should NOT see any errors)"
echo ""
echo "Test the application:"
echo "  curl http://localhost:8000/health"
echo "  open http://localhost:5173"
echo ""
