@echo off
chcp 65001 >nul
title Khoi Dong MBC Quan Ly Cong Viec Nhom

echo ========================================================
echo   DANG KHOI DONG MBC QUAN LY CONG VIEC & MO FILE NATIVE
echo ========================================================
echo.

:: Khoi dong open_file_helper.py chay ngam bang pythonw (khong hien cua so den)
where pythonw >nul 2>nul
if %errorlevel% equ 0 (
    start "" pythonw open_file_helper.py
    echo [OK] Da kich hoat File Helper ngam (pythonw).
) else (
    where python >nul 2>nul
    if %errorlevel% equ 0 (
        start /min "" python open_file_helper.py
        echo [OK] Da kich hoat File Helper (python minimized).
    ) else (
        echo [!] Khong tim thay Python. Web app van chay binh thuong.
    )
)

:: Cho 1 giay roi mo giao dien index.html tren trinh duyet mac dinh
timeout /t 1 /nobreak >nul
start "" http://127.0.0.1:38271/

echo.
echo [XONG] Da mo ung dung tren trinh duyet!
timeout /t 2 /nobreak >nul
exit
