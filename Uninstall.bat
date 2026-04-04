@echo off
setlocal
chcp 65001 >nul
title Деинсталляция Super Calculator v3.0.0

set "APP_NAME=PurpurikiCalculator"
set "INSTALL_DIR=%LocalAppData%\%APP_NAME%"
set "REG_PATH=HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\%APP_NAME%"

echo ===================================================
echo           УДАЛЕНИЕ КАЛЬКУЛЯТОРА v3.0.0
echo ===================================================
echo.

set /p confirm="Вы уверены, что хотите полностью удалить программу? (Y/N): "
if /I "%confirm%" NEQ "Y" (
    echo Удаление отменено.
    pause
    exit /b
)

echo.
echo [1/3] Удаление ярлыка...
if exist "%USERPROFILE%\Desktop\Калькулятор.lnk" (
    del "%USERPROFILE%\Desktop\Калькулятор.lnk"
    echo     Ярлык удален.
)

echo [2/3] Удаление данных из реестра...
reg delete "%REG_PATH%" /f >nul 2>&1
echo     Реестр очищен.

echo [3/3] Очистка файлов...
echo Программа будет полностью удалена через 2 секунды. Папка %INSTALL_DIR% будет стерта.
echo.
timeout /t 2 /nobreak >nul
start /b "" cmd /c "timeout /t 1 /nobreak >nul & if exist \"%INSTALL_DIR%\" rd /s /q \"%INSTALL_DIR%\""

echo Прощайте!
timeout /t 2 >nul
exit
