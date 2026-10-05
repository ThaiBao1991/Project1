@echo off
chcp 65001 >nul
title Mabuchi Motor - He Thong Tao De Thi & Dap An Tu Dong
echo ======================================================================
echo   MABUCHI MOTOR - HE THONG TAO DE THI ^& DAP AN TU DONG
echo ======================================================================
echo Dang khoi dong ung dung va kiem tra thu vien...
echo.
python app_gui.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ======================================================================
    echo Co loi xay ra khi chay chuong trinh.
    echo Neu bi loi thieu thu vien, hay xem huong dan ben tren hoac chay:
    echo   pip install -r requirements.txt
    echo ======================================================================
    echo Nhan phim bat ky de thoat...
    pause >nul
)
