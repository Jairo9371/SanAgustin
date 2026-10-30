@echo off
echo Hospital San Agustin - Django
if not exist .venv\Scripts\python.exe (
    echo Primero ejecuta: py -m venv .venv
    pause
    exit /b 1
)
.venv\Scripts\python.exe manage.py runserver
pause
