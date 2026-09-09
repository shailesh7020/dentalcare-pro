# NSIS Installer Script for DentalCare Pro
!include "MUI2.nsh"
!include "FileFunc.nsh"

Name "DentalCare Pro"
OutFile "..\dist\installer\DentalCarePro-Setup-NSIS.exe"
InstallDir "$LOCALAPPDATA\DentalCare Pro"
RequestExecutionLevel user

!define MUI_ICON "..\assets\branding\app_icon.ico"
!define MUI_UNICON "..\assets\branding\app_icon.ico"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "..\LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

Section "Install"
  SetOutPath "$INSTDIR"
  File "..\dist\DentalCarePro.exe"
  File "..\Project-tutorial.pdf"
  File "..\LICENSE"
  
  SetOutPath "$INSTDIR\backend"
  File "..\dist\backend\DentalCarePro-API.exe"
  
  CreateDirectory "$SMPROGRAMS\DentalCare Pro"
  CreateShortcut "$SMPROGRAMS\DentalCare Pro\DentalCare Pro.lnk" "$INSTDIR\DentalCarePro.exe"
  CreateShortcut "$DESKTOP\DentalCare Pro.lnk" "$INSTDIR\DentalCarePro.exe"
  
  WriteUninstaller "$INSTDIR\Uninstall.exe"
SectionEnd

Section "Uninstall"
  Delete "$DESKTOP\DentalCare Pro.lnk"
  Delete "$SMPROGRAMS\DentalCare Pro\*.*"
  RMDir "$SMPROGRAMS\DentalCare Pro"
  RMDir /r "$INSTDIR"
SectionEnd
