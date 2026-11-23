@echo off
setlocal enabledelayedexpansion

echo ======================================================================
echo PROJECT GENESIS - MILESTONE 5 VERIFICATION SUITE
echo Subsystem: Closed-Loop Iterative Discovery Worker and Lineage System
echo Target Hardware: RTX 3060 CUDA and Intel Core i7-14700KF
echo ======================================================================

set PYTHON_CHEMINFO=C:\Users\MINICO~1\envs\genesis-cheminfo\python.exe
set BACKEND_DIR=C:\ProjectGENESIS_NO_SPACE\backend

cd /d "%BACKEND_DIR%"

echo.
echo Running Milestone 5 Verification Tests in genesis-cheminfo...
"%PYTHON_CHEMINFO%" test_iterative_loop.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ======================================================================
    echo MILESTONE 5 VERIFICATION: SUCCESS [ALL TESTS PASSED]
    echo ======================================================================
    exit /b 0
) else (
    echo.
    echo ======================================================================
    echo MILESTONE 5 VERIFICATION: FAILED
    echo ======================================================================
    exit /b 1
)
