@echo off
setlocal
chcp 65001 >nul

title Super Calculator v3.0.0 Build

echo ===================================================
echo           SUPER CALCULATOR BUILD v3.0.0
echo ===================================================
echo.

set "PY_EXE=.venv\Scripts\python.exe"
set "SPEC_FILE=Calculator.spec"

if not exist "%PY_EXE%" (
    echo [ERROR] Virtual environment python not found at %PY_EXE%
    pause
    exit /b
)

echo [1/4] Installing dependencies...
"%PY_EXE%" -m pip install pyinstaller flet flet-cli flet-desktop --quiet

echo [2/4] Cleaning old data...
if exist "build" rd /s /q "build"
if exist "dist\Calculator_v3.0.0.exe" del /f /q "dist\Calculator_v3.0.0.exe"

echo [3/4] Running PyInstaller...
echo This may take 3-10 minutes. Please wait.
echo ---------------------------------------------------
"%PY_EXE%" -m PyInstaller --clean --log-level=INFO "%SPEC_FILE%"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Build failed! Check the log above.
    pause
    exit /b
)

echo.
echo [4/4] Creating ZIP archive...
set "EXE_NAME=Calculator_v3.0.0.exe"
set "ZIP_NAME=Calculator_v3.0.0.zip"

if exist "dist\%EXE_NAME%" (
    powershell -Command "Compress-Archive -Path 'dist\%EXE_NAME%' -DestinationPath 'dist\%ZIP_NAME%' -Force"
    echo Done! Archive created: dist\%ZIP_NAME%
) else (
    echo [ERROR] Resulting EXE not found.
)

echo.
echo ===================================================
echo BUILD COMPLETE!
echo ===================================================
echo.
pause
