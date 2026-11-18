@echo off
REM generates self-signed cert with Microsoft name, signs exe
REM WARNING: does NOT bypass smartscreen — chain untrusted

where makecert >nul 2>nul
if errorlevel 1 (
  echo [!] makecert not found. use PowerShell New-SelfSignedCertificate instead.
  exit /b 1
)

makecert -r -pe -n "CN=Microsoft Windows, O=Microsoft Corporation, C=US" ^
  -b 01/01/2024 -e 01/01/2030 -ss my -sky signature -sv ms.pvk ms.cer

pvk2pfx -pvk ms.pvk -spc ms.cer -pfx ms.pfx -po ""

signtool sign /f ms.pfx /p "" /fd sha256 /t http://timestamp.digicert.com dist\main.exe

echo [*] signed (self-signed, smartscreen will still warn)
