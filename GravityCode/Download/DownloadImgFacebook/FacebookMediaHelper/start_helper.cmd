@echo off
setlocal
PowerShell -NoProfile -Command "try { $r = Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 http://127.0.0.1:48765/health; if ($r.StatusCode -eq 200) { exit 0 }; exit 1 } catch { exit 1 }"
if not errorlevel 1 (
  echo Facebook Media Helper is already running at http://127.0.0.1:48765
  exit /b 0
)
node "%~dp0server.js"
pause
