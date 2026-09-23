@echo off
chcp 65001 >nul
title Mabuchi Motor - He Thong Tao De Thi & Dap An Tu Dong
echo Dang khoi dong giao dien De Thi Mabuchi Motor...
python app_gui.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Co loi khi chay chuong trinh. Nhan phim bat ky de thoat...
    pause >nul
)
