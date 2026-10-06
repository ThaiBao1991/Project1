@echo off
chcp 65001 >nul
cd /d "%~dp0"

SET PYTHON_CMD=

REM 1. Kiem tra python trong PATH
python --version >nul 2>&1
if not errorlevel 1 (
    SET PYTHON_CMD=python
    goto run
)

REM 2. Kiem tra py launcher
py -3 --version >nul 2>&1
if not errorlevel 1 (
    SET PYTHON_CMD=py -3
    goto run
)

REM 3. Kiem tra duong dan Python User / System
if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" (
    SET "PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    goto run
)
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    SET "PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    goto run
)
if exist "C:\Python312\python.exe" (
    SET "PYTHON_CMD=C:\Python312\python.exe"
    goto run
)
if exist "C:\Python310\python.exe" (
    SET "PYTHON_CMD=C:\Python310\python.exe"
    goto run
)

echo [LOI] Khong tim thay Python tren he thong!
echo Vui long cai dat Python va tick vao "Add Python to PATH".
pause
exit /b 1

:run
%PYTHON_CMD% StampByAntigravity.py
if errorlevel 1 pause

