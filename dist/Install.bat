@echo off
setlocal
chcp 65001 >nul
title Super Calculator v3.0.0 Install

set "APP_NAME=PurpurikiCalculator"
set "INSTALL_DIR=%LocalAppData%\%APP_NAME%"
set "EXE_NAME=Calculator_v3.0.0.exe"

echo ===================================================
echo           SUPER CALCULATOR INSTALL v3.0.0
echo ===================================================
echo.

if not exist "dist\%EXE_NAME%" (
    echo [ERROR] File "dist\%EXE_NAME%" not found.
    echo Please run build_exe.bat first!
    echo.
    pause
    exit /b
)

echo [1/3] Copying files to %INSTALL_DIR%...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
copy /y "dist\*.exe" "%INSTALL_DIR%\" >nul
copy /y "Uninstall.bat" "%INSTALL_DIR%\" >nul
copy /y "icon.ico" "%INSTALL_DIR%\" >nul

echo [2/3] Creating desktop shortcut...
set "SCRIPT_PATH=%TEMP%\CreateShortcut.ps1"
echo $WshShell = New-Object -ComObject WScript.Shell > "%SCRIPT_PATH%"
echo $Shortcut = $WshShell.CreateShortcut("$HOME\Desktop\Calculator.lnk") >> "%SCRIPT_PATH%"
echo $Shortcut.TargetPath = "%INSTALL_DIR%\%EXE_NAME%" >> "%SCRIPT_PATH%"
echo $Shortcut.WorkingDirectory = "%INSTALL_DIR%" >> "%SCRIPT_PATH%"
echo $Shortcut.IconLocation = "%INSTALL_DIR%\icon.ico" >> "%SCRIPT_PATH%"
echo $Shortcut.Save() >> "%SCRIPT_PATH%"
powershell -ExecutionPolicy Bypass -File "%SCRIPT_PATH%"
del "%SCRIPT_PATH%"

echo [3/3] Registering in system...
set "REG_PATH=HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\%APP_NAME%"
reg add "%REG_PATH%" /v "DisplayName" /d "Super Calculator (v3.0.0)" /f >nul
reg add "%REG_PATH%" /v "UninstallString" /d "\"%INSTALL_DIR%\Uninstall.bat\"" /f >nul
reg add "%REG_PATH%" /v "DisplayIcon" /d "%INSTALL_DIR%\icon.ico" /f >nul
reg add "%REG_PATH%" /v "Publisher" /d "JoeMoe3910" /f >nul
reg add "%REG_PATH%" /v "DisplayVersion" /d "3.0.0" /f >nul

echo.
echo ===================================================
echo DONE! Installation completed.
echo Shortcut created on Desktop.
echo ===================================================
echo.
pause
