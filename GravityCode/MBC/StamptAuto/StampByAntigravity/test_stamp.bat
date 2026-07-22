@echo off
chcp 65001 >nul
echo.
echo ============================================================
echo   TEST: StampByAntigravity.py
echo ============================================================
echo.

SET PYTHON=C:\Python312\python.exe
SET SCRIPT=%~dp0StampByAntigravity.py

echo [1] Kiem tra Python...
%PYTHON% --version
if errorlevel 1 (
    echo LOI: Khong tim thay Python tai %PYTHON%
    pause & exit /b 1
)

echo.
echo [2] Liet ke cac config co san...
%PYTHON% "%SCRIPT%" --list

echo.
echo [3] Kiem tra thu vien...
%PYTHON% -c "import fitz; print('  PyMuPDF OK:', fitz.__version__)"
%PYTHON% -c "import PIL; print('  Pillow OK:', PIL.__version__)"
%PYTHON% -c "import cv2; print('  OpenCV OK:', cv2.__version__)" 2>nul || echo   OpenCV: khong co (chi dung vi tri co dinh)
%PYTHON% -c "import numpy; print('  NumPy OK:', numpy.__version__)" 2>nul || echo   NumPy: khong co

echo.
echo ============================================================
echo   Huong dan su dung:
echo   %PYTHON% "%SCRIPT%" "duong_dan_file.pdf" "ten_config"
echo.
echo   Vi du:
echo   %PYTHON% "%SCRIPT%" "C:\docs\abc.pdf" "GRR"
echo ============================================================
echo.
pause
