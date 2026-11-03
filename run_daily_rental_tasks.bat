@echo off
setlocal
cd /d "%~dp0"
if exist "%~dp0env\Scripts\python.exe" (
    set "PYTHON=%~dp0env\Scripts\python.exe"
) else if exist "%~dp0.venv\Scripts\python.exe" (
    set "PYTHON=%~dp0.venv\Scripts\python.exe"
) else (
    set "PYTHON=python"
)
"%PYTHON%" manage.py close_expired_rentals
if errorlevel 1 exit /b %errorlevel%
"%PYTHON%" manage.py send_expiry_reminders
exit /b %errorlevel%
