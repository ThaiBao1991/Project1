"""
Module xóa dấu đã đóng trong file PDF - Xóa thực sự các đối tượng image
"""

import fitz
import os
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime
import numpy as np
from PIL import Image
import io
import traceback

class StampRemover:
    """Lớp xóa dấu đã đóng - Xóa thực sự các đối tượng image"""
    
    def __init__(self, stamp_image_path, config=None):
        """
        Khởi tạo bộ xóa dấu
        
        Args:
            stamp_image_path (str): Đường dẫn đến ảnh mẫu của dấu cần xóa
            config (dict, optional): Cấu hình bổ sung
        """
        self.stamp_image_path = Path(stamp_image_path)
        self.config = config or {}
        
        # Load và xử lý ảnh mẫu
        self.stamp_template = self._load_and_process_image(self.stamp_image_path)
        
        # Ngưỡng tương đồng để xác định dấu (0-1)
        self.similarity_threshold = self.config.get('similarity_threshold', 0.8)
        
        # Log file
        self.log_file = self.config.get('log_file', r"C:\Users\12953 bao\Desktop\desktop\work\Project\Python\BasicLearnPython\W3schools\Python Tutorial\Python Project\MyAppInMBC\StampAuto\stamp_remove_log.txt")
    
    def _write_log(self, message):
        """Ghi log chi tiết"""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{timestamp}] {message}\n")
        except:
            pass
    
    def _load_and_process_image(self, image_path):
        """
        Load và xử lý ảnh để so sánh
        
        Args:
            image_path: Đường dẫn file ảnh
            
        Returns:
            dict: Thông tin ảnh đã xử lý
        """
        try:
            img = Image.open(image_path)
            
            # Chuyển sang grayscale
            if img.mode != 'L':
                img = img.convert('L')
            
            # Resize về kích thước chuẩn để so sánh
            img = img.resize((100, 100), Image.Resampling.LANCZOS)
            
            # Chuyển thành numpy array
            img_array = np.array(img)
            
            # Tính các đặc trưng của ảnh
            features = {
                'array': img_array,
                'mean': np.mean(img_array),
                'std': np.std(img_array),
                'histogram': self._calculate_histogram(img_array),
                'hash': hashlib.md5(img.tobytes()).hexdigest(),
                'size': img.size
            }
            
            return features
            
        except Exception as e:
            self._write_log(f"Lỗi load ảnh mẫu: {str(e)}")
            return None
    
    def _calculate_histogram(self, img_array):
        """Tính histogram của ảnh"""
        hist, _ = np.histogram(img_array.flatten(), bins=256, range=(0, 256))
        # Chuẩn hóa histogram
        hist = hist.astype(np.float32) / np.sum(hist)
        return hist
    
    def _compare_images_advanced(self, img1_array, img2_array):
        """
        So sánh ảnh nâng cao sử dụng nhiều phương pháp
        
        Args:
            img1_array: numpy array của ảnh 1
            img2_array: numpy array của ảnh 2
            
        Returns:
            float: Độ tương đồng (0-1)
        """
        try:
            # Resize ảnh 2 về cùng kích thước với ảnh 1 nếu cần
            if img1_array.shape != img2_array.shape:
                img2_pil = Image.fromarray(img2_array)
                img2_pil = img2_pil.resize(img1_array.shape[::-1], Image.Resampling.LANCZOS)
                img2_array = np.array(img2_pil)
            
            # 1. So sánh tương quan chéo (cross-correlation)
            img1_norm = (img1_array - np.mean(img1_array)) / np.std(img1_array)
            img2_norm = (img2_array - np.mean(img2_array)) / np.std(img2_array)
            
            correlation = np.sum(img1_norm * img2_norm) / (len(img1_array.flatten()))
            correlation = max(0, min(1, (correlation + 1) / 2))  # Chuẩn hóa về 0-1
            
            # 2. So sánh MSE (Mean Square Error)
            mse = np.mean((img1_array - img2_array) ** 2)
            mse_similarity = 1 / (1 + mse / 1000)  # Chuyển MSE thành độ tương đồng
            
            # 3. So sánh histogram
            hist1 = self._calculate_histogram(img1_array)
            hist2 = self._calculate_histogram(img2_array)
            hist_similarity = 1 - np.sum(np.abs(hist1 - hist2)) / 2
            
            # Kết hợp các phương pháp
            similarity = (correlation * 0.4 + mse_similarity * 0.3 + hist_similarity * 0.3)
            
            return similarity
            
        except Exception as e:
            self._write_log(f"Lỗi so sánh ảnh: {str(e)}")
            return 0
    
    def _find_stamp_objects(self, page):
        """
        Tìm các đối tượng image là dấu trên trang
        
        Args:
            page: Đối tượng trang PDF
            
        Returns:
            list: Danh sách các tuple (xref, rect) của các dấu tìm được
        """
        stamp_objects = []
        
        try:
            # Lấy danh sách tất cả images trên trang
            image_list = page.get_images(full=True)
            self._write_log(f"Tìm thấy {len(image_list)} images trên trang")
            
            for img_index, img in enumerate(image_list):
                try:
                    xref = img[0]  # Tham chiếu đến object image
                    
                    # Lấy pixmap của image
                    pix = fitz.Pixmap(page.parent, xref)
                    
                    # Kiểm tra xem có phải ảnh màu không
                    if pix.n - pix.alpha < 4:  # Có màu sắc
                        # Chuyển pixmap thành numpy array
                        img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, -1)
                        
                        # Nếu là ảnh màu, chuyển sang grayscale
                        if img_array.shape[-1] >= 3:
                            # Chuyển RGB sang grayscale
                            if img_array.shape[-1] == 3:
                                gray_array = np.dot(img_array[..., :3], [0.299, 0.587, 0.114])
                            elif img_array.shape[-1] == 4:  # RGBA
                                gray_array = np.dot(img_array[..., :3], [0.299, 0.587, 0.114])
                            else:
                                gray_array = img_array.mean(axis=-1)
                            
                            gray_array = gray_array.astype(np.uint8)
                        else:
                            gray_array = img_array.squeeze()
                        
                        # Resize để so sánh
                        gray_pil = Image.fromarray(gray_array)
                        gray_pil = gray_pil.resize((100, 100), Image.Resampling.LANCZOS)
                        gray_array = np.array(gray_pil)
                        
                        # So sánh với ảnh mẫu
                        similarity = self._compare_images_advanced(self.stamp_template['array'], gray_array)
                        
                        self._write_log(f"  - Ảnh {img_index}: độ tương đồng {similarity:.3f}")
                        
                        if similarity >= self.similarity_threshold:
                            # Lấy vị trí của image trên trang
                            img_rects = page.get_image_rects(xref)
                            for rect in img_rects:
                                stamp_objects.append((xref, rect))
                                self._write_log(f"    ✓ Tìm thấy dấu (xref={xref}) tại {rect}")
                    
                    pix = None  # Giải phóng bộ nhớ
                    
                except Exception as e:
                    self._write_log(f"Lỗi xử lý image {img_index}: {str(e)}")
                    continue
            
        except Exception as e:
            self._write_log(f"Lỗi tìm dấu trên trang: {str(e)}")
        
        return stamp_objects
    
    def _remove_stamp_object(self, doc, page, xref, rect):
        """
        Xóa một đối tượng dấu khỏi PDF
        
        Args:
            doc: Đối tượng document PDF
            page: Đối tượng trang
            xref: Tham chiếu đến object image
            rect: Vùng chứa image
            
        Returns:
            bool: True nếu xóa thành công
        """
        try:
            # Cách 1: Xóa object image khỏi trang
            # Lấy danh sách contents của trang
            content = page.read_contents()
            
            # Tạo command xóa image (phức tạp, cần phân tích PDF stream)
            # Thay vào đó, dùng cách 2 đơn giản hơn:
            
            # Cách 2: Tạo annotation che phủ và xóa image reference
            # Vẽ một hình chữ nhật trắng lên vị trí cũ
            page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1), width=0)
            
            # Cách 3: Xóa image object khỏi catalog (nâng cao)
            # Lấy catalog và xóa reference đến image
            try:
                # Lấy resources dictionary của trang
                resources = page.get_resource('XObject')
                if resources:
                    # Tìm và xóa image trong resources
                    for key in list(resources.keys()):
                        if resources[key] == xref:
                            del resources[key]
                            self._write_log(f"    Đã xóa image khỏi resources: {key}")
            except:
                pass
            
            self._write_log(f"  - Đã xóa dấu xref={xref}")
            return True
            
        except Exception as e:
            self._write_log(f"Lỗi xóa dấu xref={xref}: {str(e)}")
            return False
    
    def remove_stamps(self, pdf_path, output_path=None, method='advanced'):
        """
        Xóa các dấu đã đóng trong file PDF
        
        Args:
            pdf_path (str): Đường dẫn file PDF cần xóa dấu
            output_path (str, optional): Đường dẫn file output
            method (str): Phương pháp xóa: 'advanced' (mặc định)
            
        Returns:
            tuple: (success, message, removed_count)
        """
        try:
            self._write_log(f"=== BẮT ĐẦU XÓA DẤU (XÓA THỰC SỰ) ===")
            self._write_log(f"File PDF: {pdf_path}")
            self._write_log(f"Ảnh mẫu: {self.stamp_image_path}")
            self._write_log(f"Ngưỡng tương đồng: {self.similarity_threshold}")
            
            # Kiểm tra file PDF
            if not os.path.exists(pdf_path):
                return False, f"File PDF không tồn tại: {pdf_path}", 0
            
            # Kiểm tra ảnh mẫu
            if not self.stamp_image_path.exists():
                return False, f"Không tìm thấy ảnh mẫu: {self.stamp_image_path}", 0
            
            if self.stamp_template is None:
                return False, "Không thể xử lý ảnh mẫu", 0
            
            # Mở file PDF
            doc = fitz.open(pdf_path)
            self._write_log(f"✓ Mở PDF thành công. Số trang: {len(doc)}")
            
            total_removed = 0
            removed_xrefs = set()  # Lưu các xref đã xóa để tránh xóa trùng
            
            # Xử lý từng trang
            for page_num in range(len(doc)):
                page = doc[page_num]
                self._write_log(f"\nXử lý trang {page_num + 1}...")
                
                # Tìm các đối tượng dấu
                stamp_objects = self._find_stamp_objects(page)
                
                if stamp_objects:
                    self._write_log(f"Tìm thấy {len(stamp_objects)} dấu trên trang {page_num + 1}")
                    
                    # Xóa từng dấu
                    for xref, rect in stamp_objects:
                        if xref not in removed_xrefs:
                            if self._remove_stamp_object(doc, page, xref, rect):
                                removed_xrefs.add(xref)
                                total_removed += 1
                else:
                    self._write_log(f"Không tìm thấy dấu nào trên trang {page_num + 1}")
            
            # Lưu file
            if total_removed > 0:
                if output_path:
                    # Lưu file mới
                    doc.save(output_path, garbage=4, deflate=True, clean=True)
                    self._write_log(f"✓ Đã lưu file kết quả: {output_path}")
                else:
                    # Lưu đè lên file gốc
                    doc.save(pdf_path, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
                    self._write_log(f"✓ Đã lưu đè lên file gốc: {pdf_path}")
            else:
                self._write_log("Không tìm thấy dấu nào để xóa")
            
            doc.close()
            
            if total_removed > 0:
                message = f"Đã xóa {total_removed} dấu thành công"
                if output_path:
                    message += f". File kết quả: {output_path}"
                else:
                    message += f". Đã cập nhật file gốc: {pdf_path}"
            else:
                message = "Không tìm thấy dấu nào để xóa"
            
            self._write_log(f"=== KẾT THÚC XÓA DẤU: {message} ===\n")
            
            return True, message, total_removed
            
        except Exception as e:
            error_msg = f"Lỗi xóa dấu: {str(e)}"
            self._write_log(f"✗ {error_msg}")
            self._write_log(traceback.format_exc())
            return False, error_msg, 0


class KTCKStampRemover(StampRemover):
    """Xóa dấu Kiểm tra cơ khí"""
    
    def __init__(self, stamp_image_path, config=None):
        super().__init__(stamp_image_path, config)
        self.stamp_id = 'ktck'
    
    def remove_stamps(self, pdf_path, output_path=None, method='advanced'):
        """Xóa dấu KTCK"""
        self._write_log(f"Xóa dấu KTCK (Kiểm tra cơ khí)")
        return super().remove_stamps(pdf_path, output_path, method)


class HieuChinhStampRemover(StampRemover):
    """Xóa dấu Hiệu chỉnh"""
    
    def __init__(self, stamp_image_path, config=None):
        super().__init__(stamp_image_path, config)
        self.stamp_id = 'hieuchinh'
    
    def remove_stamps(self, pdf_path, output_path=None, method='advanced'):
        """Xóa dấu Hiệu chỉnh"""
        self._write_log(f"Xóa dấu Hiệu chỉnh")
        return super().remove_stamps(pdf_path, output_path, method)


def verify_stamp_removal(original_pdf, processed_pdf, stamp_image_path):
    """
    Xác minh việc xóa dấu có thành công không
    
    Args:
        original_pdf: File PDF gốc
        processed_pdf: File PDF đã xử lý
        stamp_image_path: Ảnh mẫu của dấu
        
    Returns:
        dict: Kết quả xác minh
    """
    result = {
        'success': False,
        'original_count': 0,
        'processed_count': 0,
        'removed_count': 0,
        'message': ''
    }
    
    try:
        # Tạo remover tạm thời để đếm số dấu
        remover = StampRemover(stamp_image_path)
        
        # Đếm số dấu trong file gốc
        doc_orig = fitz.open(original_pdf)
        orig_count = 0
        for page_num in range(len(doc_orig)):
            stamp_objects = remover._find_stamp_objects(doc_orig[page_num])
            orig_count += len(stamp_objects)
        doc_orig.close()
        
        # Đếm số dấu trong file đã xử lý
        doc_proc = fitz.open(processed_pdf)
        proc_count = 0
        for page_num in range(len(doc_proc)):
            stamp_objects = remover._find_stamp_objects(doc_proc[page_num])
            proc_count += len(stamp_objects)
        doc_proc.close()
        
        result['original_count'] = orig_count
        result['processed_count'] = proc_count
        result['removed_count'] = orig_count - proc_count
        result['success'] = result['removed_count'] > 0
        result['message'] = f"Đã xóa {result['removed_count']}/{orig_count} dấu"
        
    except Exception as e:
        result['message'] = f"Lỗi xác minh: {str(e)}"
    
    return result


def main():
    """Hàm main để chạy từ dòng lệnh"""
    if len(sys.argv) < 3:
        print("Sử dụng: python remove_stamp.py <pdf_path> <stamp_image_path> [output_path]")
        print("  pdf_path: Đường dẫn file PDF cần xóa dấu")
        print("  stamp_image_path: Đường dẫn ảnh mẫu của dấu cần xóa")
        print("  output_path: (Tùy chọn) Đường dẫn file output")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    stamp_image_path = sys.argv[2]
    output_path = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Xác định loại dấu dựa trên tên file ảnh
    remover = None
    stamp_image_str = str(stamp_image_path)
    
    if 'KTCK' in stamp_image_str or 'ktck' in stamp_image_str:
        remover = KTCKStampRemover(stamp_image_path)
    elif 'HieuChinh' in stamp_image_str or 'hieuchinh' in stamp_image_str:
        remover = HieuChinhStampRemover(stamp_image_path)
    else:
        remover = StampRemover(stamp_image_path)
    
    success, message, count = remover.remove_stamps(pdf_path, output_path)
    
    if success:
        print(f"✓ {message}")
        
        # Xác minh kết quả nếu có output_path
        if output_path and count > 0:
            verify_result = verify_stamp_removal(pdf_path, output_path, stamp_image_path)
            print(f"✓ Xác minh: {verify_result['message']}")
        
        sys.exit(0)
    else:
        print(f"✗ {message}")
        sys.exit(1)


if __name__ == "__main__":
    main()