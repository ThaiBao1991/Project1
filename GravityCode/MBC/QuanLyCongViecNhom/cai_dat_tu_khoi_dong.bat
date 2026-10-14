@echo off
chcp 65001 >nul
echo ========================================================
echo  CAI DAT TU DONG KHOI DONG CUNG WINDOWS - MBC FILE HELPER
echo ========================================================
echo.

set "SCRIPT_DIR=%~dp0"
set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "TARGET_VBS=%STARTUP_FOLDER%\MBC_FileHelper.vbs"

echo Dang tao file khoi dong ngam tai:
echo %TARGET_VBS%
echo.

(
echo Set WshShell = CreateObject^("WScript.Shell"^)
echo WshShell.Run "cmd.exe /c start /b pythonw ""%SCRIPT_DIR%open_file_helper.py"" || start /b python ""%SCRIPT_DIR%open_file_helper.py""", 0, False
) > "%TARGET_VBS%"

if exist "%TARGET_VBS%" (
    echo [THANH CONG] Da cai dat thanh cong!
    echo Tu bay gio moi khi bat may tinh, Python Helper se tu dong chay ngam.
    echo Ban chi can mo web va bam [Mo] la Excel/Folder tu dong mo ngay lap tuc.
    echo.
    echo Dang khoi dong Helper ngay bay gio...
    wscript "%TARGET_VBS%"
) else (
    echo [THAT BAI] Khong the ghi file vao thu muc Startup.
)

echo.
pause
