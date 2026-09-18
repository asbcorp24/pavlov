@echo off
setlocal
cd /d "%~dp0"

start "" "PavlovMuseum.exe"
timeout /t 2 /nobreak >nul

set "URL=http://127.0.0.1:5000"

if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" (
  start "" "%ProgramFiles%\Google\Chrome\Application\chrome.exe" --kiosk --no-first-run --disable-pinch "%URL%"
  exit /b
)

if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" (
  start "" "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" --kiosk --no-first-run --disable-pinch "%URL%"
  exit /b
)

if exist "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" (
  start "" "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" --kiosk "%URL%" --edge-kiosk-type=fullscreen --no-first-run
  exit /b
)

start "" "%URL%"
