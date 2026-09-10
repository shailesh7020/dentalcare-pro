@echo off
title DentalCare Pro - Web Application Launcher
echo ============================================================
echo           DentalCare Pro - Starting Website
echo ============================================================
echo.
echo 1. Launching Backend API (http://localhost:8000)...
start "DentalCare Pro - Backend API (Port 8000)" cmd /k "cd /d e:\dentalcare-pro\backend && python -m uvicorn app.main:app --port 8000"

echo 2. Launching Next.js Web Frontend (http://localhost:3000)...
start "DentalCare Pro - Web Frontend (Port 3000)" cmd /k "cd /d e:\dentalcare-pro\apps\web && pnpm dev"

echo 3. Waiting for servers to initialize...
timeout /t 5 /nobreak >nul

echo 4. Opening DentalCare Pro in your default browser...
start http://localhost:3000

echo.
echo ============================================================
echo DentalCare Pro is now running!
echo - Web Application:   http://localhost:3000
echo - API Documentation: http://localhost:8000/api/v1/docs
echo.
echo (Keep the two console windows open while using the application)
echo ============================================================
