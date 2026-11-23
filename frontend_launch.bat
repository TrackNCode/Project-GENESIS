@echo off
setlocal
cd /d "%~dp0frontend"
title Project GENESIS - Frontend Portal (Port 3000)
echo =====================================================================
echo       PROJECT GENESIS: WEB INTERFACE (PORT 3000)
echo =====================================================================
echo.

where npm >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Node.js / npm not found!
    echo Please install Node.js from https://nodejs.org
    pause
    exit /b 1
)

echo Starting Vite dev server...
call npm run dev
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Frontend exited with error code %ERRORLEVEL%.
    pause
)
