@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo   PavlovMuseum - PyInstaller ONEDIR build
echo ============================================
echo.

if not exist venv (
    echo [1/5] Creating virtual environment...
    py -m venv venv
    if errorlevel 1 goto :error
) else (
    echo [1/5] Virtual environment already exists.
)

echo [2/5] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 goto :error

echo [3/5] Installing/updating dependencies...
python -m pip install --upgrade pip
if errorlevel 1 goto :error
python -m pip install -r requirements-build.txt
if errorlevel 1 goto :error

echo [4/5] Cleaning old build...
if exist build rmdir /s /q build
if exist dist\PavlovMuseum rmdir /s /q dist\PavlovMuseum

echo [5/5] Building PavlovMuseum.exe in ONEDIR mode...
python -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --onedir ^
  --windowed ^
  --name PavlovMuseum ^
  --add-data "templates;templates" ^
  --add-data "static;static" ^
  --collect-all flask ^
  --collect-all werkzeug ^
  --collect-all waitress ^
  app.py

if errorlevel 1 goto :error

echo.
echo ============================================
echo BUILD COMPLETE
echo.
echo EXE:
echo %CD%\dist\PavlovMuseum\PavlovMuseum.exe
echo.
echo Database and uploads will be stored next to the EXE:
echo   dist\PavlovMuseum\museum.db
echo   dist\PavlovMuseum\static\uploads\
echo ============================================
echo.
pause
exit /b 0

:error
echo.
echo BUILD FAILED. Error code: %errorlevel%
pause
exit /b %errorlevel%
