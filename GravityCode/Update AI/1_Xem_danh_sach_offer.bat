@echo off
chcp 65001 >nul
title Liet ke offer (khong mua)
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
echo ============================================
echo   Liet ke tat ca offer cua Pro 5TB (KHONG mua)
echo ============================================
python ultra0.py --account "current@device" --no-add --force --list --plan pro12
echo.
pause
