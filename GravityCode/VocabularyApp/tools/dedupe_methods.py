"""
tools/dedupe_methods.py — AST quét method BỊ ĐỊNH NGHĨA 2 LẦN trong cùng 1 class.

Python: def SAU đè def TRƯỚC ⇒ bản đầu thành code CHẾT (bị che khuất) — hay gây
bug "sửa mãi không ăn": người ta sửa bản đầu trong khi Python chạy bản sau.

Mặc định chỉ LIỆT KÊ (an toàn); `--apply` XÓA các bản bị che (bản đầu), có
backup `.bak-<ts>` + ghi atomic.

Cú pháp:
  python tools/dedupe_methods.py
  python tools/dedupe_methods.py --apply
  python tools/dedupe_methods.py --file ai/other_file.py --apply
"""
import argparse
import ast
import os
import shutil
import sys
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def _def_start(node):
    """Dòng bắt đầu gồm decorator (decorator đứng TRÊN dòng def)."""
    if getattr(node, "decorator_list", None):
        return min(d.lineno for d in node.decorator_list)
    return node.lineno


def scan_dupes(path: str) -> list:
    """Trả list_shadowed: (class_name, method_name, start, end, second_start).

    (start, end) là khoảng CẦN XÓA (bản đầu, gồm decorator). Bản SAU giữ nguyên.
    """
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()
    tree = ast.parse(src)
    out = []
    for cls in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
        defs_by_name = {}
        for fn in cls.body:
            if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                defs_by_name.setdefault(fn.name, []).append(fn)
        for name, defs in defs_by_name.items():
            if len(defs) < 2:
                continue
            # mọi bản TRƯỚC bản cuối đều bị che → xóa đủ
            keep = defs[-1]
            for d in defs[:-1]:
                out.append((cls.name, name, _def_start(d), d.end_lineno,
                            keep.lineno))
    return out


def _trim_blanks(lines, start0, end0):
    """Nới end0 (index 0-based, EXCLUSIVE) ăn cả các dòng RỖNG ngay sau khối."""
    while end0 < len(lines) and lines[end0].strip() == "":
        end0 += 1
    return end0


def _fmt_range(lines, start, end):
    return f"dòng {start}–{end} ({end - start + 1} dòng)"


def apply_fixes(path: str, dupes: list, dry_run: bool = True) -> str:
    """Xóa các khoảng (start, end) bị che; trả mô tả."""
    if not dupes:
        return "✔ Không có method trùng cần xử lý."
    with open(path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines(keepends=True)
    # (start, end) 1-based TRÊN DÒNG; xoá từ CUỐI lên để index các khoảng trước đứng yên
    ranges = sorted({(d[2], d[3]) for d in dupes}, reverse=True)
    report = [f"  ⛔ Xóa {_fmt_range(lines, s, e)}" for s, e in ranges]
    if dry_run:
        return "\n".join(report) + "\n[dry-run — chưa ghi]"
    bak = f"{path}.bak-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    shutil.copy2(path, bak)
    for s, e in ranges:
        e0 = _trim_blanks(lines, s - 1, e)     # 0-based exclusive
        del lines[s - 1:e0]
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        f.writelines(lines)
    os.replace(tmp, path)
    return "\n".join(report) + f"\n[APPLIED — backup: {bak}]"


def main():
    ap = argparse.ArgumentParser(prog="dedupe_methods")
    ap.add_argument("--file", default="VocabApp.py", help="File cần quét (rel về gốc app)")
    ap.add_argument("--apply", action="store_true", help="Xóa bản bị che (mặc định: chỉ liệt kê)")
    ap.add_argument("--focus", default=None,
                    help="Chỉ hiển thị method của class chứa chuỗi này (VD: StudyTab)")
    args = ap.parse_args()

    path = args.file if os.path.isabs(args.file) else os.path.join(BASE, args.file)
    if not os.path.isfile(path):
        print(f"⛔ Không thấy file: {path}")
        return 1

    dupes = scan_dupes(path)
    if args.focus:
        dupes = [d for d in dupes if d[0] == args.focus]
    if not dupes:
        print(f"✔ {args.file}: không có method nào bị định nghĩa 2 lần trong cùng class.")
        return 0

    print(f"⚠ {len(dupes)} method TRÙNG trong {args.file} (bản đầu bị che, code chết):")
    for cls, name, start, end, second in dupes:
        print(f"  • {cls}.{name}: chết dòng {start}–{end} · đang chạy bản dòng {second}+")
    print()
    print(apply_fixes(path, dupes, dry_run=not args.apply))
    return 0


if __name__ == "__main__":
    sys.exit(main())
