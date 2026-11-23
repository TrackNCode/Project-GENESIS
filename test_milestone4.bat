@echo off
REM ====================================================================
REM  PROJECT GENESIS - Milestone 4 REINVENT 4 Generative RL Engine Test
REM ====================================================================

echo [GENESIS-AI] Executing Milestone 4 Test Suite...
"C:\Users\MINICO~1\envs\genesis-cheminfo\python.exe" C:\ProjectGENESIS_NO_SPACE\test_generation_pipeline.py
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Milestone 4 verification suite failed!
    exit /b %ERRORLEVEL%
)
echo [GENESIS-AI] Milestone 4 verification completed successfully.
