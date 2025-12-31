@echo off
REM Quick Fix for Frontend Tailwind Plugin Error
REM SynthetIQ Signals CDP - Windows Version

echo ========================================
echo Fixing frontend Tailwind CSS plugin error...
echo ========================================
echo.

REM Stop frontend container
echo [1/5] Stopping frontend container...
docker-compose stop frontend

REM Rebuild frontend with no cache
echo [2/5] Rebuilding frontend (installing missing dependencies)...
docker-compose build --no-cache frontend

REM Start frontend
echo [3/5] Starting frontend...
docker-compose up -d frontend

REM Wait for it to be ready
echo [4/5] Waiting for frontend to be ready...
timeout /t 5 /nobreak >nul

REM Check status
echo [5/5] Checking frontend status...
docker-compose logs --tail=20 frontend

echo.
echo ========================================
echo Fix complete!
echo ========================================
echo.
echo Test the frontend:
echo   start http://localhost:5173
echo.
echo If you still see errors, check logs:
echo   docker-compose logs -f frontend
echo.
pause
