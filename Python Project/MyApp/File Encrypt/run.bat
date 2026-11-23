@echo off
cd /d "%~dp0"
python main.py
if %errorlevel% neq 0 (
    echo.
    echo ========================================================
    echo [LOI] Chuong trinh bi dung dot ngot voi ma loi: %errorlevel%
    echo Vui long kiem tra lai thu vien hoac chay CAI_DAT_THU_VIEN.bat
    echo ========================================================
    pause
)
