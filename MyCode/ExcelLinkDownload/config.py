# config.py
import os

APP_NAME = "Excel Link Downloader"
APP_VERSION = "1.0"

# Default settings
DEFAULT_SAVE_FOLDER = os.path.join(os.path.expanduser("~"), "Downloads")
LOG_FILENAME = "download_log.json"

# File size thresholds (MB)
MAX_FILE_SIZE_MB = 500

# Supported file extensions (for display)
SUPPORTED_EXTENSIONS = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.zip', '.rar', '.jpg', '.png', '.txt']