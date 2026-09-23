import os
import io
import shutil
import hashlib
import tempfile
import zipfile
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# Chunk size t\u1ed1i \u01b0u cho I/O hi\u1ec7n \u0111\u1ea1i (4MB thay v\u00ec 64KB \u2192 ~3x nhanh h\u01a1n)
_CHUNK = 4 * 1024 * 1024

def get_aes_key(password: str) -> bytes:
    """T\u1ea1o kh\u00f3a AES 256-bit t\u1eeb m\u1eadt kh\u1ea9u b\u1eb1ng SHA-256."""
    return hashlib.sha256(password.encode('utf-8')).digest()

def _make_cipher(key: bytes, iv: bytes, mode='decrypt'):
    cipher = Cipher(algorithms.AES(key), modes.CTR(iv), backend=default_backend())
    return cipher.decryptor() if mode == 'decrypt' else cipher.encryptor()

def _stream_encrypt(fin, fout, password: str):
    """M\u00e3 ho\u00e1 stream t\u1eeb fin sang fout. Ghi IV 16 byte v\u00e0o \u0111\u1ea7u fout."""
    key = get_aes_key(password)
    iv = os.urandom(16)
    enc = _make_cipher(key, iv, 'encrypt')
    fout.write(iv)
    while True:
        chunk = fin.read(_CHUNK)
        if not chunk:
            break
        fout.write(enc.update(chunk))
    fout.write(enc.finalize())

def _stream_decrypt(fin, fout, password: str):
    """Gi\u1ea3i m\u00e3 stream t\u1eeb fin sang fout. \u0110\u1ecdc IV 16 byte \u0111\u1ea7u t\u1eeb fin."""
    key = get_aes_key(password)
    iv = fin.read(16)
    if len(iv) < 16:
        raise ValueError("File qu\u00e1 ng\u1eafn ho\u1eb7c b\u1ecb h\u1ecfng.")
    dec = _make_cipher(key, iv, 'decrypt')
    while True:
        chunk = fin.read(_CHUNK)
        if not chunk:
            break
        fout.write(dec.update(chunk))
    fout.write(dec.finalize())

# --------------------------------------------------------------------------- #
#  PUBLIC API                                                                   #
# --------------------------------------------------------------------------- #

def encrypt_folder(folder_path: str, output_file: str, password: str):
    """
    N\xe9n th\u01b0 m\u1ee5c th\u00e0nh zip t\u1ea1m, m\u00e3 h\xf3a stream b\u1eb1ng AES-CTR v\u00e0 l\u01b0u th\u00e0nh
    output_file (.askcpl). D\xf9ng cho c\xf4ng c\u1ee5 m\u00e3 ho\u00e1 th\u01b0 m\u1ee5c th\xf4ng th\u01b0\u1eddng.
    """
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"Th\u01b0 m\u1ee5c kh\xf4ng t\u1ed3n t\u1ea1i: {folder_path}")

    temp_zip_fd, temp_zip_path = tempfile.mkstemp(suffix='.zip')
    os.close(temp_zip_fd)
    try:
        shutil.make_archive(temp_zip_path[:-4], 'zip', folder_path)
        with open(temp_zip_path, 'rb') as fin, open(output_file, 'wb') as fout:
            _stream_encrypt(fin, fout, password)
    finally:
        if os.path.exists(temp_zip_path):
            os.remove(temp_zip_path)


def decrypt_file(input_file: str, output_folder: str, password: str):
    """
    Gi\u1ea3i m\u00e3 file .askcpl v\u00e0 gi\u1ea3i n\xe9n ra output_folder.
    D\xf9ng cho c\xf4ng c\u1ee5 gi\u1ea3i m\u00e3 th\u01b0 m\u1ee5c \u0111\u1ea7y \u0111\u1ee7.
    """
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"File kh\xf4ng t\u1ed3n t\u1ea1i: {input_file}")
    os.makedirs(output_folder, exist_ok=True)

    temp_zip_fd, temp_zip_path = tempfile.mkstemp(suffix='.zip')
    os.close(temp_zip_fd)
    try:
        with open(input_file, 'rb') as fin, open(temp_zip_path, 'wb') as fout:
            _stream_decrypt(fin, fout, password)
        try:
            shutil.unpack_archive(temp_zip_path, output_folder, 'zip')
        except Exception:
            raise ValueError("Sai m\u1eadt kh\u1ea9u ho\u1eb7c file b\u1ecb h\u1ecfng.")
    finally:
        if os.path.exists(temp_zip_path):
            os.remove(temp_zip_path)


def decrypt_to_memory(input_file: str, password: str,
                      max_size_mb: float = 500.0) -> tuple:
    """
    Gi\u1ea3i m\u00e3 file .askcpl v\u00e0o RAM (io.BytesIO) \u2014 kh\xf4ng ghi ra \u0111\u0129a.
    Tr\u1ea3 v\u1ec1 (BytesIO, True) n\u1ebfu trong m\u1ee9c cho ph\xe9p.

    N\u1ebfu file l\u1edbn h\u01a1n max_size_mb th\xec t\u1ef1 fallback ghi ra \u0111\u0129a,
    tr\u1ea3 v\u1ec1 (path_string, False).

    Ng\u01b0\u1eddi g\u1ecdi ki\u1ec3m tra bool th\u1ee9 hai \u0111\u1ec3 bi\u1ebft \u0111ang \u1edf ch\u1ebf \u0111\u1ed9 n\u00e0o.
    """
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"File kh\xf4ng t\u1ed3n t\u1ea1i: {input_file}")

    file_size_mb = os.path.getsize(input_file) / (1024 * 1024)

    if file_size_mb > max_size_mb:
        # Fallback: ghi ra \u0111\u0129a \u0111\u1ec3 tr\xe1nh OOM
        path = decrypt_to_zip(input_file, password)
        return path, False

    # === In-memory path (nhanh nh\u1ea5t) ===
    buf = io.BytesIO()
    with open(input_file, 'rb') as fin:
        _stream_decrypt(fin, buf, password)
    buf.seek(0)

    # Ki\u1ec3m tra zip h\u1ee3p l\u1ec7 (\u0111\u1ec3 b\u1eaft sai password)
    try:
        with zipfile.ZipFile(buf, 'r'):
            pass
    except zipfile.BadZipFile:
        raise ValueError("Sai m\u1eadt kh\u1ea9u ho\u1eb7c file b\u1ecb h\u1ecfng.")
    buf.seek(0)
    return buf, True


def decrypt_to_zip(input_file: str, password: str) -> str:
    """
    Gi\u1ea3i m\u00e3 file .askcpl ra m\u1ed9t file .zip t\u1ea1m tr\xean \u0111\u0129a v\u00e0 tr\u1ea3 v\u1ec1 \u0111\u01b0\u1eddng d\u1eabn.
    D\xf9ng khi file qu\xe1 l\u1edbn \u0111\u1ec3 n\u1ea1p v\u00e0o RAM (fallback c\u1ee7a decrypt_to_memory).
    """
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"File kh\xf4ng t\u1ed3n t\u1ea1i: {input_file}")

    temp_zip_fd, temp_zip_path = tempfile.mkstemp(suffix='.zip')
    os.close(temp_zip_fd)
    try:
        with open(input_file, 'rb') as fin, open(temp_zip_path, 'wb') as fout:
            _stream_decrypt(fin, fout, password)
        try:
            with zipfile.ZipFile(temp_zip_path, 'r'):
                pass
        except zipfile.BadZipFile:
            raise ValueError("Sai m\u1eadt kh\u1ea9u ho\u1eb7c file b\u1ecb h\u1ecfng.")
        return temp_zip_path
    except Exception as e:
        if os.path.exists(temp_zip_path):
            os.remove(temp_zip_path)
        raise e


def encrypt_from_zip_and_folder(old_zip_source, folder_path: str,
                                 output_file: str, password: str,
                                 deleted_files: set = None):
    """
    T\u1ea1o file .askcpl m\u1edbi b\u1eb1ng c\xe1ch h\u1ee3p nh\u1ea5t:
      - C\xe1c file trong folder_path (\u0111\u00e3 ch\u1ec9nh s\u1eeda / t\u1ea1o m\u1edbi) \u2014 \u01b0u ti\xean cao nh\u1ea5t
      - C\xe1c file c\xf2n l\u1ea1i t\u1eeb old_zip_source (kh\xf4ng b\u1ecb s\u1eeda, kh\xf4ng b\u1ecb x\xf3a)

    old_zip_source: str (\u0111\u01b0\u1eddng d\u1eabn \u0111\u1ebfn file .zip) HO\u1eb6C io.BytesIO
    deleted_files:  set c\xe1c t\xean file (zip path) \u0111\u00e3 b\u1ecb x\xf3a c\u1ea7n lo\u1ea1i b\u1ecf
    """
    if deleted_files is None:
        deleted_files = set()

    # M\u1edf old_zip_source d\xf9 l\u00e0 path hay BytesIO
    if isinstance(old_zip_source, (str, bytes, os.PathLike)):
        if not os.path.exists(old_zip_source):
            raise FileNotFoundError(f"File zip g\u1ed1c kh\xf4ng t\u1ed3n t\u1ea1i: {old_zip_source}")
        def _open_old():
            return zipfile.ZipFile(old_zip_source, 'r')
    else:
        # BytesIO \u2014 seek v\u1ec1 \u0111\u1ea7u tr\u01b0\u1edbc khi \u0111\u1ecdc
        def _open_old():
            old_zip_source.seek(0)
            return zipfile.ZipFile(old_zip_source, 'r')

    # Build set c\xe1c file \u0111\u00e3 \u0111\u01b0\u1ee3c extract ra folder_path (\u01b0u ti\xean cao)
    updated_files = set()
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            abs_path = os.path.join(root, file)
            rel_path = os.path.relpath(abs_path, folder_path)
            updated_files.add(rel_path.replace(os.sep, '/'))

    # D\xf9ng BytesIO l\u00e0m buffer trung gian (kh\xf4ng ghi ra \u0111\u0129a th\xeam l\u1ea7n n\u1eefa)
    zip_buf = io.BytesIO()

    with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED, allowZip64=True) as new_zip:
        # 1. Ghi c\xe1c file \u0111\u00e3 ch\u1ec9nh s\u1eeda t\u1eeb folder_path
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, folder_path)
                new_zip.write(abs_path, rel_path)

        # 2. Copy c\xe1c file kh\xf4ng thay \u0111\u1ed5i t\u1eeb zip c\u0169 (streaming \u2014 ti\u1ebft ki\u1ec7m RAM)
        with _open_old() as old_zip:
            for item in old_zip.infolist():
                if (item.filename in updated_files
                        or item.filename in deleted_files
                        or item.filename.endswith('/')):
                    continue
                with old_zip.open(item) as src, new_zip.open(item, 'w') as dst:
                    shutil.copyfileobj(src, dst, _CHUNK)

    # M\u00e3 ho\u00e1 zip_buf \u2192 output_file
    zip_buf.seek(0)
    with open(output_file, 'wb') as fout:
        _stream_encrypt(zip_buf, fout, password)

