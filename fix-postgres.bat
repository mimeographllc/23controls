@echo off
REM Quick Fix Script for PostgreSQL Logical Replication Error
REM SynthetIQ Signals CDP - Windows Version

echo ========================================
echo Fixing PostgreSQL logical replication error...
echo ========================================
echo.

REM Step 1: Stop containers
echo [1/5] Stopping containers...
docker-compose down

REM Step 2: Remove volumes
echo [2/5] Removing PostgreSQL volume...
docker-compose down -v

REM Step 3: Start with new configuration
echo [3/5] Starting containers with fixed configuration...
docker-compose up -d --build

REM Step 4: Wait for services to be healthy
echo [4/5] Waiting for services to be healthy...
timeout /t 10 /nobreak >nul

REM Step 5: Check status
echo [5/5] Checking service status...
docker-compose ps

echo.
echo ========================================
echo Fix complete!
echo ========================================
echo.
echo Verify the fix:
echo   docker-compose logs postgres ^| findstr /i "logical replication"
echo   (You should NOT see any errors)
echo.
echo Test the application:
echo   curl http://localhost:8000/health
echo   start http://localhost:5173
echo.
pause
