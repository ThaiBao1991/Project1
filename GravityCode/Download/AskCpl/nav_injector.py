"""
nav_injector.py
Inject thanh điều hướng cố định (fixed nav bar) vào các file day_X.html.
- Nút ◀ ▶ để qua lại Day
- Dropdown Mục Lục ±10 ngày
- Dính đầu trang (position: fixed)
- Phím tắt: ← → trên bàn phím
- Hoạt động offline (không cần server)
"""

import os
import re

NAV_MARKER = "<!-- NAV-BAR-V2 -->"
NAV_END_MARKER = "<!-- END-NAV-BAR-V2 -->"


def build_nav_html(current_day: int, day_map: dict, total_days: int, file_map: dict = None) -> str:
    """
    Tạo HTML cho thanh điều hướng.
    day_map: { day_num: title_string } cho ±10 ngày xung quanh current_day
    file_map: { day_num: filename } cho toàn bộ các ngày (để render link Prev/Next)
    """
    import json
    toc_items_html = ""
    for d in sorted(day_map.keys()):
        title = day_map[d]
        css_class = "nav-toc-item nav-toc-current" if d == current_day else "nav-toc-item"
        marker = " \u2190" if d == current_day else ""
        safe_title = title.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
        filename = file_map.get(d, f"day_{d}.html") if file_map else f"day_{d}.html"
        toc_items_html += f'<a class="{css_class}" href="{filename}">Day {d} \u2014 {safe_title}{marker}</a>\n'

    prev_disabled = 'disabled' if current_day <= 1 else ''
    next_disabled = ''

    nav_html = f"""
{NAV_MARKER}
<style>
#askcpl-nav {{
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
  color: #fff;
  padding: 8px 16px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.5);
  font-family: 'Segoe UI', Arial, sans-serif;
  font-size: 14px;
  box-sizing: border-box;
  height: 48px;
}}
#askcpl-nav button {{
  background: rgba(255,255,255,0.15);
  border: 1px solid rgba(255,255,255,0.3);
  color: #fff;
  padding: 6px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 16px;
  transition: background 0.2s;
  flex-shrink: 0;
}}
#askcpl-nav button:hover:not([disabled]) {{
  background: rgba(255,255,255,0.3);
}}
#askcpl-nav button[disabled] {{
  opacity: 0.3;
  cursor: default;
}}
#askcpl-nav-title {{
  flex: 1;
  text-align: center;
  cursor: pointer;
  padding: 4px 12px;
  border-radius: 6px;
  transition: background 0.2s;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-weight: 600;
  letter-spacing: 0.3px;
  color: #e0d0ff;
}}
#askcpl-nav-title:hover {{
  background: rgba(255,255,255,0.15);
}}
#askcpl-toc {{
  display: none;
  position: fixed;
  top: 52px;
  left: 50%;
  transform: translateX(-50%);
  background: #1e1e2e;
  border: 1px solid rgba(167,139,250,0.3);
  border-radius: 10px;
  padding: 8px 4px;
  min-width: 340px;
  max-height: 420px;
  overflow-y: auto;
  z-index: 9998;
  box-shadow: 0 8px 32px rgba(0,0,0,0.7);
}}
#askcpl-toc::-webkit-scrollbar {{ width: 6px; }}
#askcpl-toc::-webkit-scrollbar-track {{ background: transparent; }}
#askcpl-toc::-webkit-scrollbar-thumb {{ background: rgba(167,139,250,0.3); border-radius: 3px; }}
.nav-toc-item {{
  display: block;
  padding: 7px 16px;
  color: #a0a0c0;
  text-decoration: none;
  border-radius: 6px;
  margin: 1px 4px;
  font-size: 13px;
  transition: background 0.15s, color 0.15s;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}}
.nav-toc-item:hover {{
  background: rgba(167,139,250,0.15);
  color: #e0d0ff;
}}
.nav-toc-current {{
  background: linear-gradient(90deg, #7c3aed, #4f46e5) !important;
  color: #fff !important;
  font-weight: bold;
}}
#askcpl-nav-home {{
  background: rgba(46,160,67,0.3);
  text-decoration: none;
  border: 1px solid rgba(46,160,67,0.5);
  color: #fff;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 14px;
  transition: background 0.2s;
  display: flex;
  align-items: center;
}}
#askcpl-nav-home:hover {{ background: rgba(46,160,67,0.5); }}
body {{ padding-top: 52px !important; }}
</style>

<div id="askcpl-nav">
  <button id="nav-prev" onclick="askcplNav(-1)" {prev_disabled}>&#9664; Prev</button>
  <a id="askcpl-nav-home" href="index.html#day-{current_day}" title="Quay lại danh sách tổng">🏠 Menu</a>
  <span id="askcpl-nav-title" onclick="askcplToggleToc()" title="Click xem Mục Lục">
    Day {current_day} / {total_days} &nbsp;&#9660;
  </span>
  <button id="nav-next" onclick="askcplNav(1)" {next_disabled}>Next &#9654;</button>
</div>

<div id="askcpl-toc">
{toc_items_html}
</div>

<script>
(function() {{
  var CURRENT_DAY = {current_day};
  var TOTAL_DAYS = {total_days};
  var FILE_MAP = {json.dumps(file_map) if file_map else "{}"};
  var tocOpen = false;

  function showToast(msg) {{
    var t = document.getElementById('askcpl-toast');
    if (!t) {{
      t = document.createElement('div');
      t.id = 'askcpl-toast';
      t.style.cssText = 'position:fixed;bottom:28px;left:50%;transform:translateX(-50%);background:linear-gradient(135deg,#1e1b4b,#312e81);color:#e0e7ff;padding:12px 24px;border-radius:8px;border:1px solid #6366f1;box-shadow:0 10px 25px rgba(0,0,0,0.6);font-size:14px;font-family:sans-serif;z-index:999999;transition:opacity 0.3s;text-align:center;';
      document.body.appendChild(t);
    }}
    t.innerHTML = msg;
    t.style.opacity = '1';
    clearTimeout(t._timer);
    t._timer = setTimeout(function(){{ t.style.opacity = '0'; }}, 3500);
  }}

  var _lastNextAttempt = 0;
  window.askcplNav = function(delta) {{
    var next = CURRENT_DAY + delta;
    if (next < 1) return;
    if (FILE_MAP[next]) {{
        window.location.href = FILE_MAP[next];
    }} else if (delta > 0) {{
        var now = Date.now();
        var candidate = 'day_' + next + '.html';
        if (now - _lastNextAttempt < 4000) {{
          window.location.href = candidate;
        }} else {{
          _lastNextAttempt = now;
          showToast('⏳ Day ' + next + ' chưa có trong mục lục. Bấm Next lần nữa để thử mở trực tiếp ' + candidate);
        }}
    }}
  }};

  window.askcplToggleToc = function() {{
    var toc = document.getElementById('askcpl-toc');
    tocOpen = !tocOpen;
    toc.style.display = tocOpen ? 'block' : 'none';
    if (tocOpen) {{
      var cur = toc.querySelector('.nav-toc-current');
      if (cur) cur.scrollIntoView({{block: 'center'}});
    }}
  }};

  document.addEventListener('click', function(e) {{
    var nav = document.getElementById('askcpl-nav');
    var toc = document.getElementById('askcpl-toc');
    if (toc && !nav.contains(e.target) && !toc.contains(e.target)) {{
      toc.style.display = 'none';
      tocOpen = false;
    }}
  }});

  document.addEventListener('keydown', function(e) {{
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
    if (e.key === 'ArrowLeft') askcplNav(-1);
    if (e.key === 'ArrowRight') askcplNav(1);
    if (e.key === 'Escape') {{
      document.getElementById('askcpl-toc').style.display = 'none';
      tocOpen = false;
    }}
  }});
}})();
</script>
{NAV_END_MARKER}"""
    return nav_html


def get_day_files(folder: str) -> list:
    """Trả về list (day_num, filename) được sắp xếp, hỗ trợ cả định dạng cũ và mới (Addon)."""
    result = []
    for f in os.listdir(folder):
        fl = f.lower()
        if not fl.endswith('.html') or fl == 'index.html' or ' exercise' in fl:
            continue
            
        # Thử định dạng mới từ Addon: 001_Day 1...
        m1 = re.match(r'^(\d+)_day', fl)
        if m1:
            result.append((int(m1.group(1)), f))
            continue
            
        # Thử định dạng cũ: day_1.html, day_1b.html
        m2 = re.search(r'day_(\d+)', fl)
        if m2:
            result.append((int(m2.group(1)), f))
            
    # Sắp xếp theo số ngày, nếu trùng số (vd: day_1, day_1b) thì xếp theo bảng chữ cái
    result.sort(key=lambda x: (x[0], x[1]))
    return result


def get_day_title(filepath: str, day_num: int) -> str:
    """Lấy tiêu đề ngắn từ <title> hoặc <h1>."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        m = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
        if m:
            title = m.group(1).strip()
            title = re.sub(r'^Day\s+\d+\s*[\u2014\-]\s*', '', title).strip()
            if title:
                return title
        m = re.search(r'<h1[^>]*>([\s\S]*?)</h1>', content, re.IGNORECASE)
        if m:
            raw = re.sub(r'<[^>]+>', '', m.group(1)).strip()
            raw = re.sub(r'^Day\s+\d+\s*[\u2014\-]\s*', '', raw).strip()
            if raw:
                return raw
    except Exception:
        pass
    return f"Day {day_num}"


def remove_old_nav(content: str) -> str:
    """Xóa nav bar cũ (v2 và v1 legacy)."""
    pattern = re.compile(
        re.escape(NAV_MARKER) + r'[\s\S]*?' + re.escape(NAV_END_MARKER),
        re.DOTALL
    )
    content = pattern.sub('', content)
    pattern_v1 = re.compile(
        r'<!-- NAV BAR[^>]*-->[\s\S]*?<!-- END NAV BAR[^>]*-->',
        re.DOTALL | re.IGNORECASE
    )
    content = pattern_v1.sub('', content)
    return content


def inject_nav_into_file(filepath: str, current_day: int, day_map: dict, total_days: int, file_map: dict = None) -> bool:
    """Inject nav bar vào 1 file HTML. Trả về True nếu thành công."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        content = remove_old_nav(content)
        nav_html = build_nav_html(current_day, day_map, total_days, file_map)
        if '</body>' in content.lower():
            insert_pos = content.lower().rfind('</body>')
            content = content[:insert_pos] + nav_html + '\n' + content[insert_pos:]
        else:
            content += nav_html
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error: {filepath}: {e}")
        return False


def inject_all(folder: str, log_callback=None) -> dict:
    """Inject nav vào tất cả day_X.html trong folder."""
    def log(msg):
        if log_callback:
            log_callback(msg)
        else:
            print(msg)

    day_files = get_day_files(folder)
    if not day_files:
        log("[X] Khong tim thay file day_X.html nao!")
        return {"success": 0, "failed": 0, "missing": []}

    total_days = day_files[-1][0]
    log(f"[OK] Tim thay {len(day_files)} file | Day 1 -> Day {total_days}")

    all_found = {d for d, _ in day_files}
    missing = [d for d in range(1, total_days + 1) if d not in all_found]
    if missing:
        log(f"[!] File bi thieu: Day {', '.join(map(str, missing[:10]))}{'...' if len(missing) > 10 else ''}")

    log("[*] Dang doc tieu de cac ngay...")
    full_title_map = {}
    full_file_map = {}
    for day_num, fname in day_files:
        full_title_map[day_num] = get_day_title(os.path.join(folder, fname), day_num)
        full_file_map[day_num] = fname

    success_count = 0
    failed_count = 0
    for day_num, fname in day_files:
        fpath = os.path.join(folder, fname)
        lo = max(1, day_num - 10)
        hi = min(total_days, day_num + 10)
        day_map = {d: full_title_map[d] for d in range(lo, hi + 1) if d in full_title_map}
        if day_num not in day_map:
            day_map[day_num] = f"Day {day_num}"
        ok = inject_nav_into_file(fpath, day_num, day_map, total_days, full_file_map)
        if ok:
            success_count += 1
        else:
            failed_count += 1

    log(f"[OK] Inject thanh cong: {success_count} file")
    if failed_count:
        log(f"[X] That bai: {failed_count} file")
    return {"success": success_count, "failed": failed_count, "missing": missing}


def rebuild_index(folder: str, log_callback=None) -> bool:
    """Tái tạo index.html với danh sách tất cả Day files."""
    def log(msg):
        if log_callback:
            log_callback(msg)
        else:
            print(msg)

    day_files = get_day_files(folder)
    if not day_files:
        log("\u274c Kh\u00f4ng c\u00f3 file n\u00e0o \u0111\u1ec3 t\u1ea1o index!")
        return False

    folder_name = os.path.basename(folder)
    title_map = {}
    for day_num, fname in day_files:
        title_map[day_num] = get_day_title(os.path.join(folder, fname), day_num)

    items_html = ""
    for day_num, fname in day_files:
        title = title_map.get(day_num, f"Day {day_num}")
        safe_title = title.replace('<', '&lt;').replace('>', '&gt;')
        items_html += (
            f'    <a class="day-item" id="day-{day_num}" href="{fname}">\n'
            f'      <span class="day-num">Day {day_num}</span>\n'
            f'      <span class="day-title">{safe_title}</span>\n'
            f'    </a>\n'
        )

    index_html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>&#128218; {folder_name} &#8212; M&#7909;c L&#7909;c</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #0f0c29; color: #e0e0f0; min-height: 100vh; }}
    .header {{ background: linear-gradient(135deg, #1a1a3e, #2d2b55); padding: 32px 24px; text-align: center; border-bottom: 1px solid rgba(255,255,255,0.1); }}
    .header h1 {{ font-size: 2em; color: #a78bfa; margin-bottom: 8px; }}
    .header p {{ color: #9090b0; font-size: 0.95em; }}
    .container {{ max-width: 820px; margin: 0 auto; padding: 24px 16px; }}
    .stats {{ background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 10px; padding: 12px 20px; margin-bottom: 20px; display: flex; gap: 24px; flex-wrap: wrap; }}
    .stats span {{ color: #a0a0c0; font-size: 0.9em; }}
    .stats b {{ color: #a78bfa; }}
    .search-box {{ width: 100%; padding: 10px 16px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.2); background: rgba(255,255,255,0.08); color: #e0e0f0; font-size: 14px; margin-bottom: 16px; outline: none; transition: border-color 0.2s; }}
    .search-box:focus {{ border-color: rgba(167,139,250,0.6); }}
    .search-box::placeholder {{ color: #7070a0; }}
    .day-list {{ display: flex; flex-direction: column; gap: 4px; }}
    .day-item {{ display: flex; align-items: center; gap: 12px; padding: 10px 16px; border-radius: 8px; text-decoration: none; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.07); transition: all 0.18s; }}
    .day-item:hover {{ background: rgba(167,139,250,0.15); border-color: rgba(167,139,250,0.4); transform: translateX(4px); }}
    .day-num {{ font-size: 0.8em; font-weight: bold; color: #a78bfa; min-width: 64px; flex-shrink: 0; }}
    .day-title {{ color: #c0c0e0; font-size: 0.93em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
    .footer {{ text-align: center; padding: 24px; color: #5050a0; font-size: 0.8em; margin-top: 16px; }}
  </style>
</head>
<body>
  <div class="header">
    <h1>&#128218; {folder_name}</h1>
    <p>T&#7893;ng c&#7897;ng {len(day_files)} ng&#224;y h&#7885;c</p>
  </div>
  <div class="container">
    <div class="stats">
      <span>T&#7893;ng s&#7889; ng&#224;y: <b>{len(day_files)}</b></span>
      <span>Day &#273;&#7847;u: <b>Day {day_files[0][0]}</b></span>
      <span>Day cu&#7889;i: <b>Day {day_files[-1][0]}</b></span>
    </div>
    <input class="search-box" type="text" id="searchInput"
           placeholder="Tim kiem Day hoac tieu de..." oninput="filterDays()">
    <div class="day-list" id="dayList">
{items_html}
    </div>
  </div>
  <div class="footer">Duoc tao tu dong boi AskCpl Config Index</div>
  <script>
    function filterDays() {{
      var q = document.getElementById('searchInput').value.toLowerCase();
      document.querySelectorAll('.day-item').forEach(function(item) {{
        item.style.display = item.textContent.toLowerCase().includes(q) ? 'flex' : 'none';
      }});
    }}
  </script>
</body>
</html>"""

    index_path = os.path.join(folder, 'index.html')
    try:
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_html)
        log(f"[OK] Da tai tao index.html ({len(day_files)} ngay)")
        return True
    except Exception as e:
        log(f"[X] Loi tao index.html: {e}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# INTEGRITY CHECK
# ─────────────────────────────────────────────────────────────────────────────
MIN_FILE_BYTES = 500   # File nhỏ hơn mức này bị coi là rỗng/lỗi
# Regex nhận cả hai định dạng tên file
_FILENAME_REGEX = re.compile(
    r'(?:^|[/\\])(\d+)_.*\.html$|[/\\]day_(\d+)[a-z]?\.html$',
    re.IGNORECASE
)


def check_integrity(folder: str, log_callback=None) -> dict:
    """
    Kiểm tra toàn vẹn thư mục roadmap HTML.

    Trả về dict:
    {
        "total_files": int,
        "missing_days": [int, ...],
        "no_nav": [(day_num, fname), ...],    # chưa có nav bar
        "bad_regex": [(day_num, fname), ...], # nav đã inject nhưng regex cũ sẽ sai
        "tiny_files": [(day_num, fname), ...],# file < MIN_FILE_BYTES bytes
        "index_ok": bool,
        "score": int,   # 0-100
        "items": [      # chi tiết từng file để hiển thị trong listbox
            {"day": int, "fname": str, "status": "ok"|"no_nav"|"bad_regex"|"tiny", "size": int}
        ]
    }
    """
    def log(msg):
        if log_callback:
            log_callback(msg)

    log("[Integrity] Bắt đầu kiểm tra...")
    day_files = get_day_files(folder)
    if not day_files:
        log("[Integrity] Không tìm thấy file nào!")
        return {
            "total_files": 0, "missing_days": [], "no_nav": [],
            "bad_regex": [], "tiny_files": [], "index_ok": False,
            "score": 0, "items": []
        }

    total = day_files[-1][0]
    found_days = {d for d, _ in day_files}
    missing_days = [d for d in range(1, total + 1) if d not in found_days]

    no_nav = []
    bad_regex = []
    tiny_files = []
    items = []

    for day_num, fname in day_files:
        fpath = os.path.join(folder, fname)
        size = 0
        has_nav = False
        regex_ok = False
        try:
            size = os.path.getsize(fpath)
            if size < MIN_FILE_BYTES:
                tiny_files.append((day_num, fname))
                status = "tiny"
            else:
                with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                    snippet = f.read(4096)
                has_nav = NAV_MARKER in snippet

                if not has_nav:
                    no_nav.append((day_num, fname))
                    status = "no_nav"
                else:
                    # Kiểm tra regex có match tên file không
                    # Bỏ qua đường dẫn thư mục, chỉ dùng tên file
                    test_path = "/" + fname
                    regex_ok = bool(_FILENAME_REGEX.search(test_path))
                    if not regex_ok:
                        bad_regex.append((day_num, fname))
                        status = "bad_regex"
                    else:
                        status = "ok"
        except Exception as ex:
            log(f"[Integrity] Lỗi đọc {fname}: {ex}")
            status = "tiny"
            tiny_files.append((day_num, fname))

        items.append({"day": day_num, "fname": fname, "status": status, "size": size})

    # Kiểm tra index.html
    index_path = os.path.join(folder, 'index.html')
    index_ok = os.path.exists(index_path) and os.path.getsize(index_path) > 200

    # Tính điểm toàn vẹn (0-100)
    total_files = len(day_files)
    problem_count = len(no_nav) + len(bad_regex) + len(tiny_files) + len(missing_days)
    denominator = total_files + len(missing_days)
    score = max(0, round(100 * (1 - problem_count / max(denominator, 1))))
    if not index_ok:
        score = max(0, score - 5)

    log(f"[Integrity] Tổng: {total_files} file | Thiếu: {len(missing_days)} | "
        f"Chưa nav: {len(no_nav)} | Nav lỗi regex: {len(bad_regex)} | "
        f"File rỗng: {len(tiny_files)} | Điểm: {score}/100")

    return {
        "total_files": total_files,
        "missing_days": missing_days,
        "no_nav": no_nav,
        "bad_regex": bad_regex,
        "tiny_files": tiny_files,
        "index_ok": index_ok,
        "score": score,
        "items": items,
    }

