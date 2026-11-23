@echo off
chcp 65001 >nul
echo ==============================================================================
echo           DANG KIEM TRA VA CAI DAT THU VIEN CHO UNG DUNG FILE ENCRYPT
echo ==============================================================================
echo.

cd /d "%~dp0"

echo [1/3] Go bo goi 'crypto' bi xung dot (neu co)...
pip uninstall -y crypto >nul 2>&1

echo [2/3] Cai dat cac thu vien chuan tu requirements.txt...
pip install -r requirements.txt

echo.
echo [3/3] Kiem tra import thu vien...
python -c "from Crypto.Cipher import AES; from Crypto.Util.Padding import pad, unpad; from Crypto.Random import get_random_bytes; import pyxlsb, pandas; print('>>> TAT CA THU VIEN DA SAN SANG! <<<')"

echo.
echo ==============================================================================
echo     HOAN TAT! Nhan phim bat ky de thoat.
echo ==============================================================================
pause >nul
