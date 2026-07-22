# models.py
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class FileInfo:
    """Thông tin một file cần tải hoặc đã tải"""
    sheet: str
    row: int
    title: str
    old_link: str
    new_link: Optional[str] = None
    size_mb: Optional[float] = None
    modified_date: Optional[str] = None
    status: str = "pending"  # pending, downloaded, skipped, failed

    def to_dict(self):
        return {
            "sheet": self.sheet,
            "row": self.row,
            "title": self.title,
            "old_link": self.old_link,
            "new_link": self.new_link,
            "size_mb": self.size_mb,
            "modified_date": self.modified_date,
            "status": self.status
        }

    @staticmethod
    def from_dict(data: dict):
        return FileInfo(
            sheet=data.get("sheet", ""),
            row=data.get("row", 0),
            title=data.get("title", ""),
            old_link=data.get("old_link", ""),
            new_link=data.get("new_link"),
            size_mb=data.get("size_mb"),
            modified_date=data.get("modified_date"),
            status=data.get("status", "pending")
        )


@dataclass
class DownloadLog:
    """File log tổng thể"""
    source_excel: str
    save_folder: str
    data_column: str
    title_column: str
    files: list  # List of FileInfo
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self):
        return {
            "source_excel": self.source_excel,
            "save_folder": self.save_folder,
            "data_column": self.data_column,
            "title_column": self.title_column,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "files": [f.to_dict() for f in self.files]
        }

    @staticmethod
    def from_dict(data: dict):
        files = [FileInfo.from_dict(f) for f in data.get("files", [])]
        return DownloadLog(
            source_excel=data.get("source_excel", ""),
            save_folder=data.get("save_folder", ""),
            data_column=data.get("data_column", ""),
            title_column=data.get("title_column", ""),
            files=files,
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", "")
        )