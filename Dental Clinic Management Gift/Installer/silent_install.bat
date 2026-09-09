@echo off
echo ===================================================
echo DentalCare Pro - Silent Unattended Workstation Setup
echo ===================================================
echo Installing DentalCare Pro silently...
"%~dp0..\Install DentalCare Pro.exe" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
echo Installation finished with exit code %ERRORLEVEL%.
