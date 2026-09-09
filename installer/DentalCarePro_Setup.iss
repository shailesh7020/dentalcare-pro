// Inno Setup 6 Script for DentalCare Pro Enterprise Edition
// Official Commercial Windows Installer

#define MyAppName "DentalCare Pro"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "DentalCare Pro Inc."
#define MyAppURL "https://www.dentalcarepro.com"
#define MyAppExeName "DentalCarePro.exe"

[Setup]
AppId={{D37E8A91-49B6-4A23-8B39-8C7E6D8A29A1}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion} (Enterprise Edition)
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/support
AppUpdatesURL={#MyAppURL}/updates
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=..\LICENSE
OutputDir=..\dist\installer
OutputBaseFilename=DentalCarePro-Setup-{#MyAppVersion}
SetupIconFile=..\assets\branding\app_icon.ico
WizardImageFile=..\assets\branding\installer_banner.bmp
WizardSmallImageFile=..\assets\branding\installer_small.bmp
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "autostart"; Description: "Automatically launch DentalCare Pro on Windows startup"; GroupDescription: "Startup Options:"; Flags: unchecked

[Files]
; Primary Executables and Core Binaries
Source: "..\dist\DentalCarePro.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\backend\DentalCarePro-API.exe"; DestDir: "{app}\backend"; Flags: ignoreversion; Tasks: 
Source: "..\Project-tutorial.pdf"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\assets\branding\*"; DestDir: "{app}\assets\branding"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\branding\app_icon.ico"
Name: "{group}\Database Backup Tool"; Filename: "{app}\backend\DentalCarePro-API.exe"; Parameters: "--backup"; IconFilename: "{app}\assets\branding\app_icon.ico"
Name: "{group}\User Manual & Tutorial (PDF)"; Filename: "{app}\Project-tutorial.pdf"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\assets\branding\app_icon.ico"
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: autostart

[Run]
Filename: "{app}\backend\DentalCarePro-API.exe"; Parameters: "--migrate"; StatusMsg: "Applying latest database migrations..."; Flags: runhidden
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: files; Name: "{app}\*.log"

[Code]
// Pascal Script for PostgreSQL Detection & Data Preservation Safeguards

function IsPostgresInstalled(): Boolean;
begin
  // Check for PostgreSQL service or installation in registry
  Result := RegKeyExists(HKLM, 'SOFTWARE\PostgreSQL\Installations') or
            RegKeyExists(HKLM64, 'SOFTWARE\PostgreSQL\Installations') or
            RegKeyExists(HKLM, 'SYSTEM\CurrentControlSet\Services\postgresql-x64-16') or
            RegKeyExists(HKLM, 'SYSTEM\CurrentControlSet\Services\postgresql-x64-15');
end;

function InitializeSetup(): Boolean;
var
  MsgResult: Integer;
begin
  Result := True;
  if not IsPostgresInstalled() then
  begin
    MsgResult := MsgBox(
      'DentalCare Pro requires a PostgreSQL database.' + #13#10#13#10 +
      '• If this is a standalone clinic computer, PostgreSQL 16 should be installed locally.' + #13#10 +
      '• If your clinic already runs PostgreSQL on a central server, you can configure the remote server during setup.' + #13#10#13#10 +
      'Would you like to proceed with installation now?',
      mbInformation, MB_YESNO
    );
    if MsgResult = IDNO then
      Result := False;
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DataDir: String;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    DataDir := ExpandConstant('{localappdata}\DentalCarePro');
    if DirExists(DataDir) then
    begin
      if MsgBox('Do you want to retain your clinic patient data and backups at ' + DataDir + '?' + #13#10#13#10 +
                'Click YES to keep your patient records (Recommended for HIPAA/GDPR compliance).' + #13#10 +
                'Click NO to permanently erase all local clinic data.', mbConfirmation, MB_YESNO) = IDNO then
      begin
        DelTree(DataDir, True, True, True);
      end;
    end;
  end;
end;
