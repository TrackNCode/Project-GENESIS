@echo off
REM ====================================================================
REM  PROJECT GENESIS - Milestone 3 GNINA 3D-CNN Docking Engine Test
REM ====================================================================

echo [GENESIS-AI] Executing Milestone 3 Test Suite...
"C:\Users\MINICO~1\envs\genesis-cheminfo\python.exe" C:\ProjectGENESIS_NO_SPACE\test_gnina_pipeline.py
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Milestone 3 verification suite failed!
    exit /b %ERRORLEVEL%
)
echo [GENESIS-AI] Milestone 3 verification completed successfully.
