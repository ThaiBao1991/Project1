@echo off
chcp 65001 >nul
echo ========================================================
echo  HUY TU DONG KHOI DONG CUNG WINDOWS - MBC FILE HELPER
echo ========================================================
echo.

set "TARGET_VBS=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\MBC_FileHelper.vbs"

if exist "%TARGET_VBS%" (
    del "%TARGET_VBS%"
    echo [THANH CONG] Da xoa khoi dong ngam cung Windows!
) else (
    echo [THONG BAO] File khoi dong chua tung duoc cai dat.
)

echo.
pause
