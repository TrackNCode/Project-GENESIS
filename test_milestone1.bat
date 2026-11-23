@echo off
REM ====================================================================
REM  PROJECT GENESIS - Milestone 1 Ingestion and Scientific Foundation Test
REM ====================================================================

echo [GENESIS-AI] Executing Milestone 1 Test Suite...
"C:\Users\MINICO~1\envs\genesis-cheminfo\python.exe" C:\ProjectGENESIS_NO_SPACE\test_ingestion_pipeline.py
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Milestone 1 verification suite failed!
    exit /b %ERRORLEVEL%
)
echo [GENESIS-AI] Milestone 1 verification completed successfully.
