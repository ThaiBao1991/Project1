"""
openclaw_browser.py — Wrapper quanh `openclaw browser` CLI.

Cơ chế:
  - Dùng subprocess gọi lệnh `openclaw browser <subcommand> --json`
  - Chrome được OpenClaw quản lý (không có --enable-automation flag → bypass anti-bot)
  - Không cần playwright / pyppeteer / websockets

Luồng điển hình:
  1. ensure_running()           → bật Chrome nếu chưa chạy
  2. open_tab(url)              → mở URL trong tab mới
  3. wait(selector=..., ms=...) → chờ JS render xong
  4. get_inner_html(selector)   → lấy nội dung HTML
  5. close_tab(tab_id)          → đóng tab vừa mở

Content mode trong ghfuConfig.json:
  "contentMode": "openclaw"     → engine tự dispatch sang _get_chapter_openclaw()
"""

import json
import logging
import subprocess
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)

DEFAULT_CLI_TIMEOUT_MS = 30000
DEFAULT_WAIT_AFTER_NAV = 3.0


class OpenClawBrowserError(Exception):
    pass


class OpenClawBrowser:
    """Wrapper quanh `openclaw browser` CLI."""

    def __init__(self, timeout_ms: int = DEFAULT_CLI_TIMEOUT_MS):
        self.timeout_ms = timeout_ms
        self._cli_base = ["openclaw", "browser"]

    def _run(self, *args: str, timeout_sec: int = 60) -> dict:
        """Chạy: openclaw browser <args...> --json. Trả về dict đã parse."""
        cmd = self._cli_base + list(args) + ["--json", f"--timeout={self.timeout_ms}"]
        logger.debug(f"[openclaw] {' '.join(cmd)}")
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=timeout_sec, encoding="utf-8", errors="replace",
            )
        except subprocess.TimeoutExpired as e:
            raise OpenClawBrowserError(f"openclaw CLI timeout ({timeout_sec}s): {e}")
        except FileNotFoundError:
            raise OpenClawBrowserError(
                "Không tìm thấy lệnh 'openclaw'. Cần cài đặt OpenClaw và thêm vào PATH."
            )

        raw = result.stdout.strip() or result.stderr.strip()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return {"ok": True, "raw": raw}

        if not data.get("ok", True):
            err = data.get("error", {})
            msg = err.get("message", str(data)) if isinstance(err, dict) else str(err)
            raise OpenClawBrowserError(f"openclaw error: {msg}")

        return data

    def start(self) -> bool:
        """Bật Chrome nếu chưa chạy."""
        try:
            self._run("start", timeout_sec=20)
            logger.info("[openclaw] Browser started.")
            return True
        except OpenClawBrowserError as e:
            logger.error(f"[openclaw] start failed: {e}")
            return False

    def is_running(self) -> bool:
        """Kiểm tra browser có đang chạy không."""
        try:
            data = self._run("status", timeout_sec=10)
            return bool(data.get("running", False))
        except Exception:
            return False

    def navigate(self, url: str, target_id: Optional[str] = None) -> None:
        """Điều hướng tab đến URL."""
        args = ["navigate", url]
        if target_id:
            args += ["--target-id", target_id]
        self._run(*args, timeout_sec=40)

    def open_tab(self, url: str) -> Optional[str]:
        """Mở URL trong tab mới. Trả về target_id."""
        try:
            data = self._run("open", url, timeout_sec=30)
            return data.get("targetId") or data.get("target_id") or data.get("id")
        except OpenClawBrowserError as e:
            logger.error(f"[openclaw] open_tab failed: {e}")
            return None

    def wait(self, selector: Optional[str] = None, text: Optional[str] = None, ms: int = 3000) -> bool:
        """Chờ selector / text xuất hiện trên trang."""
        args = ["wait"]
        if selector:
            args += ["--selector", selector]
        elif text:
            args += ["--text", text]
        else:
            args += ["--time-ms", str(ms)]
        try:
            self._run(*args, timeout_sec=int(ms / 1000) + 15)
            return True
        except OpenClawBrowserError as e:
            logger.warning(f"[openclaw] wait failed (non-fatal): {e}")
            return False

    def evaluate(self, js_fn: str) -> Any:
        """Chạy JS trong trang. js_fn là thân hàm (VD: 'return document.title;')"""
        data = self._run("evaluate", "--fn", js_fn, timeout_sec=30)
        return data.get("result")

    def get_inner_html(self, selector: str) -> Optional[str]:
        """Lấy innerHTML của element khớp selector."""
        js = f"var el = document.querySelector({json.dumps(selector)}); return el ? el.innerHTML : null;"
        result = self.evaluate(js)
        return result if isinstance(result, str) else None

    def get_text(self, selector: str) -> Optional[str]:
        """Lấy textContent của element."""
        js = f"var el = document.querySelector({json.dumps(selector)}); return el ? el.textContent.trim() : null;"
        result = self.evaluate(js)
        return result if isinstance(result, str) else None

    def get_title(self) -> str:
        """Lấy document.title."""
        result = self.evaluate("return document.title;")
        return str(result) if result else ""

    def close_tab(self, target_id: Optional[str] = None) -> None:
        """Đóng tab hiện tại hoặc tab theo target_id."""
        args = ["close"]
        if target_id:
            args += [target_id]
        try:
            self._run(*args, timeout_sec=10)
        except OpenClawBrowserError as e:
            logger.warning(f"[openclaw] close_tab failed (non-fatal): {e}")

    def ensure_running(self) -> bool:
        """Đảm bảo Chrome đang chạy, tự start nếu cần."""
        if self.is_running():
            return True
        logger.info("[openclaw] Browser not running, starting...")
        return self.start()

    def fetch_chapter(
        self,
        url: str,
        content_selector: str,
        title_selector: Optional[str] = None,
        wait_selector: Optional[str] = None,
        wait_ms: int = 6000,
        wait_after_nav: float = DEFAULT_WAIT_AFTER_NAV,
    ) -> dict:
        """
        High-level: mở URL trong Chrome, chờ render, extract nội dung.

        Trả về dict:
          {"ok": True,  "title": str, "content": str}
          {"ok": False, "error": str}
        """
        if not self.ensure_running():
            return {"ok": False, "error": "Không thể khởi động Chrome qua OpenClaw."}

        tab_id = None
        try:
            # 1. Mở tab mới
            tab_id = self.open_tab(url)
            if not tab_id:
                self.navigate(url)
            time.sleep(wait_after_nav)

            # 2. Chờ content render
            target_selector = wait_selector or content_selector
            if target_selector:
                self.wait(selector=target_selector, ms=wait_ms)

            # Extra delay cho JS tiếp tục sau khi selector xuất hiện
            time.sleep(1.5)

            # 3. Extract content
            content = self.get_inner_html(content_selector)
            if content is None:
                return {"ok": False, "error": f"Không tìm thấy '{content_selector}' sau khi tải trang."}

            # 4. Extract title
            title = ""
            if title_selector:
                title = self.get_text(title_selector) or ""
            if not title:
                title = self.get_title()

            return {"ok": True, "title": title.strip(), "content": content}

        except OpenClawBrowserError as e:
            return {"ok": False, "error": str(e)}
        finally:
            if tab_id:
                self.close_tab(tab_id)
