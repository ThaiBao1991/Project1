# -*- coding: utf-8 -*-
"""tools/setup_autostart.py — CÀI ĐẶT TỰ ĐỘNG CHẠY SAU KHI BẬT MÁY.

GÓI 9 (17/11): yêu cầu user "kiểm tra nếu tắt máy tính thì có lỗi gì không".
⇒ Ngoài việc dữ liệu AN TOÀN (atomic write), hệ thống phải **tự phục hồi**
sau khi bật máy lại:

  1. **Thư mục Startup** (KHÔNG cần admin) — watchdog 24/7 chạy khi user đăng
     nhập ⇒ tự bù media + AI + toast sau mỗi lần tắt/bật máy.
  2. Task Scheduler `VocabularyApp-CheckDone` → StartWhenAvailable + RestartCount
     (bù lịch bị bỏ khi máy tắt) — đã cài sẵn.
  3. Task `VocabularyApp-Watchdog` (AtStartup, SYSTEM) — **cần admin**, tùy chọn.

Chạy:
  python tools/setup_autostart.py --install     # startup folder + task
  python tools/setup_autostart.py --status
  python tools/setup_autostart.py --uninstall
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TASK_WATCHDOG = "VocabularyApp-Watchdog"
TASK_CHECK = "VocabularyApp-CheckDone"
CMD = os.path.join(BASE, "tools", "watchdog_task.cmd")
CHECK_CMD = os.path.join(BASE, "tools", "check_done_task.cmd")

# Thư mục Startup của user (không cần quyền admin)
STARTUP = os.path.join(
    os.environ.get("APPDATA", ""),
    "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
STARTUP_ITEM = os.path.join(STARTUP, "VocabularyApp_Watchdog.vbs")


def _ps(script: str) -> str:
    p = subprocess.run(["powershell", "-NoProfile", "-Command", script],
                       capture_output=True, text=True, timeout=120)
    return (p.stdout or "") + (p.stderr or "")


def install() -> int:
    if not os.path.isfile(CMD):
        with open(CMD, "w", encoding="ascii", errors="replace") as f:
            f.write(
                "@echo off\r\n"
                "REM VocabularyApp - watchdog 24/7 (AI + media + toast)\r\n"
                "cd /d \"%s\"\r\n"
                "python -X utf8 tools\\ai_watchdog.py >> data\\logs\\watchdog_stdout.log 2>&1\r\n"
                % BASE)
        print("đã tạo:", CMD)

    # 1) THƯ MỤC STARTUP — KHÔNG cần admin ⇒ chạy khi user đăng nhập.
    # Ghi .vbs/.cmd bằng **ASCII thuần**: VBScript/cmd đọc theo ANSI ⇒ tiếng
    # Việt có dấu sẽ hỏng (đo thật: file .vbs đầu tiên bị méo).
    os.makedirs(STARTUP, exist_ok=True)
    with open(STARTUP_ITEM, "w", encoding="ascii", errors="replace") as f:
        f.write(
            "' VocabularyApp - watchdog 24/7 (AI + media + toast).\r\n"
            "' Runs hidden at logon. ASCII only (VBScript reads ANSI).\r\n"
            "Set shell = CreateObject(\"WScript.Shell\")\r\n"
            "shell.Run \"cmd /c \"\"%s\"\"\", 0, False\r\n" % CMD)
    print("✓ đã cài Startup:", STARTUP_ITEM)

    # 2) Task watchdog (AtStartup, SYSTEM) — CẦN ADMIN, bỏ qua nếu không có quyền.
    _ps(f"""
$ErrorActionPreference = 'Stop'
$a = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument '/c "{CMD}"' -WorkingDirectory '{BASE}'
$t = New-ScheduledTaskTrigger -AtStartup
$t2 = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(2) `
      -RepetitionInterval (New-TimeSpan -Minutes 30)
$s = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
      -StartWhenAvailable -RestartCount 5 -RestartInterval (New-TimeSpan -Minutes 5) `
      -ExecutionTimeLimit (New-TimeSpan -Days 3650)
$p = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
Unregister-ScheduledTask -TaskName '{TASK_WATCHDOG}' -Confirm:$false -ErrorAction SilentlyContinue
Register-ScheduledTask -TaskName '{TASK_WATCHDOG}' -Action $a -Trigger @($t,$t2) `
  -Settings $s -Principal $p -Description 'VocabularyApp: watchdog 24/7 (AI + media + thong bao)'
""")
    out = _ps(f"Get-ScheduledTask -TaskName '{TASK_WATCHDOG}' -ErrorAction SilentlyContinue | "
              f"Select-Object -ExpandProperty TaskName")
    if TASK_WATCHDOG in out:
        print("✓ đã cài task:", TASK_WATCHDOG)
    else:
        print("⚠ task", TASK_WATCHDOG,
              "cần QUYỀN ADMIN — đã cài Startup folder (chạy khi đăng nhập) thay thế.")

    # 3) Task check_done: bổ sung StartWhenAvailable
    _ps(f"""
$ErrorActionPreference = 'SilentlyContinue'
$t = Get-ScheduledTask -TaskName '{TASK_CHECK}'
if ($t) {{
  Set-ScheduledTask -TaskName '{TASK_CHECK}' `
    -Settings (New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries `
      -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 `
      -RestartInterval (New-TimeSpan -Minutes 10) `
      -ExecutionTimeLimit (New-TimeSpan -Hours 2))
}}
""")
    print("✓ đã cập nhật task:", TASK_CHECK)
    return 0


def uninstall() -> int:
    try:
        os.remove(STARTUP_ITEM)
        print("✓ đã gỡ Startup:", STARTUP_ITEM)
    except OSError:
        pass
    _ps(f"Unregister-ScheduledTask -TaskName '{TASK_WATCHDOG}' -Confirm:$false "
         f"-ErrorAction SilentlyContinue")
    return 0


def status() -> int:
    print(f"KIỂM TRA TỰ ĐỘNG CHẠY {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Startup folder : {'CÓ' if os.path.isfile(STARTUP_ITEM) else 'KHÔNG'}"
          f"  ({STARTUP_ITEM})")
    print(_ps(f"""
foreach ($n in @('{TASK_WATCHDOG}','{TASK_CHECK}')) {{
  $t = Get-ScheduledTask -TaskName $n -ErrorAction SilentlyContinue
  if (-not $t) {{ Write-Output "  $n : KHONG CO"; continue }}
  $info = Get-ScheduledTaskInfo -TaskName $n
  Write-Output ("  $n : " + $t.State + " | triggers=" + $t.Triggers.Count + `
    " | StartWhenAvailable=" + $t.Settings.StartWhenAvailable + `
    " | Restart=" + $t.Settings.RestartCount + `
    " | LastRun=" + $info.LastRunTime + " Result=" + $info.LastTaskResult)
}}
"""))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--install", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--uninstall", action="store_true")
    args = ap.parse_args()
    if args.install:
        return install()
    if args.uninstall:
        return uninstall()
    return status()


if __name__ == "__main__":
    sys.exit(main())
