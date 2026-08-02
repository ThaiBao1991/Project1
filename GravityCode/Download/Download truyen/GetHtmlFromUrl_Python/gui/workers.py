"""
workers.py — QThread worker cho việc tải truyện
Tương đương TAuto.java của phiên bản Java gốc.
Đã nâng cấp: Hỗ trợ Multi-threading (tải nhiều chương cùng lúc) & Resume chuẩn vị trí.
"""

import os
import re
import time
import json
import logging
import concurrent.futures
from datetime import datetime
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal, QSettings
from core.page_config_mgr import PageConfigManager
from core.engine import GetHtmlEngine
from models.chapter import Chapter

logger = logging.getLogger(__name__)


def html_to_text(html: str) -> str:
    """Chuyển HTML sang text thuần (tương đương removeHtmlString trong Java)"""
    # Thay <br>, <p>, <h*> bằng dòng mới
    text = re.sub(r'</?(?:h\d|br|p)[^>]*>', '\n', html, flags=re.IGNORECASE)
    # Xóa tất cả thẻ HTML còn lại
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    return text.strip()


class DownloadWorker(QThread):
    """
    Worker chạy trong luồng nền để tải danh sách chương và nội dung.
    Phát các signal về UI chính để cập nhật.
    """
    progress_signal = pyqtSignal(int, str, str)   # (index, status, error_msg)
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(str)
    chapter_list_ready = pyqtSignal(int)          # total_count

    def __init__(self, url: str, config_mgr: PageConfigManager, save_path: str,
                 is_divide_file: bool = False, ebook_info: str = "",
                 start_idx: int = 0, end_idx: int = -1, file_format: str = "html",
                 manual_links: list[str] = None, page_config=None, resume_data: dict = None,
                 delete_folder: bool = False):
        super().__init__()
        self.url = url
        self.config_mgr = config_mgr
        self.save_path = save_path
        self.is_divide_file = is_divide_file
        self.ebook_info = ebook_info
        self.start_idx = start_idx
        self.end_idx = end_idx
        self.file_format = file_format
        self.manual_links = manual_links
        self.forced_page_config = page_config
        self.resume_data = resume_data
        self.delete_folder = delete_folder

        self.engine = GetHtmlEngine()
        self.is_running = True
        self.download_failed_count = 0
        self.chapters: list[Chapter] = []
        self.failed_links: list[str] = []

    # ------------------------------------------------------------------
    # Public Methods
    # ------------------------------------------------------------------
    def stop(self):
        self.is_running = False

    def _get_max_workers(self):
        settings = QSettings("Mkbyme", "GetHtmlFromUrl")
        return settings.value("download/max_connection", 1, type=int)

    def _get_delay_ms(self):
        settings = QSettings("Mkbyme", "GetHtmlFromUrl")
        return settings.value("download/delay_ms", 300, type=int)

    # ------------------------------------------------------------------
    # Main Thread Entry
    # ------------------------------------------------------------------
    def run(self):
        try:
            # 1. KHỞI TẠO HOẶC KHÔI PHỤC TIẾN TRÌNH (RESUME)
            if self.resume_data:
                self.log_signal.emit("🔄 Đang khôi phục tiến trình tải (Resume)...")
                
                # Backward compatibility cho file _Resume.json cũ (không có all_links)
                if "all_links" not in self.resume_data:
                    old_selected = self.resume_data.get("selected_links", [])
                    self.start_idx = self.resume_data.get("start_idx", 0)
                    all_links = [""] * self.start_idx + old_selected
                    self.end_idx = self.start_idx + len(old_selected) - 1
                else:
                    all_links = self.resume_data.get("all_links", [])
                    self.start_idx = self.resume_data.get("start_idx", 0)
                    self.end_idx = self.resume_data.get("end_idx", -1)
                    
                if self.end_idx == -1:
                    self.end_idx = len(all_links) - 1
                    
                selected_links = all_links[self.start_idx : self.end_idx + 1]
                
                chapters_status = self.resume_data.get("chapters_status", [])
                self.chapters = [None] * len(selected_links)
                save_dir = self.resume_data.get("save_dir", "")
                final_path = self.resume_data.get("final_path", "")
                story_title = self.resume_data.get("story_title", self._extract_story_title())
                
                # Khôi phục các chapter đã tải thành công vào bộ nhớ
                extracted_chapters = {}
                # Cố gắng trích xuất từ file HTML tổng hợp trước (nếu có)
                if final_path and os.path.exists(final_path) and self.file_format == "html":
                    self.log_signal.emit("🔄 Đang trích xuất các chương đã có từ file HTML gốc...")
                    try:
                        with open(final_path, "r", encoding="utf-8-sig", errors="ignore") as f:
                            html_content = f.read()
                            
                        # File HTML gộp có định dạng: <h2 id="chap_{idx}">{title}</h2>\n<div>{content}</div>
                        parts = html_content.split('<h2 id="chap_')
                        for part in parts[1:]:
                            try:
                                idx_str, rest = part.split('">', 1)
                                idx = int(idx_str)
                                title, rest2 = rest.split('</h2>\n', 1)
                                
                                div_start = rest2.find('<div>')
                                if div_start != -1:
                                    div_start += 5
                                div_end = rest2.rfind('</div>\n<hr/>')
                                if div_end == -1:
                                    div_end = rest2.rfind('</div>')
                                
                                content = rest2[div_start:div_end] if div_start != -1 and div_end != -1 else rest2.strip()
                                extracted_chapters[idx] = Chapter(title=title, url="", content=content)
                            except Exception:
                                pass
                        if extracted_chapters:
                            self.log_signal.emit(f"✅ Đã tìm thấy {len(extracted_chapters)} chương trong file HTML gốc.")
                    except Exception as e:
                        self.log_signal.emit(f"⚠️ Lỗi đọc file HTML gốc: {e}")
                
                # Áp dụng dữ liệu trích xuất hoặc tải từ file tạm
                for idx, status_obj in enumerate(chapters_status):
                    if status_obj.get("status") == "done":
                        if idx in extracted_chapters:
                            self.chapters[idx] = extracted_chapters[idx]
                        elif save_dir and os.path.exists(save_dir):
                            ch_title = status_obj.get("title", "")
                            safe_title = re.sub(r'[\\/:*?"<>|]', '_', ch_title or f"Chuong_{idx + 1}")
                            ext = f".{self.file_format}"
                            file_path = os.path.join(save_dir, f"{idx + 1:04d}_{safe_title}{ext}")
                            
                            if os.path.exists(file_path):
                                with open(file_path, "r", encoding="utf-8") as f:
                                    content = f.read()
                                    
                                if self.file_format == "txt":
                                    lines = content.splitlines()
                                    if len(lines) >= 2:
                                        content = "\n".join(lines[2:])
                                        
                                ch = Chapter(title=ch_title, url=selected_links[idx], content=content)
                                self.chapters[idx] = ch
                            else:
                                status_obj["status"] = "error"
                                self.log_signal.emit(f"  ⚠️ Mất file chương {self.start_idx + idx + 1}, sẽ tải lại.")
                        else:
                            status_obj["status"] = "error"
                            self.log_signal.emit(f"  ⚠️ Không tìm thấy dữ liệu chương {self.start_idx + idx + 1}, sẽ tải lại.")
                
                page_config = self.forced_page_config or self.config_mgr.get_config_by_url(self.url)
            else:
                # 2. KHỞI TẠO TẢI MỚI
                page_config = self.forced_page_config or self.config_mgr.get_config_by_url(self.url)
                if not page_config:
                    self.log_signal.emit(f"❌ Không tìm thấy cấu hình hỗ trợ cho URL: {self.url}")
                    self.finished_signal.emit("Lỗi: Không hỗ trợ site này.")
                    return

                self.log_signal.emit(f"🔄 Sử dụng cấu hình host: {page_config.page_code}")

                if self.manual_links is not None:
                    all_links = self.manual_links
                    self.log_signal.emit(f"🔎 Đang tải thủ công {len(all_links)} link...")
                else:
                    self.log_signal.emit("🔎 Đang phân tích mục lục...")
                    all_links = self.engine.get_list_chapter_links(self.url, page_config, log_fn=self.log_signal.emit)

                if not all_links:
                    self.log_signal.emit("❌ Không tìm thấy danh sách chương nào.")
                    self.finished_signal.emit("Lỗi: Không tìm thấy link chương.")
                    return
                
                total = len(all_links)
                self.log_signal.emit(f"✅ Đã tìm thấy {total} chương.")
                self.chapter_list_ready.emit(total)

                start = self.start_idx
                end = self.end_idx if self.end_idx != -1 else total - 1
                end = min(end, total - 1)
                selected_links = all_links[start:end + 1]

                story_title = self._extract_story_title()
                save_dir, final_path = self._prepare_save_paths(story_title)
                
                self.chapters = [None] * len(selected_links)
                chapters_status = [{"status": "pending", "title": ""} for _ in selected_links]

            self.log_signal.emit(f"📥 Bắt đầu tải với {self._get_max_workers()} luồng...")
            delay_ms = self._get_delay_ms() / 1000.0

            # 3. HÀM WORKER CHO TỪNG CHƯƠNG (CHẠY TRONG THREADPOOL)
            def download_single(local_idx: int, link: str):
                if not self.is_running:
                    return
                    
                # Bỏ qua nếu đã tải xong trong quá trình resume
                if self.resume_data and chapters_status[local_idx].get("status") == "done":
                    return
                    
                global_idx = self.start_idx + local_idx
                self.progress_signal.emit(global_idx, "Đang tải...", "")
                
                full_link = link if link.startswith("http") else f"https://{page_config.page_code}{link}"
                
                max_retries = 5
                chapter = None
                for attempt in range(max_retries):
                    if not self.is_running:
                        return
                    chapter = self.engine.get_chapter_title_and_content(full_link, page_config)
                    chapter.url = full_link
                    
                    if not chapter.is_get_failed:
                        break  # Thành công thì thoát vòng lặp retry
                        
                    if attempt < max_retries - 1:
                        self.log_signal.emit(f"  ⚠️ Lỗi chương {global_idx + 1}, thử lại lần {attempt + 2}/{max_retries}...")
                        time.sleep(1)  # Nghỉ 1 giây trước khi thử lại

                if chapter.is_get_failed:
                    self.download_failed_count += 1
                    self.failed_links.append(full_link)
                    chapters_status[local_idx] = {"status": "error", "title": chapter.title}
                    self.progress_signal.emit(global_idx, "❌ Lỗi", f"Thất bại sau {max_retries} lần")
                    self.log_signal.emit(f"  ❌ Thất bại hoàn toàn: {full_link}")
                else:
                    self.chapters[local_idx] = chapter
                    chapters_status[local_idx] = {"status": "done", "title": chapter.title}
                    self.progress_signal.emit(global_idx, "✅ Xong", "")
                    self.log_signal.emit(f"  ✅ Chương {global_idx + 1}: {chapter.title[:50] if chapter.title else '(no title)'}")

                    if save_dir:
                        self._save_single_chapter(chapter, local_idx, save_dir)
                
                # Cập nhật _Resume.json liên tục sau mỗi chương
                self._save_resume_state(story_title, final_path, all_links, save_dir, chapters_status)

            # 4. CHẠY THREADPOOL EXECUTOR CÓ AUTO-RESUME TỐI ĐA 5 LẦN
            for auto_resume_attempt in range(5):
                if not self.is_running:
                    break
                    
                max_workers = self._get_max_workers()
                with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                    futures = []
                    for idx, link in enumerate(selected_links):
                        if not self.is_running:
                            break
                        # Bỏ qua nếu đã tải xong (từ lần trước hoặc lần thử nghiệm trong cùng session)
                        if chapters_status[idx].get("status") == "done":
                            continue
                            
                        futures.append(executor.submit(download_single, idx, link))
                        time.sleep(delay_ms) # Khoảng nghỉ tránh spam request quá nhanh
                    
                    # Chờ tất cả xong
                    for future in concurrent.futures.as_completed(futures):
                        pass

                if not self.is_running:
                    break

                # Kiểm tra xem đã hoàn thành 100% chưa
                if all(ch is not None for ch in self.chapters):
                    break # Success 100%
                    
                # Nếu chưa, đếm số chương lỗi và thử lại
                failed_count = sum(1 for ch in self.chapters if ch is None)
                if auto_resume_attempt < 4:
                    self.log_signal.emit(f"🔄 Auto-resume lần {auto_resume_attempt + 1}/5: còn {failed_count} chương lỗi. Đang thử lại...")
                    time.sleep(2)
                else:
                    self.log_signal.emit(f"❌ Đã thử tải tự động 5 lần nhưng vẫn còn {failed_count} chương lỗi.")

        except Exception as e:
            import traceback
            err_msg = traceback.format_exc()
            logger.error(f"Error in run: {e}\n{err_msg}")
            self.finished_signal.emit(f"Lỗi: {e}")
            self.log_signal.emit(f"❌ CHI TIẾT LỖI:\n{err_msg}")
            return

        # 5. XỬ LÝ SAU KHI TẢI XONG
        # Ghi log lỗi TXT để tương thích với chức năng tải tay
        if self.failed_links and final_path:
            error_log_path = os.path.join(str(Path(final_path).parent), f"{story_title}_ErrorLog.txt")
            try:
                with open(error_log_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(self.failed_links))
                self.log_signal.emit(f"📝 Đã ghi danh sách {len(self.failed_links)} link lỗi vào: {error_log_path}")
            except Exception as e:
                logger.error(f"Lỗi ghi error log: {e}")

        # Kiểm tra xem có thành công 100% không
        all_done = all(ch is not None for ch in self.chapters)

        # Xóa _Resume.json sau khi RESUME hoàn tất thành công (0 lỗi)
        # Không xóa khi tải mới (self.resume_data is None)
        if self.resume_data and all_done and final_path:
            resume_path = os.path.join(str(Path(final_path).parent), f"{story_title}_Resume.json")
            if os.path.exists(resume_path):
                try:
                    os.remove(resume_path)
                    self.log_signal.emit("🧹 Đã xóa file Resume (resume hoàn tất 100%).")
                except Exception:
                    pass

        if all_done:
            self.log_signal.emit(f"✅ Tải xong {len(self.chapters)} chương. Đang tự động gộp file...")
            
            # Tự động gộp
            if final_path:
                self._save_concatenate_file(story_title, final_path)
                self.log_signal.emit(f"✅ Đã gộp thành công vào: {final_path}")
                
                # Tự động xóa thư mục nếu user đã check
                if self.delete_folder and save_dir and os.path.exists(save_dir):
                    import shutil
                    try:
                        shutil.rmtree(save_dir, ignore_errors=True)
                        self.log_signal.emit(f"🧹 Đã xóa thư mục tạm: {save_dir}")
                    except Exception as e:
                        self.log_signal.emit(f"⚠️ Lỗi xóa thư mục tạm: {e}")
                        
            self.finished_signal.emit("Hoàn tất và đã gộp file tự động!")
        else:
            self.finished_signal.emit(f"Hoàn tất ({self.download_failed_count} chương thất bại). Xem ErrorLog để tải lại.")

    # ------------------------------------------------------------------
    # Private Helpers
    # ------------------------------------------------------------------
    def _extract_story_title(self) -> str:
        """Lấy tên truyện từ URL (sử dụng đoạn path cuối)"""
        path_part = self.url.rstrip("/").split("/")[-1]
        # Chuyển dấu gạch ngang thành khoảng trắng, viết hoa từng chữ
        return path_part.replace("-", " ").title()

    def _prepare_save_paths(self, story_title: str):
        """Chuẩn bị đường dẫn lưu file. Dùng URL slug làm tên thư mục cố định."""
        if not self.save_path:
            return None, None

        ext = f".{self.file_format}"
        base_name = self.save_path
        if not base_name.endswith(ext):
            base_name = base_name + ext

        parent_dir = str(Path(base_name).parent)
        # Dùng URL slug làm tên thư mục cố định (không dùng timestamp nữa)
        slug = self.url.rstrip("/").split("/")[-1] if self.url else story_title.replace(" ", "-").lower()
        save_dir = os.path.join(parent_dir, slug)
        os.makedirs(save_dir, exist_ok=True)

        return save_dir, base_name

    def _save_single_chapter(self, chapter: Chapter, idx: int, save_dir: str):
        """Lưu 1 chương thành file riêng lẻ trong save_dir"""
        try:
            safe_title = re.sub(r'[\\/:*?"<>|]', '_', chapter.title or f"Chuong_{idx + 1}")
            ext = f".{self.file_format}"
            file_path = os.path.join(save_dir, f"{idx + 1:04d}_{safe_title}{ext}")

            with open(file_path, "w", encoding="utf-8") as f:
                if self.file_format == "html":
                    content_str = chapter.content or ""
                    content_str = re.sub(r'(?<!>)\n(?!<)', '<br/>\n', content_str)
                    
                    f.write(f"<h2>{chapter.title}</h2>\n")
                    f.write(f"<div class='chapter-content'>\n{content_str}\n</div>\n")
                else:
                    f.write(f"{chapter.title}\n\n")
                    f.write(html_to_text(chapter.content or ""))
        except Exception as e:
            logger.error(f"Lỗi lưu chương {idx}: {e}")

    def _save_resume_state(self, story_title: str, final_path: str, all_links: list, save_dir: str, chapters_status: list):
        """Lưu state JSON bao gồm cả title và status để khôi phục chính xác"""
        if not final_path:
            return
        
        resume_path = os.path.join(str(Path(final_path).parent), f"{story_title}_Resume.json")
        state = {
            "story_title": story_title,
            "final_path": final_path,
            "save_dir": save_dir,
            "start_idx": self.start_idx,
            "end_idx": self.end_idx,
            "all_links": all_links,
            "chapters_status": chapters_status,
            "failed_links": self.failed_links # Giữ lại cho các tool ngoài nếu cần
        }
        try:
            with open(resume_path, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except:
            pass

    def _save_concatenate_file(self, story_title: str, final_path: str):
        """Gộp tất cả chương đã tải vào 1 file"""
        # Lọc bỏ None (các chương lỗi)
        valid_chapters = [(i, ch) for i, ch in enumerate(self.chapters) if ch is not None]
        try:
            # Dùng utf-8-sig để tự động chèn BOM, sửa lỗi font khi convert sang prc/mobi
            with open(final_path, "w", encoding="utf-8-sig") as f:
                if self.file_format == "html":
                    f.write(f"<!DOCTYPE html><html lang='vi'>\n<head>\n")
                    f.write(f"<meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\" />\n")
                    f.write(f"<title>{story_title}</title>\n</head>\n<body>\n")
                    
                    f.write(f"<style> .chapter-content {{ white-space: pre-wrap; line-height: 1.6; word-wrap: break-word; }} </style>\n")
                    if self.ebook_info:
                        f.write(f"<div id='ebook-info'>{self.ebook_info}</div>\n<hr/>\n")
                    
                    # Mục lục
                    f.write("<div id='toc'><h2>Mục lục</h2><ul>\n")
                    for i, ch in valid_chapters:
                        f.write(f"  <li><a href='#chap-{i}'>{ch.title or f'Chương {i+1}'}</a></li>\n")
                    f.write("</ul></div>\n<hr/>\n")
                    
                    # Nội dung
                    for i, ch in valid_chapters:
                        f.write(f"<a name='chap-{i}'></a>\n")
                        content_str = ch.content or ""
                        
                        # Fix lỗi mất dòng: chuyển \n thành <br/> (trừ khi nó nằm cạnh tag HTML)
                        content_str = re.sub(r'(?<!>)\n(?!<)', '<br/>\n', content_str)
                        
                        # Nếu nội dung chưa có thẻ h2 (trường hợp không resume), chèn thêm
                        if not content_str.strip().startswith("<h2>"):
                            f.write(f"<h2>{ch.title}</h2>\n")
                            
                        f.write(f"<div class='chapter-content'>\n{content_str}\n</div>\n<hr/>\n")
                    f.write("</body></html>\n")
                else:
                    # TXT format
                    if self.ebook_info:
                        f.write(f"{self.ebook_info}\n{'='*60}\n\n")
                    for i, ch in valid_chapters:
                        f.write(f"\n{'='*60}\n")
                        f.write(f"{ch.title or f'Chương {i+1}'}\n")
                        f.write(f"{'='*60}\n\n")
                        # Do resume đã bóc dòng title ra nên html_to_text(ch.content) sẽ chuẩn
                        f.write(html_to_text(ch.content or ""))
                        f.write("\n")

            self.log_signal.emit(f"💾 Đã lưu: {final_path}")
        except Exception as e:
            self.log_signal.emit(f"❌ Lỗi ghi file: {e}")
            logger.error(f"Lỗi ghi file tổng hợp: {e}")


class MergeWorker(QThread):
    """
    Worker gộp các file chương HTML riêng lẻ thành 1 file tổng hợp.
    Scan tất cả *.html trong folder, sort theo tên file (0001_, 0002_,...),
    ghi ra file HTML tổng có TOC và nội dung đầy đủ.
    """
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(str)

    def __init__(self, folder_path: str, output_path: str, story_title: str, ebook_info: str = ""):
        super().__init__()
        self.folder_path = folder_path
        self.output_path = output_path
        self.story_title = story_title
        self.ebook_info = ebook_info

    def run(self):
        try:
            html_files = sorted([
                f for f in os.listdir(self.folder_path) if f.lower().endswith(".html")
            ])
            if not html_files:
                self.log_signal.emit("❌ Không tìm thấy file HTML nào trong thư mục.")
                self.finished_signal.emit("Lỗi: Không tìm thấy file HTML trong thư mục.")
                return

            self.log_signal.emit(f"📂 Tìm thấy {len(html_files)} file chương. Đang gộp...")

            chapters = []  # list of (index, title, raw_content)
            for i, fname in enumerate(html_files):
                fpath = os.path.join(self.folder_path, fname)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        raw = f.read()
                    # Trích title từ thẻ <h2>
                    m = re.search(r"<h2[^>]*>(.*?)</h2>", raw, re.IGNORECASE | re.DOTALL)
                    title = m.group(1) if m else f"Chương {i + 1}"
                    chapters.append((i, title, raw))
                    if (i + 1) % 100 == 0:
                        self.log_signal.emit(f"  📖 Đã đọc {i + 1}/{len(html_files)} chương...")
                except Exception as e:
                    self.log_signal.emit(f"  ⚠️ Lỗi đọc {fname}: {e}")

            self.log_signal.emit(f"💾 Đang ghi file tổng hợp ({len(chapters)} chương)...")

            with open(self.output_path, "w", encoding="utf-8-sig") as f:
                f.write("<!DOCTYPE html><html lang='vi'>\n<head>\n")
                f.write('<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />\n')
                f.write(f"<title>{self.story_title}</title>\n</head>\n<body>\n")
                
                f.write(f"<style> .chapter-content {{ white-space: pre-wrap; line-height: 1.6; word-wrap: break-word; }} </style>\n")

                if self.ebook_info:
                    f.write(f"<div id='ebook-info'>{self.ebook_info}</div>\n<hr/>\n")

                # Mục lục
                f.write("<div id='toc'><h2>Mục lục</h2><ul>\n")
                for i, title, _ in chapters:
                    f.write(f"  <li><a href='#chap-{i}'>{title}</a></li>\n")
                f.write("</ul></div>\n<hr/>\n")

                # Nội dung
                for i, title, raw in chapters:
                    f.write(f"<a name='chap-{i}'></a>\n")
                    # Break long lines for KindleGen to avoid memory overflow (Crash/WinError 32)
                    raw_safe = raw.replace("<br>", "<br/>\n").replace("<br/>", "<br/>\n")
                    f.write(raw_safe)
                    f.write("\n<hr/>\n")

                f.write("</body></html>\n")
            self.log_signal.emit(f"✅ Đã gộp xong → {self.output_path}")
            self.finished_signal.emit(f"Gộp hoàn tất! {len(chapters)} chương → {os.path.basename(self.output_path)}")

        except Exception as e:
            self.log_signal.emit(f"❌ Lỗi gộp file: {e}")
            self.finished_signal.emit(f"Lỗi gộp: {e}")
            logger.error(f"MergeWorker error: {e}")

class PrcWorker(QThread):
    """
    Worker xử lý việc tải kindlegen.exe và biên dịch file HTML thành PRC.
    Chạy trong luồng nền để không chặn giao diện.
    """
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(bool, str) # success (True/False), message

    def __init__(self, html_path: str, base_dir: str, final_prc_path: str = None):
        super().__init__()
        self.html_path = html_path
        self.base_dir = base_dir
        self.final_prc_path = final_prc_path
        self._is_running = True
        self.compiler = None

    def stop(self):
        self._is_running = False
        if self.compiler:
            self.compiler.cancel()
        self.quit()

    def run(self):
        try:
            # Load PrcCompiler dynamically inside run to avoid circular import if any
            from core.prc_compiler import PrcCompiler
            self.compiler = PrcCompiler(self.base_dir)

            self.log_signal.emit("🔎 Đang kiểm tra công cụ biên dịch PRC...")
            # progress callback
            def on_progress(msg):
                self.log_signal.emit(msg)
            
            def on_percent(pct):
                self.progress_signal.emit(pct)

            if not self.compiler.check_and_download_kindlegen(progress_callback=on_progress):
                self.finished_signal.emit(False, "Lỗi: Không thể tải hoặc tìm thấy kindlegen.exe")
                return

            if not self._is_running:
                return

            self.log_signal.emit("🚀 Bắt đầu quá trình biên dịch HTML sang PRC...")
            success = self.compiler.compile_html_to_prc(
                self.html_path, 
                log_callback=on_progress, 
                percent_callback=on_percent,
                final_prc_path=self.final_prc_path
            )
            
            if not self._is_running:
                return

            if success:
                self.finished_signal.emit(True, "Biên dịch PRC thành công!")
            else:
                self.finished_signal.emit(False, "Biên dịch PRC thất bại!")
                
        except Exception as e:
            self.log_signal.emit(f"❌ Lỗi PrcWorker: {e}")
            self.finished_signal.emit(False, f"Lỗi ngoại lệ: {e}")
            import logging
            logging.error(f"PrcWorker error: {e}")
