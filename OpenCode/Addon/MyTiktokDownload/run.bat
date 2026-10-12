@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo  TikTok Downloader - yt-dlp Edition
echo ========================================
echo.

echo Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found!
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

echo Checking dependencies...
python -c "import yt_dlp, customtkinter, requests" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing dependencies...
    pip install yt-dlp customtkinter requests --quiet
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
    echo Dependencies installed!
)

echo.
echo Starting TikTok Downloader...
echo.
python src/main.py

pause