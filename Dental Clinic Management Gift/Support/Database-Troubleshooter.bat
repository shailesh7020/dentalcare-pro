@echo off
echo ===================================================
echo DentalCare Pro - PostgreSQL Database Troubleshooter
echo ===================================================
echo Testing connection to PostgreSQL on localhost:5432...
powershell -NoProfile -Command "try { $c = New-Object System.Net.Sockets.TcpClient('127.0.0.1', 5432); Write-Host 'SUCCESS: PostgreSQL is listening on port 5432.' -ForegroundColor Green; $c.Close() } catch { Write-Host 'WARNING: Cannot connect to PostgreSQL on port 5432.' -ForegroundColor Red; Write-Host 'Ensure PostgreSQL service is started.' -ForegroundColor Yellow }"
echo.
pause
