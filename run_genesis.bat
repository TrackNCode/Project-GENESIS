@echo off
setlocal enabledelayedexpansion
title Project GENESIS - Scientific AI Platform Launcher

echo =====================================================================
echo          PROJECT GENESIS: SCIENTIFIC AI DISCOVERY PLATFORM
echo                     One-Click System Launcher
echo =====================================================================
echo.

cd /d "%~dp0"

:: 1. Detect Python environment
set "PY_CMD="

if exist "C:\Users\MINICO~1\envs\genesis-cheminfo\python.exe" (
    set "PY_CMD=C:\Users\MINICO~1\envs\genesis-cheminfo\python.exe"
    echo [ENV] Using established Conda environment: genesis-cheminfo
    goto launch
)

if exist "venv\Scripts\python.exe" (
    set "PY_CMD=venv\Scripts\python.exe"
    echo [ENV] Using local virtual environment in .\venv
    goto launch
)

:: Check for conda environments
where conda >nul 2>nul
if %ERRORLEVEL% equ 0 (
    conda env list | findstr /C:"genesis-cheminfo" >nul 2>nul
    if !ERRORLEVEL! equ 0 (
        set "PY_CMD=conda run --no-capture-output -n genesis-cheminfo python"
        echo [ENV] Using Conda environment: genesis-cheminfo
        goto launch
    )
    conda env list | findstr /C:"genesis " >nul 2>nul
    if !ERRORLEVEL! equ 0 (
        set "PY_CMD=conda run --no-capture-output -n genesis python"
        echo [ENV] Using Conda environment: genesis
        goto launch
    )
)

where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    set "PY_CMD=python"
    echo [ENV] Using System Python
    goto launch
)

echo [ERROR] No Python environment detected!
echo Please run 'install_genesis_windows.bat' first to install all requirements.
pause
exit /b 1

:launch
echo.
echo =====================================================================
echo [STARTING] Launching GENESIS Scientific Backend on Port 8000 ...
echo [INFO] Swagger API Docs: http://127.0.0.1:8000/docs
echo =====================================================================
echo.

:: Launch Backend in its own persistent window
start "GENESIS Backend (Port 8000)" cmd /k "cd /d "%~dp0" && %PY_CMD% -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000"

:: Check if Node/npm is present to run Vite dev server on port 3000
where npm >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [STARTING] Launching GENESIS Frontend on Port 3000 ...
    start "GENESIS Frontend (Port 3000)" cmd /k "cd /d "%~dp0\frontend" && npm run dev"
    echo Waiting 3 seconds for services to initialize...
    timeout /t 3 >nul
    echo Opening browser to http://localhost:3000/ ...
    start http://localhost:3000/
) else (
    echo [NOTICE] Running in self-hosted mode via FastAPI on Port 8000...
    timeout /t 3 >nul
    echo Opening browser to http://127.0.0.1:8000/ ...
    start http://127.0.0.1:8000/
)

echo.
echo =====================================================================
echo   GENESIS IS LIVE!
echo   - Frontend Portal: http://localhost:3000/  (or http://127.0.0.1:8000/)
echo   - Backend Docs:    http://127.0.0.1:8000/docs
echo =====================================================================
echo You can keep this launcher window open or minimize it.
pause
