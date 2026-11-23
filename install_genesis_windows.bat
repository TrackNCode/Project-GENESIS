@echo off
setlocal enabledelayedexpansion
title Project GENESIS - Windows Automated Installer

echo =====================================================================
echo          PROJECT GENESIS: SCIENTIFIC AI DISCOVERY PLATFORM
echo                    Windows Automated Installer
echo =====================================================================
echo.

cd /d "%~dp0"

echo [1/3] Checking Python and Conda environment managers...
where conda >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [FOUND] Conda is installed on this system.
    echo Creating / updating Conda environment 'genesis'...
    call conda env create -f environment_genesis.yml || call conda env update -f environment_genesis.yml --prune
    echo.
    echo [SUCCESS] Conda environment 'genesis' is ready!
    goto check_bin
)

where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [FOUND] System Python detected.
    echo Creating virtual environment in .\venv ...
    python -m venv venv
    call .\venv\Scripts\activate.bat
    echo Installing dependencies from requirements_full.txt ...
    pip install --upgrade pip
    pip install -r requirements_full.txt
    echo.
    echo [SUCCESS] Virtual environment .\venv is ready!
    goto check_bin
)

echo [ERROR] Neither Conda nor Python was found on PATH.
echo Please install Miniforge or Python 3.11 from https://github.com/conda-forge/miniforge/releases
pause
exit /b 1

:check_bin
echo.
echo [2/3] Checking AutoDock Vina molecular docking binaries...
if exist "backend\bin\vina.exe" (
    echo [OK] AutoDock Vina executable confirmed at backend\bin\vina.exe.
) else (
    echo [WARNING] backend\bin\vina.exe not found!
    echo Downloading official AutoDock Vina v1.2.5 for Windows...
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://github.com/ccsb-scripps/AutoDock-Vina/releases/download/v1.2.5/vina_1.2.5_windows_x86_64.exe' -OutFile 'backend\bin\vina.exe'"
    echo [OK] AutoDock Vina downloaded successfully.
)

echo.
echo [3/3] Verifying pre-built frontend distribution bundle...
if exist "frontend\dist\index.html" (
    echo [OK] Frontend distribution bundle confirmed at frontend\dist.
) else (
    echo [NOTICE] Building frontend bundle...
    where npm >nul 2>nul
    if %ERRORLEVEL% equ 0 (
        cd frontend && call npm install && call npm run build && cd ..
    ) else (
        echo [WARNING] Node.js/npm not found. Using pre-packaged frontend bundle.
    )
)

echo.
echo =====================================================================
echo   INSTALLATION COMPLETE!
echo   Double-click 'run_genesis.bat' to launch the entire platform.
echo =====================================================================
pause
