@echo off
chcp 65001 >nul
title Pro +6 thang - buoc 2
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
echo ============================================
echo   Google AI Pro 5TB - them 6 thang (buoc 2)
echo   Chi chay khi buoc 1 da thanh cong
echo   Dung nang cap goi dang ky (purchaseToken cu + CHARGE_FULL_PRICE) de
echo   thoi gian dung thu con lai duoc quy doi va doi lai thay vi bi thay the.
echo ============================================
python ultra0.py --account "current@device" --no-add --force --stack --plan pro6
echo.
pause
