@echo off
cd /d "%~dp0"
title Local AI Control Panel

:: Kiem tra xem pythonw.exe co ton tai de khoi chay an cua so cmd
where pythonw >nul 2>&1
if %ERRORLEVEL% equ 0 (
    start "" pythonw local_ai_gui.py
) else (
    start "" python local_ai_gui.py
)
exit

