@echo off
setlocal
cd /d "%~dp0frontend"
title Project GENESIS - Frontend Portal (Port 3000)
echo =====================================================================
echo       PROJECT GENESIS: WEB INTERFACE (PORT 3000)
echo =====================================================================
echo.

:: Check if Port 3000 is already active
netstat -ano | findstr ":3000 " | findstr "LISTENING" >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [INFO] GENESIS Frontend is ALREADY active and running on Port 3000!
    echo [INFO] User Interface: http://localhost:3000/
    echo [INFO] System is healthy and accepting requests.
    echo.
    echo Leave this window open while using the application.
    pause
    exit /b 0
)

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
