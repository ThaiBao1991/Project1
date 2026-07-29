"""
workers.py — QThread worker cho việc tải truyện
Tương đương TAuto.java của phiên bản Java gốc.
"""

import os
import re
import time
import logging
from datetime import datetime
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal
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
    # Khi lấy xong danh sách chương → gửi về UI để hiện hộp thoại Range nếu cần
    chapter_list_ready = pyqtSignal(int)          # total_count

    def __init__(self, url: str, config_mgr: PageConfigManager, save_path: str,
                 is_divide_file: bool = False, ebook_info: str = "",
                 start_idx: int = 0, end_idx: int = -1, file_format: str = "html",
                 manual_links: list[str] = None, page_config=None):
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

    # ------------------------------------------------------------------
    # Main Thread Entry
    # ------------------------------------------------------------------
    def run(self):
        try:
            # Lấy PageConfig
            page_config = self.forced_page_config or self.config_mgr.get_config_by_url(self.url)
            if not page_config:
                self.log_signal.emit(f"❌ Không tìm thấy cấu hình hỗ trợ cho URL: {self.url}")
                self.finished_signal.emit("Lỗi: Không hỗ trợ site này.")
                return

            self.log_signal.emit(f"🔄 Sử dụng cấu hình host: {page_config.page_code}")

            # Lấy danh sách link (nếu không phải Manual GET)
            if self.manual_links is not None:
                all_links = self.manual_links
                self.log_signal.emit(f"🔎 Đang tải thủ công {len(all_links)} link...")
            else:
                self.log_signal.emit("🔎 Đang phân tích mục lục...")
                all_links = self.engine.get_list_chapter_links(self.url, page_config)

            if not all_links:
                self.log_signal.emit("❌ Không tìm thấy danh sách chương nào.")
                self.finished_signal.emit("Lỗi: Không tìm thấy link chương.")
                return

        except Exception as e:
            logger.error(f"Error in run: {e}")
            self.finished_signal.emit("Lỗi hệ thống")
            return

        total = len(all_links)
        self.log_signal.emit(f"✅ Đã tìm thấy {total} chương.")
        self.chapter_list_ready.emit(total)

        # Xác định phạm vi tải (Download Range)
        start = self.start_idx
        end = self.end_idx if self.end_idx != -1 else total - 1
        end = min(end, total - 1)
        selected_links = all_links[start:end + 1]

        self.log_signal.emit(f"📥 Bắt đầu tải từ chương {start + 1} đến {end + 1} ({len(selected_links)} chương)...")

        # Xác định tên file / thư mục lưu
        story_title = self._extract_story_title()
        save_dir, final_path = self._prepare_save_paths(story_title)

        self.chapters = []

        for local_idx, link in enumerate(selected_links):
            if not self.is_running:
                self.log_signal.emit("⏹️ Đã hủy tải xuống.")
                break

            global_idx = start + local_idx
            self.progress_signal.emit(global_idx, "Đang tải...", "")

            # Ghép URL tương đối thành tuyệt đối
            full_link = link if link.startswith("http") else f"https://{page_config.page_code}{link}"

            chapter = self.engine.get_chapter_title_and_content(full_link, page_config)
            chapter.url = full_link

            if chapter.is_get_failed:
                self.download_failed_count += 1
                self.failed_links.append(full_link)
                self.progress_signal.emit(global_idx, "❌ Lỗi", "Không tải được nội dung")
                self.log_signal.emit(f"  ⚠️ Thất bại: {full_link}")
            else:
                self.chapters.append(chapter)
                self.progress_signal.emit(global_idx, "✅ Xong", "")
                self.log_signal.emit(f"  ✅ Chương {global_idx + 1}: {chapter.title[:50] if chapter.title else '(no title)'}")

                # Luôn lưu thành file lẻ (nếu không chia file thì đây là file tạm để resume)
                if save_dir:
                    self._save_single_chapter(chapter, local_idx, save_dir)
                    
            self._save_resume_state(story_title, final_path, selected_links)

            time.sleep(0.3)  # Tránh spam request

        # Gộp file nếu không chia
        if self.is_running and not self.is_divide_file and final_path:
            self.log_signal.emit("📝 Đang ghi file tổng hợp...")
            self._save_concatenate_file(story_title, final_path)

        # Ghi log lỗi nếu có
        if self.failed_links and final_path:
            error_log_path = os.path.join(str(Path(final_path).parent), f"{story_title}_ErrorLog.txt")
            try:
                with open(error_log_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(self.failed_links))
                self.log_signal.emit(f"📝 Đã ghi danh sách {len(self.failed_links)} link lỗi vào: {error_log_path}")
            except Exception as e:
                logger.error(f"Lỗi ghi error log: {e}")
                
        # Dọn dẹp thư mục tạm nếu tải gộp file thành công 100%
        if not self.is_divide_file and not self.failed_links and save_dir:
            import shutil
            try:
                shutil.rmtree(save_dir)
                self.log_signal.emit("🧹 Đã dọn dẹp thư mục tải tạm.")
            except Exception as e:
                pass

        failed_msg = f" ({self.download_failed_count} chương thất bại)" if self.download_failed_count else ""
        self.finished_signal.emit(f"Hoàn tất{failed_msg}")

    # ------------------------------------------------------------------
    # Private Helpers
    # ------------------------------------------------------------------
    def _extract_story_title(self) -> str:
        """Lấy tên truyện từ URL (sử dụng đoạn path cuối)"""
        path_part = self.url.rstrip("/").split("/")[-1]
        # Chuyển dấu gạch ngang thành khoảng trắng, viết hoa từng chữ
        return path_part.replace("-", " ").title()

    def _prepare_save_paths(self, story_title: str):
        """Chuẩn bị đường dẫn lưu file.
        Trả về (save_dir, final_path) — save_dir dùng cho chia file, final_path dùng cho gộp file.
        """
        if not self.save_path:
            return None, None

        ext = f".{self.file_format}"
        base_name = self.save_path
        if not base_name.endswith(ext):
            base_name = base_name + ext

        # Thư mục tạm để mỗi chương lưu riêng, sau đó gộp
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        parent_dir = str(Path(base_name).parent)
        folder_name = f"{Path(base_name).stem}_GHFU_{timestamp}"
        save_dir = os.path.join(parent_dir, folder_name)
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
                    f.write(f"<h2>{chapter.title}</h2>\n")
                    f.write(chapter.content or "")
                else:
                    f.write(f"{chapter.title}\n\n")
                    f.write(html_to_text(chapter.content or ""))
        except Exception as e:
            logger.error(f"Lỗi lưu chương {idx}: {e}")

    def _save_resume_state(self, story_title: str, final_path: str, all_links: list):
        import json
        if not final_path:
            return
        
        resume_path = os.path.join(str(Path(final_path).parent), f"{story_title}_Resume.json")
        state = {
            "story_title": story_title,
            "final_path": final_path,
            "total_links": len(all_links),
            "failed_links": self.failed_links
        }
        try:
            with open(resume_path, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except:
            pass

    def _save_concatenate_file(self, story_title: str, final_path: str):
        """Gộp tất cả chương đã tải vào 1 file (tương đương writeConcatenateFile Java)"""
        try:
            # Dùng utf-8-sig để tự động chèn BOM (Byte Order Mark), sửa lỗi font khi convert sang prc/mobi
            with open(final_path, "w", encoding="utf-8-sig") as f:
                if self.file_format == "html":
                    f.write(f"<!DOCTYPE html><html lang='vi'>\n<head>\n")
                    f.write(f"<meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\" />\n")
                    f.write(f"<title>{story_title}</title>\n</head>\n<body>\n")
                    # Thông tin ebook
                    if self.ebook_info:
                        f.write(f"<div id='ebook-info'>{self.ebook_info}</div>\n<hr/>\n")
                    # Mục lục
                    f.write("<div id='toc'><h2>Mục lục</h2><ul>\n")
                    for i, ch in enumerate(self.chapters):
                        f.write(f"  <li><a href='#chap-{i}'>{ch.title or f'Chương {i+1}'}</a></li>\n")
                    f.write("</ul></div>\n<hr/>\n")
                    # Nội dung
                    for i, ch in enumerate(self.chapters):
                        f.write(f"<a name='chap-{i}'></a>\n")
                        f.write(f"<h2>{ch.title}</h2>\n")
                        f.write(ch.content or "")
                        f.write("\n<hr/>\n")
                    f.write("</body></html>\n")
                else:
                    # TXT format
                    if self.ebook_info:
                        f.write(f"{self.ebook_info}\n{'='*60}\n\n")
                    for i, ch in enumerate(self.chapters):
                        f.write(f"\n{'='*60}\n")
                        f.write(f"{ch.title or f'Chương {i+1}'}\n")
                        f.write(f"{'='*60}\n\n")
                        f.write(html_to_text(ch.content or ""))
                        f.write("\n")

            self.log_signal.emit(f"💾 Đã lưu: {final_path}")
        except Exception as e:
            self.log_signal.emit(f"❌ Lỗi ghi file: {e}")
            logger.error(f"Lỗi ghi file tổng hợp: {e}")
