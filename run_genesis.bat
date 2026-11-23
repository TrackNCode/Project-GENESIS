@echo off
setlocal enabledelayedexpansion
title Project GENESIS - Scientific AI Platform Launcher

echo =====================================================================
echo          PROJECT GENESIS: SCIENTIFIC AI DISCOVERY PLATFORM
echo                     One-Click System Launcher
echo =====================================================================
echo.

cd /d "%~dp0"

echo [1/3] Launching Backend Server (Port 8000)...
start "GENESIS Backend (Port 8000)" cmd /c ""%~dp0backend_launch.bat""

where npm >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [2/3] Launching Frontend Portal (Port 3000)...
    start "GENESIS Frontend (Port 3000)" cmd /c ""%~dp0frontend_launch.bat""
    echo [3/3] Initializing services, opening browser in 4 seconds...
    timeout /t 4 >nul
    start http://localhost:3000/
) else (
    echo [2/3] Node/npm not found, serving production bundle on Port 8000...
    timeout /t 4 >nul
    start http://127.0.0.1:8000/
)

echo.
echo =====================================================================
echo   GENESIS IS LIVE!
echo   - Frontend Portal: http://localhost:3000/  (or http://127.0.0.1:8000/)
echo   - Backend Docs:    http://127.0.0.1:8000/docs
echo =====================================================================
echo Keep the backend and frontend command windows open while using GENESIS.
echo You may close this launcher window now.
echo.
pause
