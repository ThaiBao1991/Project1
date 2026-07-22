import os
import shutil
import hashlib
import tempfile
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

def get_aes_key(password: str) -> bytes:
    """Tạo khóa AES 256-bit từ mật khẩu bằng SHA-256."""
    return hashlib.sha256(password.encode('utf-8')).digest()

def encrypt_folder(folder_path: str, output_file: str, password: str):
    """
    Nén thư mục thành file zip tạm, mã hóa stream (chunk) nội dung bằng mật khẩu 
    và lưu thành output_file (.askcpl) để tiết kiệm RAM.
    """
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"Thư mục không tồn tại: {folder_path}")

    # Tạo file zip tạm
    temp_zip_fd, temp_zip_path = tempfile.mkstemp(suffix='.zip')
    os.close(temp_zip_fd)
    
    try:
        # Nén thư mục vào file tạm
        base_name = temp_zip_path[:-4]
        shutil.make_archive(base_name, 'zip', folder_path)
        
        # Mã hóa dạng luồng (streaming)
        key = get_aes_key(password)
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(key), modes.CTR(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        
        with open(temp_zip_path, 'rb') as fin, open(output_file, 'wb') as fout:
            fout.write(iv)  # Ghi IV vào đầu file
            while True:
                chunk = fin.read(64 * 1024)
                if len(chunk) == 0:
                    break
                fout.write(encryptor.update(chunk))
            fout.write(encryptor.finalize())
            
    finally:
        if os.path.exists(temp_zip_path):
            os.remove(temp_zip_path)

def decrypt_file(input_file: str, output_folder: str, password: str):
    """
    Đọc file mã hóa dạng stream, giải mã bằng mật khẩu, lưu thành file zip tạm 
    và giải nén ra output_folder.
    """
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"File không tồn tại: {input_file}")

    key = get_aes_key(password)
    
    # Tạo thư mục đầu ra nếu chưa có
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        
    # Lưu file zip tạm
    temp_zip_fd, temp_zip_path = tempfile.mkstemp(suffix='.zip')
    os.close(temp_zip_fd)
    
    try:
        with open(input_file, 'rb') as fin, open(temp_zip_path, 'wb') as fout:
            iv = fin.read(16)
            if len(iv) < 16:
                raise ValueError("File quá ngắn hoặc bị hỏng.")
                
            cipher = Cipher(algorithms.AES(key), modes.CTR(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            
            while True:
                chunk = fin.read(64 * 1024)
                if len(chunk) == 0:
                    break
                fout.write(decryptor.update(chunk))
            fout.write(decryptor.finalize())
            
        # Giải nén vào output_folder. Nếu sai pass, dữ liệu zip sẽ lỗi và văng Exception.
        try:
            shutil.unpack_archive(temp_zip_path, output_folder, 'zip')
        except Exception:
            raise ValueError("Sai mật khẩu hoặc file bị hỏng.")
            
    finally:
        if os.path.exists(temp_zip_path):
            os.remove(temp_zip_path)

