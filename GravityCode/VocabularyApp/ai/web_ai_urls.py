"""
web_ai_urls.py — Mở trực tiếp các ứng dụng AI web để tra cứu nhanh.

Cơ chế AN TOÀN, CHI PHÍ 0, RỦI RO 0:
  1. Copy prompt vào clipboard
  2. Mở tab bằng trình duyệt mặc định
  3. Người dùng tự dán & Enter

⛔ KHÔNG dùng deep-link `?q=` — đã kiểm tra Chrome History: Gemini/Grok/ChatGPT
   KHÔNG hỗ trợ deep-link prompt ổn định (chỉ có `?hl=vi`, `?rid=`, `?pageId=none`).
   History cũng cho thấy `google.com/sorry/index` (CAPTCHA do truy cập tự động)
   và `grok.com/tos-gate` ⇒ tự động hoá UI có rủi ro ban account ⇒ chỉ dùng
   "mở tab + copy prompt", người dùng tự quyết định.

Bảng nền tảng được đồng bộ với `ai/openclaw_web_ai.py` và
`addon/VocabAIExtractor/content_script.js` (cùng bộ selector).
"""

import os
import shutil
import subprocess
import sys
import webbrowser

# ─── Bảng nền tảng ──────────────────────────────────────────────────────────
PLATFORMS = {
    "gemini": {
        "label": "Gemini",
        "url": "https://gemini.google.com/app?hl=vi",
        "icon": "🔮",
        "note": "Đã đăng nhập sẵn trên máy bạn",
    },
    "grok": {
        "label": "Grok",
        "url": "https://grok.com/",
        "icon": "🧠",
        "note": "Có ToS gate — đọc kỹ trước khi dùng tự động",
    },
    "chatgpt": {
        "label": "ChatGPT",
        "url": "https://chatgpt.com/",
        "icon": "💬",
        "note": "",
    },
    "claude": {
        "label": "Claude",
        "url": "https://claude.ai/new",
        "icon": "🦎",
        "note": "",
    },
    "copilot": {
        "label": "Copilot",
        "url": "https://copilot.microsoft.com/",
        "icon": "🐧",
        "note": "",
    },
    "perplexity": {
        "label": "Perplexity",
        "url": "https://www.perplexity.ai/",
        "icon": "🔎",
        "note": "Tra cứu nhanh + có nguồn",
    },
    "deepseek": {
        "label": "DeepSeek",
        "url": "https://chat.deepseek.com/",
        "icon": "🐳",
        "note": "",
    },
    "aistudio": {
        "label": "AI Studio (API key)",
        "url": "https://aistudio.google.com/app/api-keys",
        "icon": "🔑",
        "note": "Quản lý API key Gemini",
    },
}


# ─── Clipboard (Windows, không cần thư viện ngoài) ───────────────────────────
def copy_to_clipboard(text: str) -> bool:
    """Copy text vào clipboard. Ưu tiên ctypes (Windows), fallback pyperclip/tkinter."""
    if not text:
        return False
    # 1) ctypes — Windows native
    if os.name == "nt":
        try:
            import ctypes
            from ctypes import wintypes

            CF_UNICODETEXT = 13
            GMEM_MOVEABLE = 0x0002
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32

            user32.OpenClipboard.argtypes = [wintypes.HWND]
            user32.OpenClipboard.restype = wintypes.BOOL
            user32.EmptyClipboard.restype = wintypes.BOOL
            user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
            user32.SetClipboardData.restype = wintypes.HANDLE
            kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
            kernel32.GlobalLock.restype = wintypes.LPVOID

            if not user32.OpenClipboard(None):
                return False
            try:
                user32.EmptyClipboard()
                data = text + "\0"
                size = len(data) * ctypes.sizeof(ctypes.c_wchar)
                handle = kernel32.GlobalAlloc(GMEM_MOVEABLE, size)
                locked = kernel32.GlobalLock(handle)
                ctypes.memmove(locked, ctypes.create_unicode_buffer(data), size)
                kernel32.GlobalUnlock(handle)
                user32.SetClipboardData(CF_UNICODETEXT, handle)
                return True
            finally:
                user32.CloseClipboard()
        except Exception:
            pass
    # 2) pyperclip
    try:
        import pyperclip
        pyperclip.copy(text)
        return True
    except Exception:
        pass
    # 3) tkinter (dùng chính CTk root nếu có)
    try:
        import tkinter as tk
        r = tk.Tk()
        r.withdraw()
        r.clipboard_clear()
        r.clipboard_append(text)
        r.update()
        r.destroy()
        return True
    except Exception:
        return False
    return False


# ─── Prompt builder ──────────────────────────────────────────────────────────
def build_lookup_prompt(language: str = "", word: str = "", meaning: str = "",
                        extra: str = "") -> str:
    """Prompt tra cứu nhanh 1 từ (dán vào Gemini/Grok)."""
    lines = []
    if word:
        lines.append(f"Từ vựng: {word}")
    if meaning:
        lines.append(f"Nghĩa tiếng Việt: {meaning}")
    if language:
        lines.append(f"Ngôn ngữ: {language}")
    if extra:
        lines.append(extra)
    lines += [
        "",
        "Cho tôi: 1) phiên âm chuẩn IPA kèm giải thích khẩu hình (môi/lưỡi/răng), "
        "2) nghĩa + 1 ví dụ tự nhiên, 3) 1-2 cụm từ thường dùng đi kèm, "
        "4) nguồn tham khảo (URL nếu có).",
    ]
    return "\n".join(lines)


def build_course_prompt(language: str, day_title: str = "", words=None) -> str:
    """Prompt tạo nội dung cho 1 ngày học."""
    words = words or []
    lines = [
        f"Dạy tôi bài {day_title}" if day_title else "Dạy tôi bài hôm nay",
        f"Ngôn ngữ: {language}",
    ]
    if words:
        lines.append("Từ vựng cần dạy: " + ", ".join(str(w) for w in words[:15]))
    lines += [
        "",
        "Mỗi từ: nghĩa tiếng Việt, phiên âm IPA, 1 ví dụ tự nhiên, 1 cụm thường dùng.",
        "Sau đó viết một đoạn hội thoại ngắn (6 lượt) dùng các từ trên.",
    ]
    return "\n".join(lines)


# ─── Mở trình duyệt ─────────────────────────────────────────────────────────
def open_platform(platform: str = "gemini", prompt: str = "", log_fn=None) -> dict:
    """Copy prompt (nếu có) + mở tab. Trả dict kết quả."""
    def _log(m):
        if log_fn:
            try:
                log_fn(m)
            except Exception:
                pass

    conf = PLATFORMS.get(platform)
    if not conf:
        return {"ok": False, "error": f"nền tảng không hỗ trợ: {platform}"}

    copied = False
    if prompt:
        copied = copy_to_clipboard(prompt)
        if copied:
            _log(f"📋 Đã copy prompt vào clipboard ({len(prompt)} ký tự).")
        else:
            _log("⚠ Không copy được clipboard — hãy tự dán prompt.")

    url = conf["url"]
    try:
        webbrowser.open(url, new=2)
    except Exception as e:
        return {"ok": False, "error": f"không mở được trình duyệt: {e}"}

    _log(f"{conf['icon']} Đã mở {conf['label']}: {url}")
    if conf.get("note"):
        _log(f"   ℹ️  {conf['note']}")
    return {"ok": True, "platform": platform, "url": url, "copied": copied,
            "label": conf["label"]}


def open_with_default_browser(url: str) -> bool:
    """Mở URL bằng trình duyệt mặc định (fallback khi webbrowser lỗi)."""
    try:
        if os.name == "nt":
            os.startfile(url)
            return True
    except Exception:
        pass
    try:
        return webbrowser.open(url, new=2)
    except Exception:
        return False


# ─── CLI ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if "--list" in sys.argv:
        for k, v in PLATFORMS.items():
            print(f"{v['icon']} {k:12s} {v['label']:18s} {v['url']}")
    elif "--open" in sys.argv:
        i = sys.argv.index("--open")
        plat = sys.argv[i + 1] if len(sys.argv) > i + 1 else "gemini"
        r = open_platform(plat, log_fn=print)
        print("KẾT QUẢ:", r)
    else:
        print(__doc__)
        print("\nDùng: python -m ai.web_ai_urls --list | --open <platform>")
