@echo off
rem ====================================================================
rem Project GENESIS - PyMOL Visualisation Engine Test Suite
rem ====================================================================

set "MINICONDA=C:\Users\MINICO~1"
set "PYTHON_EXE=%MINICONDA%\envs\genesis-cheminfo\python.exe"

if not exist "%PYTHON_EXE%" (
    echo [ERROR] Python environment not found at %PYTHON_EXE%
    exit /b 1
)

echo Starting PyMOL Visualisation Engine Test Suite against http://127.0.0.1:8000 ...
"%PYTHON_EXE%" "%~dp0test_pymol_integration.py"
exit /b %ERRORLEVEL%
