@echo off
title DentalCare Pro - Complete Clinic Launcher
echo ============================================================
echo        DentalCare Pro - Starting Clinic Services
echo ============================================================
echo.
echo 1. Launching Direct WhatsApp PDF Gateway (http://127.0.0.1:4050)...
start "DentalCare Pro - WhatsApp Gateway (Port 4050)" /min cmd /c "cd /d e:\dentalcare-pro && node scripts\whatsapp-gateway.mjs"

echo 2. Launching Backend API (http://0.0.0.0:8000)...
start "DentalCare Pro - Backend API (Port 8000)" /min cmd /c "cd /d e:\dentalcare-pro\backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

echo 3. Launching Next.js Web Frontend (http://0.0.0.0:3000)...
start "DentalCare Pro - Web Frontend (Port 3000)" /min cmd /c "cd /d e:\dentalcare-pro\apps\web && npx next dev -H 0.0.0.0 -p 3000"

echo 4. Waiting for clinic services to initialize...
timeout /t 5 /nobreak >nul

echo 5. Opening DentalCare Pro in your default browser...
start http://localhost:3000

echo.
echo ============================================================
echo DentalCare Pro is now running!
echo - Web Application:   http://localhost:3000
echo - API Documentation: http://localhost:8000/api/v1/docs
echo - WhatsApp Gateway:  http://127.0.0.1:4050/status
echo ============================================================
