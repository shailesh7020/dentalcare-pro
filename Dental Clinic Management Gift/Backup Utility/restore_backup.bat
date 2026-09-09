@echo off
setlocal enabledelayedexpansion
title DentalCare Pro - Database Restore Tool
color 0C
echo ======================================================================
echo   DENTALCARE PRO - DATABASE RESTORATION UTILITY
echo ======================================================================
echo.
echo [CAUTION] Restoring a database backup will overwrite the existing
echo           database with the contents of the chosen backup file!
echo.

set BACKUP_DIR=C:\DentalCarePro_Backups
if not exist "%BACKUP_DIR%" (
    echo [ERROR] Backup directory %BACKUP_DIR% does not exist!
    pause
    exit /b 1
)

echo Available backups in %BACKUP_DIR%:
echo ----------------------------------------------------------------------
dir /B /O-D "%BACKUP_DIR%\*.sql" 2>nul
echo ----------------------------------------------------------------------
echo.

set /p BACKUP_FILE="Enter full backup filename or drag-and-drop .sql file here: "
if "%BACKUP_FILE%"=="" (
    echo Operation cancelled by user.
    pause
    exit /b 0
)

:: Strip surrounding quotes
set BACKUP_FILE=%BACKUP_FILE:"=%

if not exist "%BACKUP_FILE%" (
    if exist "%BACKUP_DIR%\%BACKUP_FILE%" (
        set BACKUP_FILE=%BACKUP_DIR%\%BACKUP_FILE%
    ) else (
        echo [ERROR] Cannot find backup file: %BACKUP_FILE%
        pause
        exit /b 1
    )
)

echo.
echo [CONFIRMATION] Are you sure you want to restore from:
echo   %BACKUP_FILE%
echo.
set /p CONFIRM="Type YES in capital letters to proceed: "
if not "%CONFIRM%"=="YES" (
    echo Restore cancelled. Database was not modified.
    pause
    exit /b 0
)

echo.
echo [*] Restoring database...
if exist "%~dp0backup_manager.exe" (
    "%~dp0backup_manager.exe" --restore "%BACKUP_FILE%"
    goto finish_restore
)

set PGPASSWORD=postgres
set PSQL_BIN=psql
if exist "C:\Program Files\PostgreSQL\18\bin\psql.exe" set PSQL_BIN="C:\Program Files\PostgreSQL\18\bin\psql.exe"
if exist "C:\Program Files\PostgreSQL\17\bin\psql.exe" set PSQL_BIN="C:\Program Files\PostgreSQL\17\bin\psql.exe"
if exist "C:\Program Files\PostgreSQL\16\bin\psql.exe" set PSQL_BIN="C:\Program Files\PostgreSQL\16\bin\psql.exe"

%PSQL_BIN% -h 127.0.0.1 -p 5432 -U postgres -d dentalcare -f "%BACKUP_FILE%"

:finish_restore
echo.
echo ======================================================================
echo   RESTORATION PROCESS FINISHED
echo ======================================================================
echo.
pause
