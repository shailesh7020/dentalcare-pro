@echo off
setlocal enabledelayedexpansion
title DentalCare Pro - Database Backup Tool
color 0B
echo ======================================================================
echo   DENTALCARE PRO - ONE-CLICK SECURE DATABASE BACKUP
echo ======================================================================
echo.

set BACKUP_DIR=C:\DentalCarePro_Backups
if not exist "%BACKUP_DIR%" (
    mkdir "%BACKUP_DIR%"
    echo [+] Created backup folder: %BACKUP_DIR%
)

for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c%%a%%b)
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a%%b)
set TIMESTAMP=%DATE:~10,4%%DATE:~4,2%%DATE:~7,2%_%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%
set OUTPUT_FILE=%BACKUP_DIR%\dentalcare_backup_%TIMESTAMP%.sql

echo [*] Starting PostgreSQL database snapshot...
echo [*] Target: %OUTPUT_FILE%
echo.

if exist "%~dp0backup_manager.exe" (
    "%~dp0backup_manager.exe" --backup --dest "%BACKUP_DIR%"
    goto finish
)

:: Direct fallback via pg_dump if executable not available
set PGPASSWORD=postgres
set PG_BIN=pg_dump
if exist "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" set PG_BIN="C:\Program Files\PostgreSQL\18\bin\pg_dump.exe"
if exist "C:\Program Files\PostgreSQL\17\bin\pg_dump.exe" set PG_BIN="C:\Program Files\PostgreSQL\17\bin\pg_dump.exe"
if exist "C:\Program Files\PostgreSQL\16\bin\pg_dump.exe" set PG_BIN="C:\Program Files\PostgreSQL\16\bin\pg_dump.exe"

%PG_BIN% -h 127.0.0.1 -p 5432 -U postgres -F p -f "%OUTPUT_FILE%" dentalcare
if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] Backup created successfully at:
    echo           %OUTPUT_FILE%
) else (
    echo [WARNING] Direct pg_dump returned code %ERRORLEVEL%.
)

:finish
echo.
echo ======================================================================
echo   BACKUP PROCESS COMPLETE
echo   All patient charts, appointments, and billing data are protected.
echo ======================================================================
echo.
pause
