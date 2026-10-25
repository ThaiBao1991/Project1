"""
providers.py — Chuỗi provider cho pipeline tự trị.

ProviderChain thử lần lượt các provider theo thứ tự ưu tiên, tự chuyển sang
provider kế tiếp khi provider hiện tại không khả dụng. Mỗi provider có:
    name         : tên định danh
    available()  : (bool, reason) — có dùng được không
    call(...)    : (ok, data, error_kind)

Provider hiện có:
    gemini_api  — Gemini (text + TTS), dùng chung key pool
    web_ai      — Web AI (addon Chrome / Selenium / OpenClaw) — Phase 4
    dict        — Ảnh từ từ điển / Wikimedia — 0 key, luôn khả dụng
    mock        — Dùng cho test (không gọi mạng)
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Provider:
    name = "base"

    def available(self):
        return True, ""

    def call(self, *a, **kw):
        return False, None, "not_implemented"


class GeminiApiProvider(Provider):
    """Gemini API — text (content/quiz/dialogue) + TTS."""

    name = "gemini_api"

    def __init__(self, coord=None, log_fn=None):
        self._coord = coord
        self._log = log_fn or (lambda m: None)

    def _ensure(self):
        if self._coord is not None:
            return self._coord
        try:
            from ai.course_generator import _load_gemini_keys
            from api.gemini_safe import GeminiCoordinator
            if not _load_gemini_keys():
                return None
            self._coord = GeminiCoordinator(key_loader=_load_gemini_keys,
                                          log_fn=self._log,
                                          temperature=0.35,
                                          max_output_tokens=16384,
                                          timeout=180,
                                          lock_after_success=False)
        except Exception as e:
            self._log(f"⚠ Không khởi tạo được GeminiCoordinator: {e}")
            self._coord = None
        return self._coord

    @property
    def coord(self):
        return self._ensure()

    def available(self):
        try:
            from ai.course_generator import _load_gemini_keys
            n = len(_load_gemini_keys())
            if n == 0:
                return False, "không có Gemini API key"
            return True, f"{n} key"
        except Exception as e:
            return False, str(e)

    def request(self, prompt, schema=None, **kw):
        c = self.coord
        if not c:
            return {"ok": False, "error": {"kind": "no_key", "message": "không có key"}}
        return c.request(prompt, response_schema=schema, **kw)

    def request_image(self, prompt, **kw):
        c = self.coord
        if not c:
            return {"ok": False, "error": {"kind": "no_key", "message": "không có key"}}
        return c.request_image(prompt, **kw)

    def tts(self, text, voice, model="gemini-3.8-flash-tts"):
        """Sinh WAV bằng Gemini TTS. Trả (bytes, mime)."""
        try:
            from ai.course_generator import _load_gemini_keys
            from ai.tts_generator import synth_gemini_tts
            api_key = ""
            for k in _load_gemini_keys():
                if k.get("key"):
                    api_key = k["key"]
                    break
            if not api_key:
                return b"", ""
            return synth_gemini_tts(text, voice=voice, model=model, api_key=api_key)
        except Exception:
            return b"", ""


class WebAiProvider(Provider):
    """Web AI — lấy nội dung + ảnh từ trang Gemini/ChatGPT/Copilot (Phase 4)."""

    name = "web_ai"

    def __init__(self, log_fn=None, bridge=None):
        self._log = log_fn or (lambda m: None)
        self._bridge = bridge

    def available(self):
        # KHÔNG start bridge ở đây — bridge là server riêng, chỉ cần khi thật sự
        # dùng tầng web. Việc start mỗi lần gọi available() làm tốn tài nguyên.
        try:
            from ai.web_ai_bridge import breaker_state
            st = breaker_state()
            if st.get("tripped"):
                return False, (f"tạm vô hiệu sau {st.get('fail_streak')} lần thất bại")
            try:
                from ai.bridge_server import VocabBridge  # noqa: F401
                return True, "bridge sẵn sàng (cần addon Chrome để hoạt động)"
            except Exception as e:
                return False, f"bridge không khởi động được ({e})"
        except Exception as e:
            return False, f"module chưa sẵn sàng ({e})"

    def fetch_images(self, language, day, vocab):
        try:
            from ai.web_ai_bridge import fetch_images_via_web
            return fetch_images_via_web(language, day, vocab, log_fn=self._log)
        except Exception as e:
            self._log(f"⚠ Web AI lỗi: {e}")
            return []

    def fetch_content(self, language, day, prompt):
        try:
            from ai.web_ai_bridge import fetch_content_via_web
            return fetch_content_via_web(language, day, prompt, log_fn=self._log)
        except Exception as e:
            self._log(f"⚠ Web AI lỗi: {e}")
            return {}


class DictProvider(Provider):
    """Ảnh từ từ điển / kho ảnh Wikimedia — 0 key, luôn khả dụng."""

    name = "dict"

    def available(self):
        return True, "0 key (Wikimedia)"

    def fetch_images(self, language, day, vocab, max_workers=4):
        try:
            from ai import dictionary_image
            words = [{"word": v.get("word", ""),
                      "pronunciation": v.get("pronunciation", ""),
                      "meaning_vi": v.get("meaning_vi", "")} for v in vocab]
            return dictionary_image.find_images_for_words(
                words, language, log_fn=None, max_workers=max_workers)
        except Exception as e:
            return []


class MockProvider(Provider):
    """Provider giả — dùng cho unit test (không gọi mạng)."""

    name = "mock"

    def __init__(self, payload=None, log_fn=None):
        self.payload = payload or {}
        self._log = log_fn or (lambda m: None)
        self.calls = []

    def available(self):
        return True, "mock"

    def request(self, prompt, schema=None, **kw):
        self.calls.append(prompt)
        p = self.payload.get("text")
        if p is None:
            return {"ok": False, "error": {"kind": "mock", "message": "no payload"}}
        return {"ok": True, "text": p, "model": "mock"}

    def request_image(self, prompt, **kw):
        self.calls.append(prompt)
        b64 = self.payload.get("image_b64")
        if not b64:
            return {"ok": False, "error": {"kind": "mock", "message": "no image"}}
        return {"ok": True, "b64": b64, "mime": "image/png", "model": "mock"}

    def fetch_images(self, language, day, vocab):
        return [{} for _ in vocab]


class ProviderChain:
    """Thử lần lượt nhiều provider, tự chuyển khi provider lỗi."""

    def __init__(self, providers=None, log_fn=None):
        self.providers = list(providers or [])
        self._log = log_fn or (lambda m: None)
        self.unavailable = {}

    @classmethod
    def default(cls, log_fn=None, coord=None, include_web=True):
        provs = [GeminiApiProvider(coord=coord, log_fn=log_fn)]
        if include_web:
            provs.append(WebAiProvider(log_fn=log_fn))
        provs.append(DictProvider())
        return cls(provs, log_fn=log_fn)

    def available_providers(self, only=None):
        out = []
        for p in self.providers:
            if only and p.name not in only:
                continue
            ok, reason = p.available()
            if ok:
                out.append(p)
            else:
                self.unavailable[p.name] = reason
                self._log(f"⏭  Provider '{p.name}' không dùng được: {reason}")
        return out

    def fetch_images(self, language, day, vocab, only=None):
        """Trả list dict ảnh (song song với vocab). Provider đầu tiên có kết quả thắng.

        only: danh sách tên provider được phép dùng (None = tất cả).
        """
        for p in self.available_providers(only=only):
            if not hasattr(p, "fetch_images"):
                continue
            res = p.fetch_images(language, day, vocab)
            if res and any(r for r in res):
                return res
        return [{} for _ in vocab]


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    chain = ProviderChain.default(log_fn=print)
    print("\nProvider khả dụng:", [p.name for p in chain.available_providers()])
    print("Không dùng được:", chain.unavailable)
