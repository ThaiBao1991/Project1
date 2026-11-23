@echo off
chcp 65001 >nul
title Pro +6 thang - buoc 3
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
echo ============================================
echo   Google AI Pro 5TB - them 6 thang (buoc 3)
echo   Tong cong se thanh 24 thang
echo ============================================
python ultra0.py --account "current@device" --no-add --force --stack --plan pro6b
echo.
pause
