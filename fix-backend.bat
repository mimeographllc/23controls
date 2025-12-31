@echo off
REM Quick Fix for Backend Pydantic Settings Error
REM SynthetIQ Signals CDP - Windows Version

echo ========================================
echo Fixing backend Pydantic settings error...
echo ========================================
echo.

REM Stop backend container
echo [1/5] Stopping backend container...
docker-compose stop backend

REM Rebuild backend with no cache
echo [2/5] Rebuilding backend (updating dependencies)...
docker-compose build --no-cache backend

REM Start backend
echo [3/5] Starting backend...
docker-compose up -d backend

REM Wait for it to be ready
echo [4/5] Waiting for backend to be ready...
timeout /t 5 /nobreak >nul

REM Check status
echo [5/5] Checking backend status...
docker-compose logs --tail=20 backend

echo.
echo ========================================
echo Fix complete!
echo ========================================
echo.
echo Test the backend:
echo   curl http://localhost:8000/health
echo   start http://localhost:8000/api/v1/docs
echo.
echo If you still see errors, check logs:
echo   docker-compose logs -f backend
echo.
pause
