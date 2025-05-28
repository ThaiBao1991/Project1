@echo off
cd /D "%~dp0"
git add .
git commit -m "a"
git push
pause