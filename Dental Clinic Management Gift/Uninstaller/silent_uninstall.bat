@echo off
title DentalCare Pro - Silent Unattended Uninstall
echo ======================================================================
echo   DentalCare Pro - Silent Workstation Decommissioning
echo ======================================================================
echo Removing DentalCare Pro application files silently...
"%~dp0uninstall.exe" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
echo Uninstallation completed with exit code %ERRORLEVEL%.
