"""Primary background launcher distributed with FB Liked Media Downloader.

Chrome stays a real, minimized browser because the authenticated extension
cannot run in headless Chrome.  The runner records only its own PIDs.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.request

HELPER_DIR = Path(__file__).resolve().parent
PROJECT_DIR = HELPER_DIR.parent
HELPER_SCRIPT = HELPER_DIR / "server.js"
CONFIG_PATH = Path(os.environ.get("LOCALAPPDATA", str(HELPER_DIR))) / "FB_Liked_Media_Addon" / "background_runner_config.json"
STATE_PATH = Path(os.environ.get("LOCALAPPDATA", str(HELPER_DIR))) / "FB_Liked_Media_Addon" / "background_runner_state.json"
TASK_NAME = "FB Liked Media Background Runner"
ACTIVITY_URL = "https://www.facebook.com/100007948240441/allactivity?activity_history=false&category_key=LIKEDPOSTS&manage_mode=false&should_load_landing_page=false"

def default_config():
    root = Path(os.environ.get("LOCALAPPDATA", "")) / "FB_Liked_Media_Addon" / "ChromeProfile"
    return {"enabled_at_logon": False, "chrome_user_data_dir": str(root), "chrome_profile_dir": "Default"}

def load_config():
    config = default_config()
    try: config.update(json.loads(CONFIG_PATH.read_text(encoding="utf-8")))
    except Exception: pass
    return config

def save_config(config):
    value = default_config(); value.update(config)
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    return value

def _load_state():
    try: return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception: return {}

def _save_state(data):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def _health():
    try:
        with urllib.request.urlopen("http://127.0.0.1:48765/health", timeout=2) as response: return response.status == 200
    except Exception: return False

def _find_chrome():
    for candidate in [Path(os.environ.get("PROGRAMFILES", "")) / "Google" / "Chrome" / "Application" / "chrome.exe", Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Google" / "Chrome" / "Application" / "chrome.exe"]:
        if candidate.is_file(): return str(candidate)
    return shutil.which("chrome") or shutil.which("chrome.exe")

def _popen(args):
    return subprocess.Popen(args, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def status():
    state = _load_state()
    return {"helper_running": _health(), "helper_pid": state.get("helper_pid"), "chrome_pid": state.get("chrome_pid"), "chrome_profile": state.get("chrome_user_data_dir", "")}

def start(config=None):
    if not HELPER_SCRIPT.is_file(): raise RuntimeError(f"Missing helper: {HELPER_SCRIPT}")
    node, chrome = shutil.which("node") or shutil.which("node.exe"), _find_chrome()
    if not node: raise RuntimeError("Node.js was not found.")
    if not chrome: raise RuntimeError("Google Chrome was not found.")
    cfg = load_config(); cfg.update({k: v for k, v in (config or {}).items() if v})
    profile_path = Path(cfg["chrome_user_data_dir"]).expanduser().resolve(); profile_path.mkdir(parents=True, exist_ok=True)
    state = _load_state()
    if not _health():
        helper = _popen([node, str(HELPER_SCRIPT)])
        for _ in range(20):
            time.sleep(.25)
            if _health(): state["helper_pid"] = helper.pid; break
        else: raise RuntimeError("The local Reel helper did not start.")
    browser = _popen([chrome, f"--user-data-dir={profile_path}", f"--profile-directory={cfg['chrome_profile_dir']}", "--start-minimized", "--no-first-run", "--no-default-browser-check", ACTIVITY_URL])
    state.update({"chrome_pid": browser.pid, "chrome_user_data_dir": str(profile_path), "chrome_profile_dir": cfg["chrome_profile_dir"], "started_at": int(time.time())})
    _save_state(state)
    return status()

def _kill_tree(pid):
    if pid: subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)

def stop():
    state = _load_state(); _kill_tree(state.get("chrome_pid")); _kill_tree(state.get("helper_pid"))
    try: STATE_PATH.unlink()
    except FileNotFoundError: pass
    return status()

def _task_command():
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    return f'"{pythonw if pythonw.is_file() else Path(sys.executable)}" "{Path(__file__).resolve()}" --start'

def set_logon_task(enabled):
    if enabled:
        subprocess.run(["schtasks", "/Create", "/TN", TASK_NAME, "/SC", "ONLOGON", "/TR", _task_command(), "/F", "/RL", "LIMITED"], check=True, capture_output=True, text=True)
    else:
        subprocess.run(["schtasks", "/Delete", "/TN", TASK_NAME, "/F"], check=False, capture_output=True, text=True)

def task_exists():
    return subprocess.run(["schtasks", "/Query", "/TN", TASK_NAME], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--start", action="store_true"); parser.add_argument("--stop", action="store_true"); parser.add_argument("--status", action="store_true"); args = parser.parse_args()
    try:
        print(json.dumps(start() if args.start else stop() if args.stop else status(), ensure_ascii=False))
    except Exception as error:
        print(json.dumps({"success": False, "error": str(error)}, ensure_ascii=False)); raise SystemExit(1)
