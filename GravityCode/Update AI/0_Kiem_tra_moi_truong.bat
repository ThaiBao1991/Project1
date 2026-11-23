@echo off
chcp 65001 >nul
title Kiem tra moi truong
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
echo ============================================
echo   Kiem tra gia lap / frida / module thanh toan
echo ============================================
python ultra0.py --check
echo.
pause
