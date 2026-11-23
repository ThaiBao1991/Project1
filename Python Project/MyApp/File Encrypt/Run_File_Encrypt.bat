@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
title File Encrypt - Ung dung da nang

set "PYTHON_CMD="
python --version >nul 2>&1 && set "PYTHON_CMD=python"
if not defined PYTHON_CMD py -3 --version >nul 2>&1 && set "PYTHON_CMD=py -3"
if not defined PYTHON_CMD py --version >nul 2>&1 && set "PYTHON_CMD=py"

if not defined PYTHON_CMD goto :NO_PYTHON

echo ============================================================
echo   FILE ENCRYPT - DANG KHOI DONG UNG DUNG...
echo   Lan dau chay co the tu dong cai dat thu vien con thieu
echo ============================================================
echo.

%PYTHON_CMD% "%~dp0main.py"
set "EXIT_CODE=%ERRORLEVEL%"

if "%EXIT_CODE%"=="0" exit /b 0
if "%EXIT_CODE%"=="2" exit /b 0

echo.
echo ============================================================
echo [LOI] Chuong trinh dung voi ma loi: %EXIT_CODE%
echo Neu loi thieu thu vien, ban co the cai thu cong bang lenh:
echo   %PYTHON_CMD% -m pip install -r "%~dp0requirements.txt"
echo ============================================================
pause
exit /b %EXIT_CODE%

:NO_PYTHON
echo ============================================================
echo [LOI] Khong tim thay Python tren may tinh nay!
echo Vui long cai dat Python 3 tu https://www.python.org/downloads/
echo Nho tick chon "Add Python to PATH" khi cai dat.
echo ============================================================
pause
exit /b 1
