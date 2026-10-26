"""
web_ai_bridge.py — Tầng Web AI: lấy nội dung + ảnh từ trang Gemini/ChatGPT/Copilot.

3 cơ chế, tự chuyển theo thứ tự:
  2a) Chrome addon  — app đẩy job vào queue, addon gửi prompt lên web AI,
                      trả HTML + ảnh base64 về bridge (http://127.0.0.1:5690)
  2b) Selenium      — tự mở Chrome, nhập prompt, chờ ổn định, trích nội dung + ảnh
  2c) OpenClaw      — điều khiển Chrome qua `openclaw browser` CLI

Nguyên tắc: lỗi 1 tầng KHÔNG chặn các tầng sau; media lỗi KHÔNG chặn bài học.
"""

import os
import re
import time
from ai.paths import lang_slug

BRIDGE_PORT = 5690
TOKEN_HEADER = "X-Vocab-Bridge"

# ─── Circuit breaker ─────────────────────────────────────────────────────────
# Tầng Web AI cần addon/Selenium/OpenClaw — nếu không có sẽ tốn ~25s/ngày chờ
# timeout. Sau N lần thất bại liên tiếp → tạm vô hiệu trong COOLDOWN giây.
_FAIL_STREAK = 0
_LAST_FAIL_TS = 0.0
_COOLDOWN_SECONDS = 1800      # 30 phút
_MAX_FAILS = 3


def _breaker_tripped() -> bool:
    global _FAIL_STREAK, _LAST_FAIL_TS
    if _FAIL_STREAK < _MAX_FAILS:
        return False
    if (time.time() - _LAST_FAIL_TS) > _COOLDOWN_SECONDS:
        # hết thời gian chờ → thử lại 1 lần
        _FAIL_STREAK = 0
        return False
    return True


def _breaker_fail():
    global _FAIL_STREAK, _LAST_FAIL_TS
    _FAIL_STREAK += 1
    _LAST_FAIL_TS = time.time()


def _breaker_ok():
    global _FAIL_STREAK
    _FAIL_STREAK = 0


def breaker_state() -> dict:
    return {"fail_streak": _FAIL_STREAK, "tripped": _breaker_tripped(),
            "cooldown_s": _COOLDOWN_SECONDS,
            "last_fail_ts": _LAST_FAIL_TS}


# ─── Bridge dùng chung ───────────────────────────────────────────────────────
_bridge = None


def get_bridge():
    """Lấy (hoặc tạo) bridge server. Trả None nếu không khởi động được."""
    global _bridge
    if _bridge is not None:
        return _bridge
    try:
        from ai.bridge_server import VocabBridge
        _bridge = VocabBridge()
        _bridge.start()
        return _bridge
    except Exception:
        return None


def stop_bridge():
    global _bridge
    if _bridge is not None:
        try:
            _bridge.stop()
        except Exception:
            pass
        _bridge = None


def web_ai_available() -> tuple:
    """(khả dụng, lý do)."""
    b = get_bridge()
    if b is None:
        return False, "không khởi động được bridge server (cần Flask)"
    return True, f"bridge cổng {b.port}"


# ─── Tạo prompt web ─────────────────────────────────────────────────────────
def build_web_prompt(language: str, day: int, lesson: dict) -> str:
    """Prompt gửi lên web AI để lấy nội dung + ảnh minh họa."""
    vocab = (lesson or {}).get("vocab") or []
    words = ", ".join(str(v.get("word", "")) for v in vocab[:12])
    topic = (lesson or {}).get("topic") or (lesson or {}).get("title") or ""
    lines = [
        f"Dạy tôi {len(vocab)} từ vựng tiếng {language} về chủ đề: {topic}.",
        f"Từ cần dạy: {words}.",
        "",
        "VỚI MỖI TỪ, trả về đúng 4 khối theo mẫu sau:",
        "### WORD: <từ>",
        "**Nghĩa**: <nghĩa tiếng Việt>",
        "**Phiên âm**: <IPA trong dấu />",
        "**Cách dùng**: <1 câu ví dụ tự nhiên + dịch>",
        "**Hình ảnh**: <mô tả ngắn bằng tiếng Anh để tôi vẽ minh họa>",
        "",
        "Sau danh sách từ, thêm một hội thoại ngắn 6-8 lượt về chủ đề trên.",
        "Chỉ trả về nội dung, không thêm chữ giải thích thừa.",
    ]
    return "\n".join(lines)


# ─── Tầng 2a: Chrome addon ─────────────────────────────────────────────────
ADDON_WAIT_SECONDS = 15      # BUG ĐÃ SỬA (L-M): trước là 180 s
# Khi addon CHƯA cài/load, mỗi lần gọi mất 180 s ⇒ treo cả pipeline
# (đo thật: tầng web luôn "chết âm thầm"). Giờ: timeout ngắn, poll trạng thái
# bridge (không dựa vào state["current"] vì push_job KHÔNG set current).


def fetch_via_addon(language: str, day: int, lesson: dict, platform: str = "gemini",
                    wait_seconds: int = ADDON_WAIT_SECONDS, log_fn=None) -> list:
    """Đẩy job cho addon và chờ kết quả. Trả list dict ảnh (bytes)."""
    def _log(m):
        if log_fn:
            try:
                log_fn(m)
            except Exception:
                pass

    b = get_bridge()
    if b is None:
        return []
    prompt = build_web_prompt(language, day, lesson)
    job_id = b.push_job({
        "platform": platform, "course": lang_slug(language), "day": day,
        "prompt": prompt, "words": [v.get("word") for v in (lesson.get("vocab") or [])][:12],
        "want_images": True, "max_images": 12, "timeout_sec": wait_seconds,
    })
    _log(f"   🌐 Đã đẩy job web AI: {job_id} (chờ addon tối đa {wait_seconds}s…)")

    out_dir = os.path.join(b.out_root, lang_slug(language), "_web")
    deadline = time.time() + wait_seconds
    while time.time() < deadline:
        time.sleep(1.5)
        # Đã có kết quả? → dừng sớm
        if _collect_images(out_dir, day, log_fn=None):
            return _collect_images(out_dir, day, log_fn)
        # Không có addon nào kết nối → dừng sớm thay vì chờ hết 180 s
        try:
            st = b.state.get("state") or ""
            if st == "idle" and not (b.jobs.qsize() > 0):
                break
        except Exception:
            break
    res = _collect_images(out_dir, day, log_fn)
    if not res:
        _log(f"   ⏭ Không có addon phản hồi trong {wait_seconds}s — chuyển tầng kế tiếp.")
    return res


def _collect_images(out_dir: str, day: int, log_fn=None) -> list:
    """Đọc ảnh addon đã lưu + đọc URL ảnh trong HTML (tải về nếu cần)."""
    import base64
    img_dir = os.path.join(out_dir, "images")
    res = []
    if not os.path.isdir(img_dir):
        return res
    for fn in sorted(os.listdir(img_dir)):
        if not fn.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            continue
        fp = os.path.join(img_dir, fn)
        try:
            with open(fp, "rb") as f:
                raw = f.read()
        except OSError:
            continue
        if len(raw) < 5 * 1024:
            continue
        res.append({
            "bytes": raw,
            "content_type": "image/png" if fn.lower().endswith(".png") else "image/jpeg",
            "prompt": "", "credit": "Web AI (Chrome addon)",
            "license": "", "source_url": "", "provider": "addon",
        })
    if log_fn and res:
        log_fn(f"   🌐 Nhận {len(res)} ảnh từ addon.")
    return res


# ─── Tầng 2b: Selenium ─────────────────────────────────────────────────────
def fetch_via_selenium(language: str, day: int, lesson: dict,
                       platform: str = "gemini", log_fn=None) -> list:
    try:
        from ai.selenium_web_ai import fetch_images_selenium
    except Exception as e:
        if log_fn:
            log_fn(f"   ⚠ Tầng Selenium không dùng được: {e}")
        return []
    try:
        return fetch_images_selenium(language, day, lesson, platform=platform,
                                     log_fn=log_fn)
    except Exception as e:
        if log_fn:
            log_fn(f"   ⚠ Selenium lỗi: {e}")
        return []


# ─── Tầng 2c: OpenClaw ─────────────────────────────────────────────────────
def fetch_via_openclaw(language: str, day: int, lesson: dict,
                       platform: str = "gemini", log_fn=None) -> list:
    try:
        from ai.openclaw_web_ai import fetch_images_openclaw
    except Exception as e:
        if log_fn:
            log_fn(f"   ⚠ Tầng OpenClaw không dùng được: {e}")
        return []
    try:
        return fetch_images_openclaw(language, day, lesson, platform=platform,
                                     log_fn=log_fn)
    except Exception as e:
        if log_fn:
            log_fn(f"   ⚠ OpenClaw lỗi: {e}")
        return []


# ─── Hàm tổng hợp ──────────────────────────────────────────────────────────
def fetch_images_via_web(language: str, day: int, lesson: dict,
                         platform: str = "gemini", log_fn=None) -> list:
    """Thử lần lượt addon → selenium → openclaw. Trả list dict ảnh (bytes).

    Dùng circuit breaker: sau N lần thất bại liên tiếp → tạm vô hiệu tầng này
    (tránh mất ~25s/ngày chờ timeout khi không cài addon / chromedriver).
    """
    if _breaker_tripped():
        if log_fn:
            log_fn(f"   ⏸ Tầng Web AI đang tạm vô hiệu "
                   f"(thất bại {_FAIL_STREAK} lần) — thử lại sau "
                   f"{int((_COOLDOWN_SECONDS - (time.time() - _LAST_FAIL_TS)) // 60)} phút.")
        return []
    for name, fn in (("addon", fetch_via_addon),
                     ("selenium", fetch_via_selenium),
                     ("openclaw", fetch_via_openclaw)):
        try:
            res = fn(language, day, lesson, platform=platform, log_fn=log_fn)
        except Exception as e:
            if log_fn:
                log_fn(f"   ⚠ Tầng {name} lỗi: {type(e).__name__}: {e}")
            continue
        if res:
            _breaker_ok()
            for r in res:
                r.setdefault("provider", name)
            return res
        if log_fn:
            log_fn(f"   ⏭ Tầng {name} không trả ảnh nào.")
    _breaker_fail()
    if log_fn and _FAIL_STREAK >= _MAX_FAILS:
        log_fn(f"   ⏸ Tầng Web AI tạm vô hiệu sau {_FAIL_STREAK} lần thất bại "
               f"(thử lại sau {_COOLDOWN_SECONDS // 60} phút).")
    return []


def fetch_content_via_web(language: str, day: int, prompt: str,
                          platform: str = "gemini", log_fn=None) -> dict:
    """Lấy NỘI DUNG (text) từ web AI. Trả {text, html, images[]} hoặc {}."""
    b = get_bridge()
    if b is None:
        return {}
    job_id = b.push_job({
        "platform": platform, "course": lang_slug(language), "day": day,
        "prompt": prompt, "want_images": False, "max_images": 0,
        "timeout_sec": 180,
    })
    if log_fn:
        log_fn(f"   🌐 Đã đẩy job lấy nội dung: {job_id}")
    out_dir = os.path.join(b.out_root, lang_slug(language), "_web")
    md_path = os.path.join(out_dir, f"day_{int(day):03d}.md")
    deadline = time.time() + 180
    while time.time() < deadline and not os.path.isfile(md_path):
        time.sleep(2)
    if os.path.isfile(md_path):
        try:
            with open(md_path, "r", encoding="utf-8") as f:
                return {"text": f.read(), "html": "", "images": []}
        except OSError:
            pass
    return {}


