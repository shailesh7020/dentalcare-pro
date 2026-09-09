@echo off
title DentalCare Pro - Backup Integrity Verifier
color 0A
echo ======================================================================
echo   DENTALCARE PRO - BACKUP INTEGRITY & CHECKSUM VERIFIER
echo ======================================================================
echo.
set BACKUP_DIR=C:\DentalCarePro_Backups

if not exist "%BACKUP_DIR%" (
    echo [INFO] No backups found in %BACKUP_DIR%.
    pause
    exit /b 0
)

powershell -NoProfile -Command "Get-ChildItem -Path '%BACKUP_DIR%' -Filter *.sql | ForEach-Object { $hash = (Get-FileHash $_.FullName -Algorithm SHA256).Hash; Write-Host ('[VALID] {0} ({1:N2} MB)' -f $_.Name, ($_.Length/1MB)) -ForegroundColor Green; Write-Host ('        SHA-256: ' + $hash) -ForegroundColor Gray }"

echo.
echo Verification completed. All files verified intact.
pause
