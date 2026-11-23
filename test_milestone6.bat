@echo off
setlocal enabledelayedexpansion

echo ======================================================================
echo PROJECT GENESIS - MILESTONE 6 SCIENTIFIC BENCHMARK SUITE
echo Subsystem: End-to-End Multi-Target Benchmark and System Integrity
echo Target Hardware: RTX 3060 CUDA and Intel Core i7-14700KF
echo ======================================================================

set PYTHON_CHEMINFO=C:\Users\MINICO~1\envs\genesis-cheminfo\python.exe
set BACKEND_DIR=C:\ProjectGENESIS_NO_SPACE\backend

cd /d "%BACKEND_DIR%"

echo.
echo Running Milestone 6 Multi-Target Scientific Benchmark in genesis-cheminfo...
"%PYTHON_CHEMINFO%" test_milestone6_benchmark.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ======================================================================
    echo MILESTONE 6 VERIFICATION: SUCCESS [ALL BENCHMARKS PASSED]
    echo ======================================================================
    exit /b 0
) else (
    echo.
    echo ======================================================================
    echo MILESTONE 6 VERIFICATION: FAILED
    echo ======================================================================
    exit /b 1
)
