@echo off
setlocal
echo ======================================================================
echo  Project GENESIS - Phase 5 Virtual Screening Automated Test Suite
echo ======================================================================

set CONDA_ENV=C:\Users\MINICO~1\envs\genesis-cheminfo
set PYTHON=%CONDA_ENV%\python.exe

if not exist "%PYTHON%" (
    echo [ERROR] Python not found at %PYTHON%
    exit /b 1
)

echo [INFO] Running test_screening_pipeline.py against active FastAPI backend...
"%PYTHON%" C:\ProjectGENESIS_NO_SPACE\test_screening_pipeline.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [FAIL] Virtual screening test suite encountered errors.
    exit /b %ERRORLEVEL%
)

echo.
echo [PASS] All Phase 5 virtual screening tests completed successfully!
exit /b 0
