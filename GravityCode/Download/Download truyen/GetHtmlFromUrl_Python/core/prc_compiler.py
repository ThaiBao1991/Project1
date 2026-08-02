import os
import sys
import stat
import urllib.request
import subprocess
import zipfile
from pathlib import Path

# URL tải file kindlegen gốc từ internet archive
KINDLEGEN_ZIP_URL = "https://archive.org/download/kindlegen2.9/kindlegen_win32_v2_9.zip"

class PrcCompiler:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.tools_dir = os.path.join(base_dir, "tools")
        self.kindlegen_path = os.path.join(self.tools_dir, "kindlegen.exe")
        self._current_process = None

    def cancel(self):
        """Hủy tiến trình KindleGen đang chạy nếu có."""
        if self._current_process:
            try:
                self._current_process.kill()
            except Exception:
                pass
            self._current_process = None

    def check_and_download_kindlegen(self, progress_callback=None) -> bool:
        """Kiểm tra kindlegen.exe đã có chưa, nếu chưa thì tự động tải về."""
        if os.path.exists(self.kindlegen_path):
            return True
            
        os.makedirs(self.tools_dir, exist_ok=True)
        zip_path = os.path.join(self.tools_dir, "kindlegen.zip")
        
        try:
            if progress_callback:
                progress_callback("Đang tải thư viện biên dịch PRC (kindlegen_win32_v2_9.zip) ~ 20MB. Vui lòng đợi...")
            
            # Hàm hook để báo cáo tiến độ tải
            def report_hook(block_num, block_size, total_size):
                if progress_callback and total_size > 0:
                    downloaded = block_num * block_size
                    pct = min(100, int(downloaded * 100 / total_size))
                    progress_callback(f"Đang tải kindlegen.zip: {pct}% ({downloaded//1024} / {total_size//1024} KB)")

            urllib.request.urlretrieve(KINDLEGEN_ZIP_URL, zip_path, reporthook=report_hook)
            
            if progress_callback:
                progress_callback("✅ Đang giải nén kindlegen.exe...")
                
            # Giải nén kindlegen.exe từ file ZIP
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Trích xuất riêng kindlegen.exe
                source_file = zip_ref.open('kindlegen.exe')
                with open(self.kindlegen_path, 'wb') as target_file:
                    target_file.write(source_file.read())
            
            # Xóa file zip rác (Bỏ qua lỗi nếu bị Antivirus lock tạm thời)
            try:
                if os.path.exists(zip_path):
                    os.remove(zip_path)
            except Exception as e:
                pass
            
            # Cấp quyền thực thi nếu cần (Windows thường không cần nhưng an toàn)
            os.chmod(self.kindlegen_path, stat.S_IEXEC | stat.S_IREAD | stat.S_IWRITE)
            
            if progress_callback:
                progress_callback("✅ Cài đặt kindlegen.exe thành công!")
            return True
        except Exception as e:
            if progress_callback:
                progress_callback(f"❌ Lỗi tải kindlegen.exe: {e}")
            if os.path.exists(self.kindlegen_path):
                os.remove(self.kindlegen_path)
            if os.path.exists(zip_path):
                os.remove(zip_path)
            return False

    def _build_opf_package(self, html_path: str, temp_dir: str, title: str) -> str:
        import re, shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)

        content = open(html_path, 'r', encoding='utf-8-sig').read()
        parts = content.split("<a name='chap-")
        
        opf_path = os.path.join(temp_dir, 'book.opf')
        ncx_path = os.path.join(temp_dir, 'toc.ncx')

        items_opf = []
        refs_opf = []
        nav_points = []

        for i, part in enumerate(parts):
            if i == 0:
                head_path = os.path.join(temp_dir, 'header.html')
                # Sửa lại link mục lục từ '#chap-X' thành 'chap_{X+1}.html' vì các chương đã bị tách file
                import re
                part = re.sub(r"href=['\"]#chap-(\d+)['\"]", lambda m: f"href='chap_{int(m.group(1)) + 1}.html'", part)
                
                with open(head_path, 'w', encoding='utf-8-sig') as f:
                    f.write(f"<!DOCTYPE html><html><head><meta http-equiv='Content-Type' content='text/html; charset=utf-8' /></head><body>{part}</body></html>")
                items_opf.append('<item id="header" href="header.html" media-type="application/xhtml+xml"/>')
                refs_opf.append('<itemref idref="header"/>')
                continue
            
            idx_end = part.find("</a>")
            if idx_end == -1:
                idx_end = part.find("'></a>")
            chap_id = part[:idx_end].strip("'\"")
            
            body = part[part.find(">", idx_end)+1:]
            
            # Sanitize HTML to prevent KindleGen segfaults (3221225477)
            # Remove forms, inputs, scripts, and other problematic tags that often get scraped accidentally
            problem_tags = r"(script|style|form|input|button|select|textarea|iframe|object|embed|noscript)"
            # Remove full blocks <tag>...</tag>
            body = re.sub(rf"<{problem_tags}[^>]*>.*?</\1>", "", body, flags=re.IGNORECASE | re.DOTALL)
            # Remove self closing <tag/>
            body = re.sub(rf"<{problem_tags}[^>]*/>", "", body, flags=re.IGNORECASE)
            # Remove any left-over opening or closing tags
            body = re.sub(rf"</?{problem_tags}[^>]*>", "", body, flags=re.IGNORECASE)

            chap_title = f'Chương {i}'
            m = re.search(r'<h2[^>]*>(.*?)</h2>', body, re.IGNORECASE)
            if m:
                chap_title = m.group(1).strip()
                
            chap_file = f'chap_{i}.html'
            chap_path = os.path.join(temp_dir, chap_file)
            
            chap_content = f"<!DOCTYPE html><html><head><meta http-equiv='Content-Type' content='text/html; charset=utf-8' /></head><body>{body}</body></html>"
            with open(chap_path, 'w', encoding='utf-8') as f:
                f.write(chap_content)
            
            items_opf.append(f'<item id="chap_{i}" href="{chap_file}" media-type="application/xhtml+xml"/>')
            refs_opf.append(f'<itemref idref="chap_{i}"/>')
            nav_points.append(f'<navPoint id="navPoint-{i}" playOrder="{i}"><navLabel><text>{chap_title}</text></navLabel><content src="{chap_file}"/></navPoint>')

        ncx_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
    <head><meta name="dtb:uid" content="12345"/><meta name="dtb:depth" content="1"/><meta name="dtb:totalPageCount" content="0"/><meta name="dtb:maxPageNumber" content="0"/></head>
    <docTitle><text>{title}</text></docTitle>
    <navMap>
        {''.join(nav_points)}
    </navMap>
</ncx>'''
        with open(ncx_path, 'w', encoding='utf-8') as f:
            f.write(ncx_content)

        opf_content = f'''<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookId" version="2.0">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
        <dc:title>{title}</dc:title>
        <dc:language>vi</dc:language>
        <dc:identifier id="BookId">12345</dc:identifier>
    </metadata>
    <manifest>
        <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
        {chr(10).join(items_opf)}
    </manifest>
    <spine toc="ncx">
        {chr(10).join(refs_opf)}
    </spine>
</package>'''
        with open(opf_path, 'w', encoding='utf-8') as f:
            f.write(opf_content)

        return opf_path

    def compile_html_to_prc(self, html_path: str, log_callback=None, percent_callback=None, final_prc_path: str = None) -> bool:
        """Chạy lệnh kindlegen.exe để biên dịch html_path thành PRC.
        Nếu final_prc_path được cung cấp, file sẽ được move tới đó.
        """
        if not os.path.exists(self.kindlegen_path):
            if log_callback:
                log_callback("❌ Lỗi: Chưa có kindlegen.exe trong thư mục tools.")
            return False
            
        if not os.path.exists(html_path):
            if log_callback:
                log_callback(f"❌ Lỗi: File HTML không tồn tại - {html_path}")
            return False

        if log_callback:
            log_callback(f"🔄 Đang chuẩn bị gói OPF cho: {os.path.basename(html_path)}")

        try:
            output_name = os.path.basename(html_path)
            if output_name.lower().endswith(".html"):
                output_name = output_name[:-5] + ".prc"
            else:
                output_name = output_name + ".prc"

            # Phân tách HTML khổng lồ thành thư mục OPF để kindlegen chạy siêu tốc
            import tempfile, shutil
            temp_dir = os.path.join(tempfile.gettempdir(), "prc_build_temp")
            title = output_name[:-4]
            opf_path = self._build_opf_package(html_path, temp_dir, title)

            if log_callback:
                log_callback(f"🔄 Đang biên dịch PRC...")

            # Ẩn cửa sổ cmd trên windows
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            self._current_process = subprocess.Popen(
                [self.kindlegen_path, opf_path, "-c1", "-dont_append_source", "-o", output_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="ignore",
                startupinfo=startupinfo
            )
            
            # Đọc log đầu ra
            for line in self._current_process.stdout:
                line = line.strip()
                if not line:
                    continue
                # Ước tính phần trăm dựa trên dòng log của KindleGen
                if percent_callback:
                    if "Parsing files" in line:
                        percent_callback(60)
                    elif "Resolving hyperlinks" in line:
                        percent_callback(70)
                    elif "Computing UNICODE ranges" in line:
                        percent_callback(80)
                    elif "Building PRC file, record count" in line:
                        percent_callback(90)
                    elif "Final stats" in line:
                        percent_callback(95)

                # Chỉ lấy các dòng Info, Warning, Error chính và loại bỏ các cảnh báo phụ (W29004, W29005, W29008, W14217)
                if ("Info" in line or "Warning" in line or "Error" in line):
                    if not any(w in line for w in ["W29004", "W29005", "W29008", "W14217"]):
                        if log_callback:
                            log_callback(f"  [KindleGen]: {line}")
                        
            self._current_process.wait()
            
            # Kiểm tra xem file PRC có được tạo ra thực sự hay không (KindleGen luôn xuất ra file cùng thư mục với file đầu vào là temp_dir)
            expected_prc_path = os.path.join(temp_dir, output_name)
            
            if os.path.exists(expected_prc_path):
                # Move file PRC từ temp_dir ra ngoài
                out_path = final_prc_path if final_prc_path else os.path.join(os.path.dirname(html_path), output_name)
                import shutil
                if os.path.exists(out_path):
                    os.remove(out_path)
                shutil.move(expected_prc_path, out_path)
                
                # Xóa thư mục tạm
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass
                
                if log_callback:
                    log_callback(f"✅ Biên dịch PRC thành công! Đã lưu: {os.path.basename(out_path)}")
                return True
            else:
                if log_callback:
                    log_callback(f"❌ Biên dịch PRC thất bại với mã lỗi: {self._current_process.returncode}")
                return False
                
        except Exception as e:
            if log_callback:
                log_callback(f"❌ Lỗi ngoại lệ khi chạy kindlegen: {e}")
            return False
