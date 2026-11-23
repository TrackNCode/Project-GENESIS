@echo off
setlocal
cd /d "%~dp0"
title Project GENESIS - Backend Server (Port 8000)
echo =====================================================================
echo       PROJECT GENESIS: SCIENTIFIC BACKEND (PORT 8000)
echo =====================================================================
echo.

:: Check if Port 8000 is already active
netstat -ano | findstr ":8000 " | findstr "LISTENING" >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [INFO] GENESIS Backend is ALREADY active and running on Port 8000!
    echo [INFO] API Documentation: http://127.0.0.1:8000/docs
    echo [INFO] System is healthy and accepting requests.
    echo.
    echo Leave this window open while using the application.
    pause
    exit /b 0
)

set "PY_CMD="
if exist "C:\Users\MINICO~1\envs\genesis-cheminfo\python.exe" (
    set "PY_CMD=C:\Users\MINICO~1\envs\genesis-cheminfo\python.exe"
    goto run
)
if exist "%~dp0venv\Scripts\python.exe" (
    set "PY_CMD=%~dp0venv\Scripts\python.exe"
    goto run
)
where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    set "PY_CMD=python"
    goto run
)

echo [ERROR] No Python interpreter found!
echo Please run install_genesis_windows.bat first.
pause
exit /b 1

:run
echo Starting FastAPI with %PY_CMD% ...
"%PY_CMD%" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Backend exited with error code %ERRORLEVEL%.
    pause
)
