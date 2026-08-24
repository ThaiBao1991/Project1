"""
Core Engine for AlowGPT - DPI/SNI Fragmentation Proxy Server & Windows System Proxy Manager
Pure Python 100% (No external dependencies required)
"""

import socket
import select
import threading
import time
import winreg
import ctypes
import os
import json
import logging
from typing import Callable, Optional, Set

# Windows Internet Option Constants to notify system of proxy changes immediately
INTERNET_OPTION_SETTINGS_CHANGED = 39
INTERNET_OPTION_REFRESH = 37

class SystemProxyManager:
    """Manages Windows Internet Settings (System Proxy) via Registry and WinINet."""
    REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"

    @classmethod
    def set_system_proxy(cls, host: str = "127.0.0.1", port: int = 7070) -> bool:
        """Enable Windows System Proxy for 127.0.0.1:port."""
        try:
            proxy_server = f"{host}:{port}"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, cls.REG_PATH, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, proxy_server)
            winreg.SetValueEx(key, "ProxyOverride", 0, winreg.REG_SZ, "<local>;localhost;127.0.0.1")
            winreg.CloseKey(key)
            cls._refresh_system()
            return True
        except Exception as e:
            logging.error(f"Error setting system proxy: {e}")
            return False

    @classmethod
    def unset_system_proxy(cls) -> bool:
        """Disable Windows System Proxy and restore normal direct connection."""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, cls.REG_PATH, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
            winreg.CloseKey(key)
            cls._refresh_system()
            return True
        except Exception as e:
            logging.error(f"Error unsetting system proxy: {e}")
            return False

    @classmethod
    def is_proxy_enabled(cls) -> bool:
        """Check if Windows System Proxy is currently active."""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, cls.REG_PATH, 0, winreg.KEY_READ)
            val, _ = winreg.QueryValueEx(key, "ProxyEnable")
            winreg.CloseKey(key)
            return val == 1
        except Exception:
            return False

    @classmethod
    def _refresh_system(cls):
        """Notify WinINet that proxy settings have changed so Chrome/Edge update immediately."""
        try:
            wininet = ctypes.windll.Wininet
            wininet.InternetSetOptionW(0, INTERNET_OPTION_SETTINGS_CHANGED, 0, 0)
            wininet.InternetSetOptionW(0, INTERNET_OPTION_REFRESH, 0, 0)
        except Exception as e:
            logging.debug(f"Failed to refresh WinINet options: {e}")


class VSCodeConfigHelper:
    """Helper to detect and update VSCode settings.json for OpenCode and Proxy."""
    @staticmethod
    def get_vscode_settings_path() -> Optional[str]:
        appdata = os.environ.get("APPDATA")
        if appdata:
            path = os.path.join(appdata, "Code", "User", "settings.json")
            return path
        return None

    @classmethod
    def apply_proxy_to_vscode(cls, host: str = "127.0.0.1", port: int = 7070) -> tuple[bool, str]:
        path = cls.get_vscode_settings_path()
        if not path:
            return False, "Không tìm thấy thư mục APPDATA."

        try:
            data = {}
            os.makedirs(os.path.dirname(path), exist_ok=True)
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except Exception:
                    # In case settings.json has trailing commas or comments
                    with open(path, "r", encoding="utf-8") as f:
                        raw = f.read()
                    # Strip simple comments if any
                    data = {}

            data["http.proxy"] = f"http://{host}:{port}"
            data["http.proxyStrictSSL"] = False

            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            return True, f"Đã cập nhật cấu hình Proxy thành công vào:\n{path}"
        except Exception as e:
            return False, f"Lỗi khi ghi file settings.json: {e}"

    @classmethod
    def remove_proxy_from_vscode(cls) -> tuple[bool, str]:
        path = cls.get_vscode_settings_path()
        if not path or not os.path.exists(path):
            return True, "File settings.json không tồn tại."

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data.pop("http.proxy", None)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True, "Đã gỡ bỏ Proxy khỏi VSCode."
        except Exception as e:
            return False, f"Lỗi: {e}"


class AlowGPTProxyServer:
    """Multi-threaded Local HTTPS/HTTP CONNECT Proxy Server with DPI/SNI Fragmentation."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 7070,
        mode: str = "sni_fragment",
        chunk_size: int = 40,
        delay_ms: int = 30,
        bypass_domains: Optional[list] = None,
        cf_worker_url: str = "",
        log_callback: Optional[Callable[[str, str], None]] = None
    ):
        self.host = host
        self.port = port
        self.mode = mode
        self.chunk_size = chunk_size
        self.delay_sec = max(0.005, delay_ms / 1000.0)
        self.bypass_domains = set(d.strip().lower() for d in (bypass_domains or []))
        self.cf_worker_url = cf_worker_url.strip()
        self.log_callback = log_callback

        self.server_socket: Optional[socket.socket] = None
        self.is_running = False
        self._thread: Optional[threading.Thread] = None
        self._active_connections = 0
        self._lock = threading.Lock()

    def log(self, message: str, level: str = "INFO"):
        if self.log_callback:
            try:
                self.log_callback(message, level)
            except Exception:
                pass

    def is_target_domain(self, host: str) -> bool:
        """Check if destination matches configured bypass list."""
        host_lower = host.lower()
        for domain in self.bypass_domains:
            if host_lower == domain or host_lower.endswith("." + domain):
                return True
        return False

    def start(self) -> bool:
        """Start listening on the configured port."""
        if self.is_running:
            return True

        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(128)
            self.is_running = True
            
            self._thread = threading.Thread(target=self._listen_loop, daemon=True)
            self._thread.start()
            self.log(f"Proxy Server đã khởi động tại {self.host}:{self.port} (Chế độ: {self.mode})", "SUCCESS")
            return True
        except OSError as e:
            self.log(f"Không thể mở cổng {self.port} (Cổng có thể đang bị chiếm dụng): {e}", "ERROR")
            self.is_running = False
            if self.server_socket:
                try:
                    self.server_socket.close()
                except Exception:
                    pass
                self.server_socket = None
            return False

    def stop(self):
        """Stop proxy server and close listening socket."""
        self.is_running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
            self.server_socket = None
        self.log("Proxy Server đã dừng.", "WARNING")

    def _listen_loop(self):
        while self.is_running and self.server_socket:
            try:
                client_sock, client_addr = self.server_socket.accept()
                t = threading.Thread(target=self._handle_client, args=(client_sock,), daemon=True)
                t.start()
            except OSError:
                break
            except Exception as e:
                if self.is_running:
                    self.log(f"Lỗi tiếp nhận kết nối: {e}", "ERROR")

    def _handle_client(self, client_sock: socket.socket):
        with self._lock:
            self._active_connections += 1

        target_sock: Optional[socket.socket] = None
        try:
            client_sock.settimeout(15.0)
            initial_data = client_sock.recv(4096)
            if not initial_data:
                return

            first_line = initial_data.split(b"\r\n")[0].decode(errors="ignore")
            parts = first_line.split(" ")
            if len(parts) < 2:
                return

            method = parts[0].upper()
            target_url = parts[1]

            if method == "CONNECT":
                # HTTPS Tunneling
                if ":" in target_url:
                    dest_host, dest_port_str = target_url.split(":")[:2]
                    dest_port = int(dest_port_str)
                else:
                    dest_host = target_url
                    dest_port = 443

                is_bypass = self.is_target_domain(dest_host)

                # Connect to destination
                target_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                target_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                target_sock.settimeout(15.0)
                target_sock.connect((dest_host, dest_port))

                # Respond 200 Connection Established to client
                client_sock.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")

                if is_bypass:
                    self.log(f"[BYPASS] Đang xử lý kết nối bảo vệ tới: {dest_host}:{dest_port}", "INFO")
                    # First packet from client is TLS Client Hello containing SNI
                    client_sock.settimeout(10.0)
                    tls_hello = client_sock.recv(8192)
                    if tls_hello:
                        split = min(self.chunk_size, len(tls_hello) - 1)
                        if split > 0:
                            part1 = tls_hello[:split]
                            part2 = tls_hello[split:]
                            target_sock.sendall(part1)
                            time.sleep(self.delay_sec)
                            target_sock.sendall(part2)
                        else:
                            target_sock.sendall(tls_hello)
                
                # Relay bidirectional data
                self._pipe_sockets(client_sock, target_sock)

            else:
                # Normal HTTP Proxy / OpenCode local API routing
                dest_host = ""
                dest_port = 80
                for line in initial_data.split(b"\r\n"):
                    if line.lower().startswith(b"host:"):
                        h = line.split(b":", 1)[1].strip().decode(errors="ignore")
                        if ":" in h:
                            dest_host, p_str = h.split(":")[:2]
                            dest_port = int(p_str)
                        else:
                            dest_host = h
                        break

                if dest_host:
                    target_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    target_sock.settimeout(15.0)
                    target_sock.connect((dest_host, dest_port))
                    target_sock.sendall(initial_data)
                    self._pipe_sockets(client_sock, target_sock)

        except Exception:
            pass
        finally:
            if client_sock:
                try:
                    client_sock.close()
                except Exception:
                    pass
            if target_sock:
                try:
                    target_sock.close()
                except Exception:
                    pass
            with self._lock:
                self._active_connections -= 1

    def _pipe_sockets(self, sock1: socket.socket, sock2: socket.socket):
        """High performance bi-directional pipe between two sockets."""
        sockets = [sock1, sock2]
        sock1.setblocking(False)
        sock2.setblocking(False)

        while self.is_running:
            try:
                rlist, _, xlist = select.select(sockets, [], sockets, 30.0)
                if xlist or not rlist:
                    break

                for r in rlist:
                    other = sock2 if r is sock1 else sock1
                    try:
                        data = r.recv(16384)
                        if not data:
                            return
                        other.sendall(data)
                    except BlockingIOError:
                        continue
                    except Exception:
                        return
            except Exception:
                break


# Template for Cloudflare Worker Relay
CF_WORKER_TEMPLATE = """export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // Mặc định chuyển tiếp đến OpenAI API (hỗ trợ OpenCode / Chat / Models)
    // Nếu dùng Claude đổi thành: api.anthropic.com
    // Nếu dùng DeepSeek đổi thành: api.deepseek.com
    url.hostname = "api.openai.com";
    url.port = "443";
    url.protocol = "https:";

    const newHeaders = new Headers(request.headers);
    newHeaders.set("Host", url.hostname);

    const newRequest = new Request(url, {
      method: request.method,
      headers: newHeaders,
      body: request.body,
      redirect: "follow"
    });

    return fetch(newRequest);
  }
};
"""
