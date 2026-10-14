"""
open_file_helper.py - Micro Bridge cục bộ hỗ trợ:
1. Mở tệp và thư mục trên Windows bằng ứng dụng mặc định (os.startfile / explorer.exe).
2. Lưu & Đọc CSDL tập trung (database.json) cho tất cả các trình duyệt và Chrome Profile.
3. Phục vụ Web App trực tiếp tại http://127.0.0.1:38271/
- Không yêu cầu cài thêm thư viện bên ngoài (chỉ dùng Python Standard Library).
- Chạy trên 127.0.0.1:38271.
- Bảo toàn tuyệt đối đường dẫn mạng UNC (\\\\vdm-fsvr\\...).
- Tự động tìm kiếm thông minh (Smart Path Match) nếu đường dẫn dán bị cắt ngắn.
- Tự động sao lưu database.backup.json trước mỗi lần ghi dữ liệu.
"""

import sys
import os
import re
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import shutil
import datetime
import mimetypes

# Đảm bảo UTF-8 trên Windows console
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

PORT = 38271
HOST = "127.0.0.1"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "database.json")
BACKUP_FILE = os.path.join(BASE_DIR, "database.backup.json")

def normalize_windows_path(raw):
    """
    Chuẩn hóa đường dẫn Windows:
    - Bóc tách dấu ngoặc kép thừa (", ') do người dùng Copy as path từ Explorer.
    - Bảo toàn đường dẫn mạng UNC: \\\\vdm-fsvr\\Du lieu...
    - Xử lý link file://, file:///, file://///
    - Xử lý ký tự đặc biệt, URL decode (%20 -> khoảng trắng)
    """
    if not raw:
        return ""
    p = str(raw).strip()
    p = re.sub(r'^[\s"\'“”]+|[\s"\'“”]+$', '', p)
    p = urllib.parse.unquote(p)
    p = re.sub(r'^[\s"\'“”]+|[\s"\'“”]+$', '', p)
    p = p.replace("/", "\\")
    
    # Bóc tách tiền tố file:
    p = re.sub(r"^file:[\\/]*", "", p, flags=re.IGNORECASE)
    p = re.sub(r'^[\s"\'“”]+|[\s"\'“”]+$', '', p)
    
    # Kiểm tra nếu là ổ đĩa cục bộ (ví dụ: C:\..., \C:\...)
    m_drive = re.match(r"^[\\/]*([a-zA-Z]:[\\/].*)$", p)
    if m_drive:
        return m_drive.group(1).replace("/", "\\").rstrip("\\ ")
        
    # Kiểm tra nếu là đường dẫn mạng UNC ban đầu (bắt đầu bằng \\ hoặc // hoặc file://)
    raw_s = str(raw).strip().strip('"\'“”')
    if raw_s.startswith(r"\\") or raw_s.startswith("//") or raw_s.lower().startswith("file://"):
        p_clean = p.lstrip(r"\/")
        return (r"\\" + p_clean.replace("/", "\\")).rstrip("\\ ")
        
    return p.rstrip("\\ ")

def resolve_smart_path(p):
    """
    Tự động giải quyết đường dẫn:
    - Nếu đường dẫn tồn tại chính xác -> dùng ngay.
    - Nếu đường dẫn bị cắt ngắn đuôi (do copy thiếu hoặc gõ dở) -> tìm kiếm thông minh trong thư mục cha.
    """
    if not p:
        return p, False
    p = p.rstrip("\\ ")
    if os.path.exists(p):
        return p, os.path.isdir(p)

    parent = os.path.dirname(p)
    target_part = os.path.basename(p).lower().strip()
    if parent and os.path.isdir(parent) and target_part:
        try:
            candidates = os.listdir(parent)
            starts = [c for c in candidates if c.lower().startswith(target_part)]
            if starts:
                best = os.path.join(parent, starts[0])
                return best, os.path.isdir(best)
            contains = [c for c in candidates if target_part in c.lower()]
            if contains:
                best = os.path.join(parent, contains[0])
                return best, os.path.isdir(best)
        except Exception:
            pass

    return p, False

class LocalFileOpenHandler(BaseHTTPRequestHandler):
    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, HEAD")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.send_header("Access-Control-Max-Age", "86400")

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path_only = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # 1. Endpoint Ping kiểm tra server đang sống
        if path_only in ["/ping", "/status"]:
            self.send_response(200)
            self._send_cors_headers()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({
                "pong": True, 
                "version": "3.1", 
                "status": "running",
                "db_file": DB_FILE,
                "db_exists": os.path.exists(DB_FILE)
            }).encode("utf-8"))
            return

        # 2. Endpoint Đọc Database tập trung cho mọi trình duyệt / Profile
        if path_only == "/api/data":
            if not os.path.exists(DB_FILE):
                self.send_response(200)
                self._send_cors_headers()
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"exists": False, "message": "Chưa có database.json trên ổ đĩa"}).encode("utf-8"))
                return

            try:
                with open(DB_FILE, "r", encoding="utf-8") as f:
                    content = f.read()
                self.send_response(200)
                self._send_cors_headers()
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(content.encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self._send_cors_headers()
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": f"Lỗi đọc file: {str(e)}"}).encode("utf-8"))
            return

        # 3. Endpoint Mở tệp / thư mục
        if path_only == "/open":
            raw_target = query.get("path", [""])[0]
            if not raw_target:
                self.send_response(400)
                self._send_cors_headers()
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": "Thiếu tham số path"}).encode("utf-8"))
                return

            clean_path = normalize_windows_path(raw_target)
            resolved_path, is_dir = resolve_smart_path(clean_path)

            if not resolved_path:
                self.send_response(400)
                self._send_cors_headers()
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": "Đường dẫn không hợp lệ"}).encode("utf-8"))
                return

            # === PHÂN LOẠI: UNC mạng vs Local ===
            is_unc = resolved_path.startswith('\\\\')
            
            # Với UNC path mạng: KHÔNG kiểm tra exists (có thể timeout hoặc lỗi encoding)
            # Cứ thử mở explorer - Windows tự xử lý kết nối mạng
            if not is_unc and not os.path.exists(resolved_path):
                self.send_response(404)
                self._send_cors_headers()
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": False, 
                    "error": f"Không tìm thấy file hoặc thư mục:\n{resolved_path}",
                    "path": resolved_path
                }).encode("utf-8"))
                return

            try:
                import subprocess
                if is_unc or is_dir:
                    # Mở thư mục / UNC mạng bằng Windows File Explorer
                    subprocess.Popen(['explorer.exe', resolved_path])
                else:
                    # Mở tệp bằng ứng dụng Windows mặc định (Excel, Word, Acrobat...)
                    opened = False
                    if hasattr(os, "startfile"):
                        try:
                            os.startfile(resolved_path)
                            opened = True
                        except Exception:
                            pass
                    if not opened:
                        subprocess.Popen(f'start "" "{resolved_path}"', shell=True)

                self.send_response(200)
                self._send_cors_headers()
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": True, 
                    "path": resolved_path, 
                    "is_dir": is_dir or is_unc,
                    "matched": resolved_path != clean_path
                }).encode("utf-8"))
                print(f"[MBC File Helper] Đã mở {'UNC mạng' if is_unc else ('Thư mục' if is_dir else 'Tệp')}: {resolved_path}")
            except Exception as e:
                self.send_response(500)
                self._send_cors_headers()
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": False, 
                    "error": str(e), 
                    "path": resolved_path
                }).encode("utf-8"))
                print(f"[MBC File Helper] Lỗi khi mở {resolved_path}: {e}")
            return

        # 4. Phục vụ tĩnh các file của Web App khi truy cập http://127.0.0.1:38271/
        req_file = path_only.lstrip("/")
        if not req_file or req_file == "":
            req_file = "index.html"
        static_path = os.path.join(BASE_DIR, req_file)

        if os.path.exists(static_path) and os.path.isfile(static_path):
            ctype, _ = mimetypes.guess_type(static_path)
            if not ctype:
                ctype = "text/html; charset=utf-8" if req_file.endswith(".html") else "application/octet-stream"
            elif ctype.startswith("text/") or ctype in ["application/javascript", "application/json"]:
                ctype += "; charset=utf-8"

            try:
                with open(static_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self._send_cors_headers()
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode())
                return

        self.send_response(404)
        self._send_cors_headers()
        self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path_only = parsed.path

        # Endpoint Lưu Database từ Web App vào file database.json trên máy
        if path_only == "/api/data":
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length).decode("utf-8")
                new_data = json.loads(body)

                # Kiểm tra tính toàn vẹn cơ bản
                if not isinstance(new_data, dict):
                    raise ValueError("Dữ liệu gửi lên phải là đối tượng JSON")

                tasks = new_data.get("tasks", [])
                employees = new_data.get("employees", [])

                # Tạo bản sao lưu (backup) an toàn trước khi ghi đè nếu file cũ tồn tại
                if os.path.exists(DB_FILE):
                    try:
                        shutil.copy2(DB_FILE, BACKUP_FILE)
                    except Exception as b_err:
                        print(f"[MBC File Helper] Cảnh báo tạo backup: {b_err}")

                # Ghi dữ liệu mới với UTF-8 và indent đẹp
                with open(DB_FILE, "w", encoding="utf-8") as f:
                    json.dump(new_data, f, ensure_ascii=False, indent=2)

                self.send_response(200)
                self._send_cors_headers()
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": True,
                    "taskCount": len(tasks),
                    "empCount": len(employees),
                    "savedAt": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }).encode("utf-8"))
                print(f"[MBC File Helper] Đã lưu thành công CSDL: {len(tasks)} công việc, {len(employees)} nhân sự vào {DB_FILE}")
            except Exception as e:
                self.send_response(500)
                self._send_cors_headers()
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": f"Lỗi ghi file: {str(e)}"}).encode("utf-8"))
            return

        self.send_response(404)
        self._send_cors_headers()
        self.end_headers()

    def log_message(self, format, *args):
        # Giảm bớt log rác terminal
        return

def run_server():
    try:
        server = HTTPServer((HOST, PORT), LocalFileOpenHandler)
        print(f"[MBC File Helper v3.1] Server đang chạy tại http://{HOST}:{PORT}")
        print(f"[MBC File Helper v3.1] File CSDL: {DB_FILE}")
        server.serve_forever()
    except OSError as e:
        if "address already in use" in str(e).lower() or getattr(e, "winerror", 0) == 10048:
            print(f"[MBC File Helper] Cổng {PORT} đang được sử dụng. Server cũ vẫn đang chạy tốt.")
        else:
            print(f"[MBC File Helper] Lỗi khởi động: {e}")

if __name__ == "__main__":
    run_server()
