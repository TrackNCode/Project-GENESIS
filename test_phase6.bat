@echo off
setlocal
echo ======================================================================
echo  Project GENESIS - Phase 6 AI Prediction ^& Lead Optimisation Test Suite
echo ======================================================================

set CONDA_ENV=C:\Users\MINICO~1\envs\genesis-cheminfo
set PYTHON=%CONDA_ENV%\python.exe

if not exist "%PYTHON%" (
    echo [ERROR] Python not found at %PYTHON%
    exit /b 1
)

echo [INFO] Running test_qsar_adme.py against active FastAPI backend...
"%PYTHON%" C:\ProjectGENESIS_NO_SPACE\test_qsar_adme.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [FAIL] Phase 6 test suite encountered errors.
    exit /b %ERRORLEVEL%
)

echo.
echo [PASS] All Phase 6 AI prediction and lead optimization tests completed successfully!
exit /b 0
