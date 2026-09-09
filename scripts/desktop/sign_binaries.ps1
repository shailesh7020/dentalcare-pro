# scripts/desktop/sign_binaries.ps1
<#
.SYNOPSIS
  Signs DentalCare Pro Windows binaries using Signtool.exe or Azure Trusted Signing.
.DESCRIPTION
  Applies SHA256 digital signatures and RFC 3161 timestamps to executables and installer packages.
#>

param(
    [string]$CertificatePath = "cert.pfx",
    [string]$CertificatePassword = "",
    [string]$TimestampServer = "http://timestamp.digicert.com"
)

$RootDir = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$BinariesToSign = @(
    "$RootDir\dist\DentalCarePro.exe",
    "$RootDir\dist\backend\DentalCarePro-API.exe",
    "$RootDir\dist\installer\DentalCarePro-Setup-1.0.0.exe"
)

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  DentalCare Pro Windows Binary Code Signing" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

$Signtool = Get-Command signtool.exe -ErrorAction SilentlyContinue

if (-not $Signtool) {
    Write-Warning "signtool.exe was not found in PATH. Skipping actual signing (Code signing placeholder mode)."
    Write-Host "To sign in production, install Windows SDK and provide a valid EV Code Signing Certificate."
    exit 0
}

foreach ($binary in $BinariesToSign) {
    if (Test-Path $binary) {
        Write-Host "Signing $binary..." -ForegroundColor Green
        & signtool.exe sign /fd SHA256 /tr $TimestampServer /td SHA256 /f $CertificatePath /p $CertificatePassword $binary
    }
}

Write-Host "Code signing process completed." -ForegroundColor Cyan
