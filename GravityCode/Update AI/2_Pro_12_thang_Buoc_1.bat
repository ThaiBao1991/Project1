@echo off
chcp 65001 >nul
title Pro 12 thang - buoc 1
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
echo ============================================
echo   Google AI Pro 5TB - 12 thang mien phi (buoc 1)
echo   Xac nhan trang thanh toan ghi: dung thu mien phi 12 thang
echo   KHONG xac nhan neu no hien 1 thang hoac co gia tien
echo ============================================
python ultra0.py --account "current@device" --no-add --force --plan pro12
echo.
pause
