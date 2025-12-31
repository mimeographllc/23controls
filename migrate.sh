#!/bin/bash

# Database Migration Helper Script
# Creates and applies Alembic migrations

echo "🗄️  Database Migration Helper"
echo "=============================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if backend is running
BACKEND_RUNNING=$(docker-compose ps backend | grep "running" | wc -l)
if [ $BACKEND_RUNNING -eq 0 ]; then
    echo -e "${RED}❌ Backend is not running${NC}"
    echo ""
    echo "Start backend first:"
    echo "  docker-compose up -d backend"
    echo ""
    exit 1
fi

echo -e "${GREEN}✅ Backend is running${NC}"
echo ""

# Step 1: Create migration
echo "Step 1: Creating migration..."
echo "Command: alembic revision --autogenerate -m 'Phase 2: Auth and hierarchy models'"
echo ""

docker-compose exec backend alembic revision --autogenerate -m "Phase 2: Auth and hierarchy models"

if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}❌ Migration creation failed${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "1. Check backend logs:"
    echo "   docker-compose logs backend"
    echo ""
    echo "2. Verify models import:"
    echo "   docker-compose exec backend python -c 'from app.models import User; print(User.__tablename__)'"
    echo ""
    echo "3. Check database connection:"
    echo "   docker-compose exec postgres pg_isready"
    echo ""
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Migration created${NC}"
echo ""

# Step 2: Apply migration
echo "Step 2: Applying migration to database..."
echo "Command: alembic upgrade head"
echo ""

docker-compose exec backend alembic upgrade head

if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}❌ Migration application failed${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "1. Check if PostgreSQL is ready:"
    echo "   docker-compose exec postgres pg_isready"
    echo ""
    echo "2. Try connecting to database:"
    echo "   docker-compose exec postgres psql -U synthetiq_user -d synthetiq_cdp -c '\dt'"
    echo ""
    echo "3. Reset database (WARNING: deletes all data):"
    echo "   docker-compose down -v"
    echo "   docker-compose up -d"
    echo "   Then run this script again"
    echo ""
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Migration applied successfully${NC}"
echo ""

# Step 3: Verify tables
echo "Step 3: Verifying database tables..."
echo ""

TABLES=$(docker-compose exec postgres psql -U synthetiq_user -d synthetiq_cdp -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';" 2>/dev/null | tr -d ' ')

if [ -n "$TABLES" ] && [ "$TABLES" -gt 10 ]; then
    echo -e "${GREEN}✅ Database has $TABLES tables${NC}"
    echo ""
    echo "Tables created:"
    docker-compose exec postgres psql -U synthetiq_user -d synthetiq_cdp -c "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;"
else
    echo -e "${YELLOW}⚠️  Expected 13+ tables, found: $TABLES${NC}"
    echo ""
    echo "List tables:"
    docker-compose exec postgres psql -U synthetiq_user -d synthetiq_cdp -c "\dt"
fi

echo ""
echo "=============================="
echo -e "${GREEN}🎉 Migration Complete!${NC}"
echo "=============================="
echo ""
echo "Next steps:"
echo ""
echo "1. Test API health:"
echo "   curl http://localhost:8000/health"
echo ""
echo "2. Test authentication:"
echo "   curl -X POST http://localhost:8000/api/v1/auth/signup \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"email\": \"test@example.com\", ...}'"
echo ""
echo "3. Import Postman collection:"
echo "   docs/api/SecureAuth_API.postman_collection.json"
echo ""
