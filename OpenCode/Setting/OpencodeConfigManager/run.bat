@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found! Please install Python from https://python.org
    pause
    exit /b 1
)

echo Checking dependencies...
python -c "import customtkinter" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing customtkinter...
    pip install customtkinter>=6.0.0
    if %errorlevel% neq 0 (
        echo Failed to install dependencies
        pause
        exit /b 1
    )
)

echo Starting OpenCode Config Manager...
python src/main.py

pause