r"""
openclaw_web_ai.py — Tầng Web AI #3: điều khiển Chrome qua OpenClaw browser CLI.

OpenClaw đã cài trên máy: npm `openclaw@2026.9.4` + `C:\Users\games\.openclaw\`.

3 BLOCKER đã kiểm chứng (xem skill `vocab_ai_media` mục 6):
  1. PHẢI gọi `openclaw.cmd` (không phải `openclaw`) — `subprocess` không nối
     `.cmd` tự động trên Windows ⇒ `FileNotFoundError [WinError 2]`.
  2. `wait` có selector là **POSITIONAL** (`wait "body"`, không phải `--selector`),
     cờ thời gian là `--time` (không phải `--time-ms`).
  3. KHÔNG có lệnh `browser text` / `browser html` → phải dùng `evaluate --fn`.
     Ngoài ra `--timeout` là timeout của Gateway RPC (30000) còn `--timeout-ms`
     mới là timeout chờ điều kiện (20000).

Profile: `openclaw` (default, port 18800) là profile SẠCH — không có session đăng nhập
⇒ vô dụng cho web AI. Phải dùng `--browser-profile chrome` (extension relay, 18799,
cần pair) hoặc `user` (Chrome DevTools MCP).

2 LỖI KỸ THUẬT đã sửa:
  1. `_pick_profile()` dùng `status` để kiểm tra — nhưng `status` trả ok=true
     dù extension CHƯA kết nối (đã kiểm chứng: status báo running/cdpReady
     trong khi `tabs` lỗi). Đổi sang `tabs`: coi là kết nối được nếu parse
     được JSON và có key `tabs` (kể cả list rỗng).
  2. Chống ban account: gặp `google.com/sorry` hoặc 429/503/rate-limit ⇒
     khóa tầng openclaw `_BLOCK_SECONDS` (30 phút) rồi trả [].

Nền tảng hỗ trợ: gemini, chatgpt, copilot, grok, claude, perplexity, deepseek.
"""

import json
import os
import re
import shutil
import subprocess
import time

# Profile ưu tiên cho web AI (cần đã đăng nhập)
PREFERRED_PROFILES = ("chrome", "user", "openclaw")

PLATFORM_URL = {
    "gemini": "https://gemini.google.com/app",
    "chatgpt": "https://chatgpt.com/",
    "copilot": "https://copilot.microsoft.com/",
    "grok": "https://grok.com/",
    "claude": "https://claude.ai/new",
    "perplexity": "https://www.perplexity.ai/",
    "deepseek": "https://chat.deepseek.com/",
}

# Selector ô nhập — thử theo thứ tự, lấy cái đầu tiên tìm thấy
INPUT_SELECTOR = {
    "gemini": [
        'rich-textarea div[contenteditable="true"]',
        ".ql-editor",
        "textarea",
    ],
    "chatgpt": [
        "#prompt-textarea",
        'div[contenteditable="true"]',
        "textarea",
    ],
    "copilot": [
        'div[role="textbox"][contenteditable="true"]',
        "textarea",
        'div[contenteditable="true"]',
    ],
    # Grok đổi DOM rất nhanh ⇒ nhiều fallback
    "grok": [
        'div[data-testid="grok-input"]',
        'textarea[data-testid="grok-input"]',
        'div[contenteditable="true"][role="textbox"]',
        'div[contenteditable="true"]',
    ],
    "claude": [
        'div[contenteditable="true"]',
        "textarea",
        "div[ProseMirror]",
    ],
    "perplexity": [
        'textarea[data-testid="ask-input"]',
        "textarea",
        'div[contenteditable="true"]',
    ],
    "deepseek": [
        "textarea#dummy-input",
        "textarea",
        'div[contenteditable="true"]',
    ],
}

# Selector nút gửi — thử theo thứ tự, lấy cái đầu tiên tìm thấy
SEND_SELECTOR = {
    "gemini": [
        'button[aria-label*="Send" i]',
        'button[aria-label*="Gửi" i]',
        'button[aria-label*="Submit" i]',
    ],
    "chatgpt": [
        'button[data-testid="send-button"]',
        'button[aria-label*="Send" i]',
    ],
    "copilot": [
        'button[data-automation-id*="send" i]',
        'button[aria-label*="Send" i]',
    ],
    "grok": [
        'button[data-testid="submit-button"]',
        'button[aria-label*="Send" i]',
        'button[aria-label*="Gửi" i]',
    ],
    "claude": [
        'button[aria-label*="Send" i]',
        'button[aria-label*="Gửi" i]',
    ],
    "perplexity": [
        'button[aria-label*="Submit" i]',
        'button[aria-label*="Send" i]',
    ],
    "deepseek": [
        'button[aria-label*="Send" i]',
        'button[aria-label*="Gửi" i]',
    ],
}

# Selector nội dung (dùng cho evaluate --fn) — thứ tự = mức ưu tiên
CONTENT_SELECTOR = {
    "gemini": ["message-content"],
    "chatgpt": ["div.markdown"],
    "copilot": [".ac-textBlock", ".markdown-body"],
    "grok": [
        'div[data-testid="grok-response"]',
        ".response-content-markdown",
        ".prose",
    ],
    "claude": [
        'div[data-testid="claude-message"]',
        ".font-claude-message",
    ],
    "perplexity": [
        ".prose",
        "div[contentid]",
    ],
    "deepseek": [
        ".ds-markdown--block",
        ".prose",
    ],
}

CLI_TIMEOUT = 60

# ─── Chống ban account ──────────────────────────────────────────────────────
# Google/AI trả trang "sorry" hoặc lỗi 429/503 ⇒ dừng hẳn tầng openclaw
_BLOCK_SECONDS = 1800          # 30 phút
_blocked_until = 0.0           # timestamp (time.time) hết hạn

# Dấu hiệu bị chặn (chỉ so khớp cụm từ, không nhầm với nội dung bài học)
_BLOCK_PHRASES = (
    "google.com/sorry",
    "sorry/index",
    "unusual traffic",
    "rate limit",
    "too many requests",
    "quota exceeded",
    "service unavailable",
    "temporarily blocked",
    "recaptcha",
)

# Mã lỗi 429/503 chỉ được tính khi đi kèm ngữ cảnh lỗi (tránh nhầm số trong bài học)
_CODE_RE = re.compile(
    r"\b(429|503)\b[^0-9]{0,24}(?:too many|rate|unavailable|error|service|forbidden)"
    r"|(?:too many|rate limit|service unavailable|error|forbidden)[^0-9]{0,24}\b(429|503)\b",
    re.IGNORECASE,
)


def _detect_block(text: str) -> str:
    """Trả lý do bị chặn (chuỗi rỗng = không bị chặn)."""
    if not text:
        return ""
    low = text.lower()
    for p in _BLOCK_PHRASES:
        if p in low:
            return p
    return ""


def _detect_block_code(text: str) -> str:
    """Phát hiện mã lỗi HTTP 429/503 kèm ngữ cảnh lỗi."""
    if not text:
        return ""
    m = _CODE_RE.search(text)
    if m:
        return m.group(1) or m.group(2) or ""
    return ""


def _is_blocked() -> bool:
    """Còn đang trong thời gian tạm khóa không."""
    return time.time() < _blocked_until


def block_state() -> int:
    """Số giây còn lại của lệnh tạm khóa (0 = không bị khóa)."""
    return max(0, int(_blocked_until - time.time()))


def _trigger_block(reason: str, log_fn=None) -> None:
    """Khóa tầng openclaw trong _BLOCK_SECONDS giây."""
    global _blocked_until
    _blocked_until = time.time() + _BLOCK_SECONDS
    if log_fn:
        log_fn(f"   ⛔ OpenClaw bị chặn ({reason}) — dừng {_BLOCK_SECONDS // 60} phút "
               f"để tránh ban account.")


def _cli_path() -> str:
    """Tìm openclaw.cmd. ƯU TIÊN openclaw.cmd (Windows không nối .cmd tự động)."""
    cand = shutil.which("openclaw.cmd")
    if cand:
        return cand
    cand = shutil.which("openclaw")
    if cand:
        return cand
    for p in (r"C:\Users\games\AppData\Roaming\npm\openclaw.cmd",
              r"C:\Users\games\AppData\Roaming\npm\openclaw"):
        if os.path.exists(p):
            return p
    return "openclaw.cmd"


def run_cli(args: list, timeout: int = CLI_TIMEOUT) -> dict:
    """Gọi `openclaw <args>` và parse JSON output. Trả {} nếu lỗi."""
    cmd = [_cli_path()] + list(args)
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return {"ok": False, "error": {"message": "không tìm thấy openclaw.cmd"}}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": {"message": f"timeout > {timeout}s"}}
    except Exception as e:
        return {"ok": False, "error": {"message": f"{type(e).__name__}: {e}"}}
    raw = (p.stdout or "").strip() or (p.stderr or "").strip()
    if not raw:
        return {"ok": False, "error": {"message": f"rc={p.returncode} (rỗng)"}}
    try:
        return json.loads(raw)
    except Exception:
        return {"ok": False, "error": {"message": raw[:200]}}


def _browser(args: list, profile: str = None, timeout: int = CLI_TIMEOUT) -> dict:
    full = ["browser"]
    if profile:
        full += ["--browser-profile", profile]
    full += args + ["--json"]
    return run_cli(full, timeout=timeout)


def openclaw_available() -> tuple:
    """(khả dụng, lý do)."""
    path = _cli_path()
    if not os.path.exists(path) and shutil.which(path) is None:
        return False, "không tìm thấy openclaw.cmd"
    r = _browser(["status"], timeout=25)
    if not r or r.get("ok") is False:
        msg = ((r or {}).get("error") or {}).get("message", "không phản hồi")
        return False, f"openclaw chưa sẵn sàng: {msg[:80]}"
    return True, f"running={r.get('running')} profile={r.get('profile')}"


def _profile_connected(profile: str) -> bool:
    """Profile có thật sự kết nối được không?

    PHẢI dùng `tabs` chứ không dùng `status`: `status` có thể trả ok=true
    dù extension CHƯA kết nối (đã kiểm chứng: status báo running/cdpReady
    trong khi `tabs` lỗi "Playwright page target identities are temporarily
    unavailable"). `tabs` mới chứng minh extension đã pair.
    """
    r = _browser(["tabs"], profile=profile, timeout=20)
    if not isinstance(r, dict):
        return False
    if r.get("ok") is False:
        return False
    return "tabs" in r          # list rỗng vẫn tính là kết nối được


def _pick_profile(log_fn=None) -> str:
    """Chọn profile có session đăng nhập (chrome > user > openclaw)."""
    for p in PREFERRED_PROFILES:
        if _profile_connected(p):
            if p == "openclaw":
                # profile sạch → vô dụng cho web AI, nhưng vẫn dùng được nếu không có lựa chọn
                if log_fn:
                    log_fn(f"   🦞 OpenClaw: dùng profile '{p}' (sạch, chưa đăng nhập)")
            else:
                if log_fn:
                    log_fn(f"   🦞 OpenClaw: dùng profile '{p}' (extension đã kết nối)")
            return p
        if log_fn:
            log_fn(f"   🦞 OpenClaw: profile '{p}' chưa kết nối — bỏ qua.")
    return "openclaw"


def _download(url: str, referer: str = "https://gemini.google.com/"):
    import requests
    try:
        r = requests.get(url, timeout=30, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Referer": referer,
        })
        ctype = (r.headers.get("content-type") or "").split(";")[0].lower()
        if r.status_code != 200 or not ctype.startswith("image/"):
            return b"", ""
        if ctype == "image/svg+xml" or len(r.content) < 5 * 1024:
            return b"", ""
        return r.content, ctype
    except Exception:
        return b"", ""


def fetch_images_openclaw(language: str, day: int, lesson: dict,
                          platform: str = "gemini", log_fn=None,
                          timeout: int = 240) -> list:
    """Điều khiển Chrome qua OpenClaw: mở web AI, gõ prompt, trích ảnh."""
    def _log(m):
        if log_fn:
            try:
                log_fn(m)
            except Exception:
                pass

    # Đang bị khóa do gặp trang "sorry"/rate-limit ⇒ dừng hẳn, không gọi CLI
    if _is_blocked():
        _log(f"   ⛔ OpenClaw đang bị tạm khóa (còn {block_state() // 60} phút) — bỏ qua.")
        return []

    ok, reason = openclaw_available()
    if not ok:
        _log(f"   🦞 OpenClaw không khả dụng: {reason}")
        return []

    profile = _pick_profile(log_fn)
    url = PLATFORM_URL.get(platform, PLATFORM_URL["gemini"])
    content_sels = CONTENT_SELECTOR.get(platform, ["message-content"])

    # 1) Mở tab
    r = _browser(["open", url], profile=profile, timeout=45)
    if not r or r.get("ok") is False:
        _log(f"   ⚠ OpenClaw không mở được tab: {str(r)[:120]}")
        return []
    target = (r.get("suggestedTargetId") or r.get("tabId") or r.get("targetId") or "")
    _log(f"   🦞 OpenClaw: đã mở {url} (target={target})")

    # 2) Chờ nạp
    _browser(["wait", "--time", "4000"], profile=profile, timeout=30)

    # 3) Gõ prompt qua evaluate (bypass selector phức tạp)
    from ai.web_ai_bridge import build_web_prompt
    prompt = build_web_prompt(language, day, lesson)
    js = """
    (function(p){
      var sels = %s;
      var el = null;
      for (var i = 0; i < sels.length; i++) {
        var e = document.querySelector(sels[i]);
        if (e) { el = e; break; }
      }
      if (!el) { var ta = document.querySelector('textarea'); if (ta) el = ta; }
      if (!el) { var ce = document.querySelector('div[contenteditable="true"]'); if (ce) el = ce; }
      if (!el) return 'NO_INPUT';
      el.focus();
      if (el.isContentEditable) {
        el.innerHTML = '';
        var t = document.createElement('div'); t.textContent = p; el.appendChild(t);
        el.dispatchEvent(new InputEvent('input', {bubbles:true, inputType:'insertText', data:p}));
      } else {
        var proto = (el.tagName === 'TEXTAREA') ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
        var setter = Object.getOwnPropertyDescriptor(proto, 'value');
        if (setter && setter.set) setter.set.call(el, p); else el.value = p;
        el.dispatchEvent(new Event('input', {bubbles:true}));
        el.dispatchEvent(new Event('change', {bubbles:true}));
      }
      return 'OK';
    })(%s);
    """
    input_sels = INPUT_SELECTOR.get(platform, ["textarea"])
    js = js % (json.dumps(input_sels), json.dumps(prompt))
    r = _browser(["evaluate", "--fn", js] + (["--target-id", target] if target else []),
                 profile=profile, timeout=40)
    if not r or not isinstance(r, dict) or str(r.get("result", "")).startswith("NO_INPUT"):
        _log("   ⚠ OpenClaw: không tìm thấy ô nhập trên web AI.")
        return []

    # 4) Gửi (nút send theo selector, fallback Enter)
    send_js = """
    (function(){
      var sels = %s;
      for (var i = 0; i < sels.length; i++) {
        var b = document.querySelector(sels[i]);
        if (b) { try { b.click(); } catch (e) {} return 'CLICKED'; }
      }
      var ta = document.querySelector('textarea');
      if (ta) {
        ta.focus();
        ta.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',code:'Enter',keyCode:13,which:13,bubbles:true}));
        return 'ENTER';
      }
      return 'NONE';
    })();
    """ % json.dumps(SEND_SELECTOR.get(platform, ['button[aria-label*="Send" i]']))
    _browser(["evaluate", "--fn", send_js] + (["--target-id", target] if target else []),
              profile=profile, timeout=30)

    # 5) Chờ ổn định (kèm dò trang "sorry"/rate-limit)
    deadline = time.time() + timeout
    last = -1
    stable = 0
    while time.time() < deadline:
        time.sleep(4)
        js_len = """
        (function(){
          var sels = %s; var els = [];
          for (var i = 0; i < sels.length; i++) {
            var g = document.querySelectorAll(sels[i]);
            if (g && g.length) { els = Array.from(g); break; }
          }
          var e = els.length ? els[els.length - 1] : null;
          var txt = e ? (e.innerText || '') : '';
          return { len: txt.length,
                   head: txt.slice(0, 1500),
                   url: (location.href || ''),
                   body: (document.body ? (document.body.innerText || '').slice(0, 1200) : '') };
        })();
        """ % json.dumps(content_sels)
        r = _browser(["evaluate", "--fn", js_len] + (["--target-id", target] if target else []),
                     profile=profile, timeout=30)
        res = r.get("result") if isinstance(r, dict) else None
        if isinstance(res, dict):
            n = int(res.get("len") or 0)
            url_now = str(res.get("url") or "")
            head = str(res.get("head") or "")
            body = str(res.get("body") or "")
            # Dò ban: URL trang sorry + câu báo rate-limit trong nội dung
            reason = (_detect_block(url_now) or _detect_block(head)
                      or _detect_block(body))
            code = _detect_block_code(url_now) or _detect_block_code(body[:500])
            if reason or code:
                _trigger_block(reason or code, _log)
                return []
        else:
            n = 0
        if n and n == last:
            stable += 1
            if stable >= 3:
                break
        else:
            stable = 0
        last = n

    # 6) Trích ảnh
    js_imgs = """
    (function(){
      var sels = %s; var els = [];
      for (var i = 0; i < sels.length; i++) {
        var g = document.querySelectorAll(sels[i]);
        if (g && g.length) { els = Array.from(g); break; }
      }
      var e = els.length ? els[els.length - 1] : null;
      if (!e) return [];
      return Array.from(e.querySelectorAll('img')).map(function(i){
        return {url: i.currentSrc || i.src || '', alt: i.alt || '',
                w: i.naturalWidth || 0, h: i.naturalHeight || 0};
      }).filter(function(x){return x.url.indexOf('http')===0;});
    })();
    """ % json.dumps(content_sels)
    r = _browser(["evaluate", "--fn", js_imgs] + (["--target-id", target] if target else []),
                 profile=profile, timeout=40)
    arr = r.get("result") if isinstance(r, dict) else None
    if not isinstance(arr, list):
        _log("   ⚠ OpenClaw: không lấy được danh sách ảnh.")
        return []

    out = []
    for im in arr:
        alt = (im.get("alt") or "").lower()
        if any(t in alt for t in ("icon", "avatar", "logo", "sticker", "badge")):
            continue
        if im.get("w") and im["w"] <= 150:
            continue
        if im.get("h") and im["h"] <= 150:
            continue
        raw, ctype = _download(im.get("url", ""))
        if raw:
            out.append({"bytes": raw, "content_type": ctype,
                        "url": im.get("url"), "alt": im.get("alt", ""),
                        "provider": "openclaw"})
    _log(f"   🦞 OpenClaw: lấy được {len(out)} ảnh.")

    # 7) Dọn tab
    if target:
        _browser(["close", target], profile=profile, timeout=20)
    return out
