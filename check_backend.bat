@echo off
setlocal enabledelayedexpansion
rem ====================================================================
rem Project GENESIS - Backend Automated Health Monitor
rem Designed for Windows Task Scheduler and manual diagnostics
rem ====================================================================

set "URL=http://127.0.0.1:8000/health"
set "LOG_FILE=%~dp0backend_health.log"
set "DATE_STR=%date% %time%"

for /f "delims=" %%I in ('curl.exe -s -m 5 "%URL%" 2^>nul') do set "RESP=%%I"

echo !RESP! | findstr /C:"\"status\":\"ok\"" >nul
if !ERRORLEVEL! equ 0 (
    echo [%DATE_STR%] [HEALTHY] Backend is online. Status: OK >> "%LOG_FILE%"
    echo [%DATE_STR%] [HEALTHY] Backend is online. Status: OK
    exit /b 0
) else (
    echo [%DATE_STR%] [UNHEALTHY] Backend failed check or unreachable! Response: "!RESP!" >> "%LOG_FILE%"
    echo [%DATE_STR%] [UNHEALTHY] Backend failed check or unreachable! Response: "!RESP!"
    exit /b 1
)
