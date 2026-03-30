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
pip install pyinstaller --quiet

echo [2/3] Сборка EXE с иконкой...
pyinstaller --onefile --noconsole --name "Калькулятор" --icon "icon.ico" main.py

echo [3/3] Создание ZIP архива...
powershell -Command "Compress-Archive -Path 'dist\Калькулятор.exe' -DestinationPath 'dist\Калькулятор.zip' -Force"

echo.
echo ===================================================
echo Готово! Файлы находятся в папке dist\
echo ===================================================
echo.
pause
