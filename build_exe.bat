@echo off
chcp 65001 >nul
title Сборка Калькулятора

echo ===================================================
echo           СБОРКА КАЛЬКУЛЯТОРА В EXE
echo ===================================================
echo.

:: Активируем виртуальное окружение
call C:\Users\Inna\venv\Scripts\activate.bat

echo [1/3] Установка/обновление PyInstaller...
pip install pyinstaller flet flet-cli flet-desktop --quiet

echo [2/3] Сборка EXE через SPEC файл...
pyinstaller --clean Calculator_PRO_v2.5.0.spec

echo [3/3] Создание ZIP архива...
ren dist\Calculator_PRO_v2.5.0.exe "Calculator_PRO_v2.5.0.exe"
powershell -Command "Compress-Archive -Path 'dist\Calculator_PRO_v2.5.0.exe' -DestinationPath 'dist\Calculator_PRO_v2.5.0.zip' -Force"

echo.
echo ===================================================
echo Готово! Файлы находятся в папке dist\
echo ===================================================
echo.
pause
