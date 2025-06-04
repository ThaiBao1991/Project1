@echo off
cd /D "%~dp0"
git add .
git commit -m "b"
git push
pause