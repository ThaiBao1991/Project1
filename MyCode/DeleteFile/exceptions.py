"""
Định nghĩa các exception tùy chỉnh cho ứng dụng
"""

class FileDeleterError(Exception):
    """Base exception cho ứng dụng"""
    pass

class ConfigError(FileDeleterError):
    """Lỗi liên quan đến cấu hình"""
    pass

class InvalidPathError(FileDeleterError):
    """Lỗi đường dẫn không hợp lệ"""
    pass

class AccessDeniedError(FileDeleterError):
    """Lỗi không có quyền truy cập"""
    pass