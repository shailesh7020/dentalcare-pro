@echo off
REM DentalCare Pro - Tailscale Zero-Trust Mesh Setup Assistant
REM Enables encrypted point-to-point remote access between doctor's phone/tablet and clinic server.

echo ===========================================================
echo DENTALCARE PRO - TAILSCALE SECURE MESH SETUP ASSISTANT
echo ===========================================================
echo.

WHERE tailscale.exe >nul 2>nul
IF %ERRORLEVEL% NEQ 0 (
    echo [!] Tailscale is not installed or not in PATH.
    echo     Download installer: https://tailscale.com/download/windows
    echo     Or install via winget: winget install Tailscale.Tailscale
    echo.
    pause
    exit /b 1
)

echo [*] Starting Tailscale with current user permissions...
tailscale up --operator=%USERNAME%

echo.
echo [*] Fetching Tailscale IP address for this Clinic Server...
for /f "tokens=*" %%i in ('tailscale ip -4') do set TS_IP=%%i

echo.
echo ===========================================================
echo TAILSCALE REMOTE ACCESS READY
echo ===========================================================
echo Clinic Server IP: %TS_IP%
echo.
echo How to access from your phone or tablet:
echo 1. Install Tailscale app on your iPhone or Android.
echo 2. Login with the same account.
echo 3. Open Chrome or Safari and visit:
echo    http://%TS_IP%:3000/mobile
echo.
echo [!] Traffic is encrypted end-to-end via WireGuard.
echo [!] Clinic database (PostgreSQL) is NEVER exposed to public internet.
echo ===========================================================
echo.
pause
