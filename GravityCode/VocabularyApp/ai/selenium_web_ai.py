"""
selenium_web_ai.py — Tầng Web AI #2: Selenium điều khiển Chrome thật.

Pattern anti-detect lấy từ `Python Project/MyApp/DlTangThuvien/utils/browser.py:24-29`
và quản lý Chrome thu nhỏ (không giết browser của user) từ
`DownloadImgFacebook/FacebookMediaHelper/background_runner.py:67-87`.

NGUYÊN TẮC:
  • KHÔNG dùng --headless (Gemini/ChatGPT chặn headless)
  • Profile RIÊNG cho app (không đụng browser đang mở của user)
  • Timeout có trần, luôn quit driver trong finally
  • Lỗi → trả [] (không chặn bài học)

Nền tảng hỗ trợ: gemini, chatgpt, copilot, grok, claude, perplexity, deepseek.
Mỗi nền tảng có bộ selector input/send/content riêng + chiến lược chờ
(`wait_min_ms` / `wait_max_ms`) — Grok stream Next.js chậm nên chờ lâu hơn.
"""

import io
import os
import time

CHROME_USER_DATA = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
    "VocabApp", "SeleniumProfile")

PLATFORMS = {
    "gemini": {
        "url": "https://gemini.google.com/app",
        "input": 'rich-textarea div[contenteditable="true"]',
        "input_alt": ".ql-editor",
        "input_alt2": "textarea",
        "send": 'button[aria-label*="Send" i], button[aria-label*="Gửi" i]',
        "content": "message-content",
        "wait_min_ms": 12000,
        "wait_max_ms": 90000,
    },
    "chatgpt": {
        "url": "https://chatgpt.com/",
        "input": "#prompt-textarea",
        "input_alt": "div[contenteditable='true']",
        "input_alt2": "textarea",
        "send": 'button[data-testid="send-button"]',
        "content": "div.markdown",
        "wait_min_ms": 12000,
        "wait_max_ms": 90000,
    },
    "copilot": {
        "url": "https://copilot.microsoft.com/",
        "input": 'div[role="textbox"][contenteditable="true"]',
        "input_alt": "textarea",
        "input_alt2": 'div[contenteditable="true"]',
        "send": 'button[data-automation-id*="send" i]',
        "content": ".ac-textBlock, .markdown-body",
        "wait_min_ms": 12000,
        "wait_max_ms": 90000,
    },
    # Grok: DOM đổi nhanh → nhiều fallback + chờ lâu hơn (stream Next.js chậm)
    "grok": {
        "url": "https://grok.com/",
        "input": 'div[data-testid="grok-input"]',
        "input_alt": 'textarea[data-testid="grok-input"]',
        "input_alt2": 'div[contenteditable="true"][role="textbox"]',
        "send": 'button[data-testid="submit-button"], button[aria-label*="Send" i], button[aria-label*="Gửi" i]',
        "content": "div[data-testid='grok-response'], .response-content-markdown, .prose",
        "wait_min_ms": 20000,
        "wait_max_ms": 150000,
    },
    # Claude: ô nhập là ProseMirror contenteditable
    "claude": {
        "url": "https://claude.ai/new",
        "input": 'div[contenteditable="true"]',
        "input_alt": "div[ProseMirror]",
        "input_alt2": "textarea",
        "send": 'button[aria-label*="Send" i], button[aria-label*="Gửi" i]',
        "content": "div[data-testid='claude-message'], .font-claude-message",
        "wait_min_ms": 15000,
        "wait_max_ms": 120000,
    },
    # Perplexity: textarea ask-input
    "perplexity": {
        "url": "https://www.perplexity.ai/",
        "input": 'textarea[data-testid="ask-input"]',
        "input_alt": "textarea",
        "input_alt2": 'div[contenteditable="true"]',
        "send": 'button[aria-label*="Submit" i], button[aria-label*="Send" i]',
        "content": ".prose, div[contentid]",
        "wait_min_ms": 15000,
        "wait_max_ms": 120000,
    },
    # DeepSeek: textarea#dummy-input
    "deepseek": {
        "url": "https://chat.deepseek.com/",
        "input": "textarea#dummy-input",
        "input_alt": "textarea",
        "input_alt2": 'div[contenteditable="true"]',
        "send": 'button[aria-label*="Send" i], button[aria-label*="Gửi" i]',
        "content": ".ds-markdown--block, .prose",
        "wait_min_ms": 15000,
        "wait_max_ms": 120000,
    },
}

MIN_IMAGE_BYTES = 5 * 1024


def _split_selectors(sel: str) -> list:
    """Tách chuỗi selector phân tách bởi dấu phẩy (giữ thứ tự ưu tiên)."""
    return [s.strip() for s in str(sel or "").split(",") if s.strip()]


def _make_driver(headless: bool = False):
    """Tạo Chrome driver với profile riêng + anti-detect."""
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service

    opts = webdriver.ChromeOptions()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--no-first-run")
    opts.add_argument("--no-default-browser-check")
    opts.add_argument("--disable-notifications")
    opts.add_argument("--window-size=1600,1000")
    opts.add_argument(f"--user-data-dir={CHROME_USER_DATA}")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 2,
    })

    driver = None
    try:
        driver = webdriver.Chrome(service=Service(), options=opts)
    except Exception:
        driver = webdriver.Chrome(options=opts)
    driver.set_page_load_timeout(90)
    return driver


def _wait_stable(driver, selector: str, min_ms: int = 15000, max_ms: int = 60000):
    """Chờ nội dung ổn định (độ dài text đừng thay đổi quá 30 ký tự).

    Nhiều selector dạng "a, b" ⇒ thử theo thứ tự ưu tiên, lấy phần tử cuối
    của nhóm đầu tiên có kết quả (phần tử mới nhất)."""
    from selenium.webdriver.support.ui import WebDriverWait

    parts = _split_selectors(selector) or [selector]
    start = time.time()
    last_len = -1
    stable_since = None
    while (time.time() - start) * 1000 < max_ms:
        try:
            for part in parts:
                els = driver.find_elements("css selector", part)
                if not els:
                    continue
                txt = els[-1].text or ""
                if len(txt) != last_len:
                    last_len = len(txt)
                    stable_since = time.time()
                elif txt and (time.time() - stable_since) * 1000 >= min_ms:
                    return els[-1]
                break
        except Exception:
            pass
        time.sleep(1.5)
    return None


def _fill_input(driver, el, text: str) -> bool:
    """Điền ô nhập. contenteditable (Grok/Claude/Perplexity) cần fallback JS."""
    try:
        el.click()
    except Exception:
        pass
    try:
        el.send_keys(text)
    except Exception:
        pass
    # Kiểm tra đã vào chưa
    try:
        tag = (el.tag_name or "").lower()
        got = el.get_attribute("value") if tag in ("textarea", "input") else el.get_attribute("innerText")
    except Exception:
        got = ""
    if got and len(got.strip()) >= 10:
        return True
    # Fallback: set trực tiếp + bắn event input (React/Vue cần event này)
    try:
        driver.execute_script(
            "var el = arguments[0], t = arguments[1];"
            "el.focus();"
            "if (el.isContentEditable) {"
            "  el.innerHTML = '';"
            "  var d = document.createElement('div'); d.textContent = t; el.appendChild(d);"
            "  el.dispatchEvent(new InputEvent('input', {bubbles:true, inputType:'insertText', data:t}));"
            "} else {"
            "  var proto = (el.tagName === 'TEXTAREA') ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;"
            "  var setter = Object.getOwnPropertyDescriptor(proto, 'value');"
            "  if (setter && setter.set) setter.set.call(el, t); else el.value = t;"
            "  el.dispatchEvent(new Event('input', {bubbles:true}));"
            "  el.dispatchEvent(new Event('change', {bubbles:true}));"
            "}"
            "return true;",
            el, text,
        )
        return True
    except Exception:
        return False


def _click_send(driver, selector: str, fallback_el=None) -> bool:
    """Bấm nút gửi (thử từng selector theo thứ tự). Trả True nếu bấm được."""
    for part in _split_selectors(selector):
        try:
            btn = driver.find_element("css selector", part)
            btn.click()
            return True
        except Exception:
            continue
    if fallback_el is not None:
        try:
            fallback_el.send_keys("\n")
            return True
        except Exception:
            pass
    return False


def _extract_images(container) -> list:
    """Trích <img> trong container, lọc rác, tải về bytes."""
    import requests
    out = []
    try:
        imgs = container.find_elements("css selector", "img")
    except Exception:
        return out
    for im in imgs:
        try:
            src = im.get_attribute("src") or im.get_attribute("data-src") or ""
            alt = (im.get_attribute("alt") or "").lower()
            w = im.size.get("width", 0) if im.size else 0
            h = im.size.get("height", 0) if im.size else 0
        except Exception:
            continue
        if not src.lower().startswith(("http://", "https://")):
            continue
        if any(t in alt for t in ("icon", "avatar", "logo", "sticker", "badge")):
            continue
        if w and w <= 150:
            continue
        if h and h <= 150:
            continue
        try:
            r = requests.get(src, timeout=30, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Referer": "https://gemini.google.com/",
            })
            ctype = (r.headers.get("content-type") or "").split(";")[0].lower()
            if r.status_code != 200 or not ctype.startswith("image/"):
                continue
            if ctype == "image/svg+xml" or len(r.content) < MIN_IMAGE_BYTES:
                continue
            out.append({"bytes": r.content, "content_type": ctype,
                        "url": src, "alt": alt, "provider": "selenium"})
        except Exception:
            continue
    return out


def fetch_images_selenium(language: str, day: int, lesson: dict,
                          platform: str = "gemini", log_fn=None,
                          timeout: int = 240) -> list:
    """Mở web AI bằng Selenium, gửi prompt, trích ảnh. Trả list dict ảnh."""
    def _log(m):
        if log_fn:
            try:
                log_fn(m)
            except Exception:
                pass

    conf = PLATFORMS.get(platform) or PLATFORMS["gemini"]
    from ai.web_ai_bridge import build_web_prompt
    prompt = build_web_prompt(language, day, lesson)

    driver = None
    try:
        os.makedirs(CHROME_USER_DATA, exist_ok=True)
        _log(f"   🖥️ Selenium: khởi động Chrome (profile riêng)...")
        driver = _make_driver(headless=False)
        driver.get(conf["url"])
        time.sleep(4)

        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait

        wait = WebDriverWait(driver, 30)
        el = None
        for sel in (conf["input"], conf["input_alt"], conf.get("input_alt2")):
            if not sel:
                continue
            try:
                el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, sel)))
                break
            except Exception:
                continue
        if el is None:
            _log("   ⚠ Selenium: không tìm thấy ô nhập (DOM đã đổi?)")
            return []

        if not _fill_input(driver, el, prompt):
            _log("   ⚠ Selenium: không điền được ô nhập.")
            return []
        time.sleep(1.5)
        if not _click_send(driver, conf["send"], el):
            _log("   ⚠ Selenium: không bấm được nút gửi.")

        # Chiến lược chờ riêng theo nền tảng (Grok stream chậm ⇒ chờ lâu hơn)
        # timeout tính bằng GIÂY ⇒ đổi sang ms cho _wait_stable
        wait_min = int(conf.get("wait_min_ms", 12000))
        wait_max = int(min(int(conf.get("wait_max_ms", 90000)), int(timeout) * 1000))
        container = _wait_stable(driver, conf["content"],
                                 min_ms=wait_min, max_ms=wait_max)
        if container is None:
            _log("   ⚠ Selenium: nội dung không ổn định (timeout)")
            return []
        imgs = _extract_images(container)
        _log(f"   🖥️ Selenium: lấy được {len(imgs)} ảnh.")
        return imgs
    except Exception as e:
        _log(f"   ⚠ Selenium lỗi: {e}")
        return []
    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass
