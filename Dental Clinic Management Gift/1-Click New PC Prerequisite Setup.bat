@echo off
title DentalCare Pro - New PC Prerequisite Auto-Installer
color 0B
echo ============================================================================
echo   DENTALCARE PRO - NEW PC PREREQUISITE CHECKER ^& AUTO-INSTALLER
echo   Automatically checks ^& installs required runtimes on a brand-new PC
echo ============================================================================
echo.

:: 1. Check Python (Bundled in .exe, no install needed for Runtime)
echo [1/4] Checking Bundled Python Engine...
echo       [OK] Python 3.13 + FastAPI + ReportLab PDF Engine are pre-compiled
echo            inside DentalCarePro.exe and DentalCarePro-API.exe!
echo.

:: 2. Check Node.js (Required for Next.js Web UI port 3000 & WhatsApp PDF Gateway port 4050)
echo [2/4] Checking Node.js LTS Runtime (for Web UI ^& WhatsApp PDF Gateway)...
where node >nul 2>nul
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('node -v') do set NODE_VER=%%i
    echo       [OK] Node.js is already installed (%NODE_VER%).
) else (
    echo       [!] Node.js not found. Installing Node.js LTS automatically via winget...
    winget install -e --id OpenJS.NodeJS.LTS --accept-package-agreements --accept-source-agreements
    echo       [OK] Node.js LTS installation triggered.
)
echo.

:: 3. Check PostgreSQL Database (Port 5432)
echo [3/4] Checking PostgreSQL Database Server (Port 5432)...
netstat -ano | findstr ":5432 " | findstr "LISTENING" >nul 2>nul
if %errorlevel% equ 0 (
    echo       [OK] PostgreSQL Server is already running on port 5432.
) else (
    echo       [!] PostgreSQL not detected on port 5432.
    echo       Installing PostgreSQL 16 via winget...
    winget install -e --id PostgreSQL.PostgreSQL.16 --accept-package-agreements --accept-source-agreements
    echo.
    echo       NOTE: When configuring PostgreSQL, set password to: postgres
    echo       Port: 5432, and create database: dentalcare
)
echo.

:: 4. Check Microsoft Edge / Chrome (Required for WebView2 & Headless WhatsApp PDF Sender)
echo [4/4] Checking Microsoft Edge WebView2 ^& Chromium Browser...
if exist "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" (
    echo       [OK] Microsoft Edge / WebView2 is installed.
) else if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    echo       [OK] Google Chrome is installed.
) else (
    echo       [!] Installing Microsoft Edge WebView2 Runtime...
    winget install -e --id Microsoft.EdgeWebView2Runtime --accept-package-agreements --accept-source-agreements
)

echo.
echo ============================================================================
echo   ALL PREREQUISITE CHECKS COMPLETE!
echo   You can now run "Setup.exe" or "Start DentalCare Pro.bat".
echo ============================================================================
pause
