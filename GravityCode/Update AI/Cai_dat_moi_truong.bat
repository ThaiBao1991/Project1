@echo off
chcp 65001 >nul
title Cai dat moi truong mot cham
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8

echo ============================================================
echo   Google Ultra / Pro cai dat mot cham
echo   - kiem tra Python
echo   - cai frida 16.5.9
echo   - tim hoac tai adb
echo   - ket noi MuMu va tu kiem tra
echo ============================================================
echo.
pause

python setup_env.py

echo.
echo ------------------------------------------------------------
echo   Xong. Neu toan xanh, bam dup 2_Pro_12_thang_Buoc_1.bat
echo ------------------------------------------------------------
pause
