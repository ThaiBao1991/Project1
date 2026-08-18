"""
quota_db.py — SQLite Database ri\u00eang cho Quota Tracker.

- L\u01b0u tr\u1eef quota data + group status theo t\u1eebng email.
- Email v\u00e0 d\u1eef li\u1ec7u nh\u1ea1y c\u1ea3m \u0111\u01b0\u1ee3c XOR-obfuscate + base64 \u0111\u1ec3 push GitHub kh\u00f4ng l\u1ed9.
- \u0110\u1ed3ng b\u1ed9 2 chi\u1ec1u v\u1edbi quota_data.dat.

Usage:
    from quota_db import merge_and_sync, get_db_path, read_accounts
    db_path = get_db_path('/path/to/quota_data.dat')
    merged = merge_and_sync(dat_data, db_path)
"""

import sqlite3
import json
import os
import base64
from pathlib import Path

# --- XOR Obfuscation (kh\u00f4ng ph\u1ea3i b\u1ea3o m\u1eadt t\u1ed1t, ch\u1ec9 obfuscate \u0111\u1ec3 push GitHub) ---
_KEY = b'QuotaAntiGravity_Tracker_2026_Secure'


def _xor(data: bytes, key: bytes = _KEY) -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def _enc(s: str) -> str:
    """String \u2192 XOR \u2192 base64 (safe ASCII)."""
    if not s:
        return ''
    return base64.b64encode(_xor(s.encode('utf-8'))).decode('ascii')


def _dec(s: str) -> str:
    """base64 \u2192 XOR \u2192 string. Return s as-is if decode fails."""
    if not s:
        return ''
    try:
        return _xor(base64.b64decode(s.encode('ascii'))).decode('utf-8')
    except Exception:
        return s


# --- DB Path ---
def get_db_path(dat_path: str) -> str:
    """Return SQLite path in same folder as quota_data.dat."""
    return str(Path(dat_path).parent / 'quota_db.sqlite3')


# --- Schema ---
_SCHEMA = [
    '''CREATE TABLE IF NOT EXISTS accounts (
        email_enc   TEXT PRIMARY KEY,
        exhausted_until INTEGER DEFAULT 0,
        overall_reset   INTEGER DEFAULT 0,
        last_update     INTEGER DEFAULT 0,
        source          TEXT DEFAULT '',
        added_at        INTEGER DEFAULT 0
    )''',
    '''CREATE TABLE IF NOT EXISTS group_status (
        email_enc  TEXT,
        grp        TEXT,
        exhausted  INTEGER DEFAULT 0,
        reset_time INTEGER DEFAULT 0,
        percent    INTEGER DEFAULT 100,
        PRIMARY KEY (email_enc, grp)
    )''',
    '''CREATE TABLE IF NOT EXISTS available_groups (
        email_enc TEXT,
        grp       TEXT,
        PRIMARY KEY (email_enc, grp)
    )''',
]


def _get_conn(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str):
    """Create tables if not exist."""
    conn = _get_conn(db_path)
    for stmt in _SCHEMA:
        conn.execute(stmt)
    conn.commit()
    conn.close()


# --- Write ---
def write_accounts(db_path: str, quota_data: dict):
    """Write entire quota_data dict \u2192 SQLite (emails obfuscated)."""
    init_db(db_path)
    conn = _get_conn(db_path)
    c = conn.cursor()

    for email, info in quota_data.items():
        if not email:
            continue
        enc = _enc(email)

        c.execute('''INSERT OR REPLACE INTO accounts
            (email_enc, exhausted_until, overall_reset, last_update, source, added_at)
            VALUES (?,?,?,?,?,?)''', (
            enc,
            int(info.get('exhaustedUntil') or 0),
            int(info.get('overallResetTime') or 0),
            int(info.get('lastUpdate') or 0),
            info.get('source', ''),
            int(info.get('addedAt') or 0),
        ))

        # group_status
        gs = info.get('groupStatus') or {}
        for grp, g in gs.items():
            c.execute('''INSERT OR REPLACE INTO group_status
                (email_enc, grp, exhausted, reset_time, percent) VALUES (?,?,?,?,?)''', (
                enc, grp,
                1 if g.get('exhausted') else 0,
                int(g.get('resetTime') or 0),
                int(g.get('percent') or 0),
            ))

        # available_groups
        c.execute('DELETE FROM available_groups WHERE email_enc=?', (enc,))
        for grp in (info.get('availableGroups') or []):
            c.execute('INSERT OR IGNORE INTO available_groups VALUES (?,?)', (enc, grp))

    conn.commit()
    conn.close()


# --- Read ---
def read_accounts(db_path: str) -> dict:
    """Read SQLite \u2192 quota_data dict (emails decrypted)."""
    if not os.path.exists(db_path):
        return {}

    conn = _get_conn(db_path)
    c = conn.cursor()
    result = {}

    c.execute('SELECT * FROM accounts')
    for row in c.fetchall():
        email = _dec(row['email_enc'])
        if not email:
            continue

        entry = {
            'exhaustedUntil':  row['exhausted_until'],
            'overallResetTime': row['overall_reset'],
            'lastUpdate':       row['last_update'],
            'source':           row['source'] or 'db',
            'addedAt':          row['added_at'],
            'groupStatus':      {},
            'availableGroups':  [],
            'exhaustedGroups':  [],
        }

        c2 = conn.cursor()
        c2.execute('SELECT * FROM group_status WHERE email_enc=?', (row['email_enc'],))
        for gs in c2.fetchall():
            entry['groupStatus'][gs['grp']] = {
                'exhausted': bool(gs['exhausted']),
                'resetTime': gs['reset_time'],
                'percent':   gs['percent'],
            }

        c2.execute('SELECT grp FROM available_groups WHERE email_enc=?', (row['email_enc'],))
        entry['availableGroups'] = [r['grp'] for r in c2.fetchall()]
        entry['exhaustedGroups'] = [g for g, s in entry['groupStatus'].items() if s['exhausted']]

        result[email] = entry

    conn.close()
    return result


# --- Merge ---
def merge_and_sync(dat_data: dict, db_path: str) -> dict:
    """
    2-way merge gi\u1eefa dat_data v\u00e0 SQLite DB:
    - Email trong dat ch\u01b0a c\u00f3 trong DB \u2192 ghi v\u00e0o DB.
    - Email trong DB ch\u01b0a c\u00f3 trong dat \u2192 th\u00eam v\u00e0o dat.
    - Khi c\u1ea3 2 \u0111\u1ec1u c\u00f3: gi\u1eef b\u1ea3n m\u1edbi h\u01a1n (theo lastUpdate).
    Returns merged dict \u0111\u00e3 \u0111\u01b0\u1ee3c ghi l\u1ea1i v\u00e0o DB.
    """
    db_data = read_accounts(db_path)
    merged = dict(db_data)

    for email, info in dat_data.items():
        if email not in merged:
            merged[email] = info
        else:
            dat_ts = int(info.get('lastUpdate') or 0)
            db_ts  = int(merged[email].get('lastUpdate') or 0)
            if dat_ts >= db_ts:
                merged[email] = info
    if merged != db_data or not os.path.exists(db_path):
        write_accounts(db_path, merged)
    return merged


# ════════════════════════════════════════════════════════════════════════════
#  GUI — chạy trực tiếp: python quota_db.py
# ════════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    import sys
    import time
    import json
    import threading
    import subprocess
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox

    # ── Màu sắc (dark theme) ──────────────────────────────────────────────
    BG      = '#13131f'
    BG2     = '#1a1a2e'
    BG3     = '#20203a'
    CARD    = '#1e1e35'
    ACCENT  = '#7c6eff'
    GREEN   = '#50fa7b'
    RED     = '#ff5555'
    YELLOW  = '#ffb86c'
    PINK    = '#ff79c6'
    TEXT    = '#e2e8f0'
    SUBTEXT = '#7f8eaa'
    BORDER  = '#2d2d4a'

    # ── Helpers dữ liệu ──────────────────────────────────────────────────
    SCRIPT_DIR = Path(__file__).parent

    def _cfg_path():
        return SCRIPT_DIR / 'quota_db_gui.json'

    def _find_dat():
        cfg = _cfg_path()
        if cfg.exists():
            try:
                c = json.loads(cfg.read_text('utf-8'))
                p = c.get('dat_path', '')
                if p and os.path.exists(p):
                    return p
            except Exception:
                pass
        # Fallback: thư mục cha
        p = SCRIPT_DIR.parent / 'quota_data.dat'
        return str(p) if p.exists() else None

    def _save_cfg(dat_path):
        _cfg_path().write_text(json.dumps({'dat_path': dat_path}, ensure_ascii=False), 'utf-8')

    def _load_dat(dat_path):
        if not dat_path or not os.path.exists(dat_path):
            return {}
        try:
            raw = open(dat_path, 'r', encoding='utf-8').read().strip()
            if not raw:
                return {}
            return json.loads(base64.b64decode(raw).decode('utf-8'))
        except Exception:
            return {}

    def _save_dat(dat_path, data):
        if not dat_path:
            return
        raw = base64.b64encode(json.dumps(data, ensure_ascii=False).encode('utf-8')).decode('ascii')
        if os.path.exists(dat_path):
            try:
                current_raw = open(dat_path, 'r', encoding='utf-8').read().strip()
                if current_raw == raw:
                    return
            except Exception:
                pass
        open(dat_path, 'w', encoding='utf-8').write(raw)

    def _find_codex_dat(dat_path):
        candidates = []
        if dat_path:
            candidates.append(Path(dat_path).parent / 'codex_quota_data.dat')
        candidates.append(Path.home() / '.quota-tracker' / 'codex_quota_data.dat')
        for candidate in candidates:
            if candidate.exists():
                return str(candidate)
        return str(candidates[0]) if candidates else None

    def _load_codex_dat(dat_path):
        data = _load_dat(dat_path)
        return data if isinstance(data, dict) else {}

    def _find_sync_script():
        up = os.environ.get('USERPROFILE', os.environ.get('HOME', ''))
        candidates = [
            SCRIPT_DIR / 'sync_antigravity.py',
            Path(up) / 'Desktop' / 'desktop' / 'work' / 'Project' / 'Python' /
                'BasicLearnPython' / 'W3schools' / 'Python Tutorial' / 'GravityCode' /
                'Download' / 'AskCpl' / 'CTApp' / 'QuotaAntigravity' / 'QuotaApp' / 'sync_antigravity.py',
            Path(up) / 'Desktop' / 'Project' / 'Python' / 'Python MyWork' /
                'Project1' / 'GravityCode' / 'Download' / 'AskCpl' / 'CTApp' /
                'QuotaAntigravity' / 'QuotaApp' / 'sync_antigravity.py',
        ]
        for c in candidates:
            if Path(c).exists():
                return str(c)
        return None

    def _find_codex_sync_script():
        candidate = SCRIPT_DIR / 'sync_codex.py'
        return str(candidate) if candidate.exists() else None

    def _format_duration(ms):
        if ms <= 0: return ""
        d = int(ms // 86_400_000)
        h = int((ms % 86_400_000) // 3_600_000)
        m = int((ms % 3_600_000) // 60_000)
        
        parts = []
        if d > 0: parts.append(f'{d}d')
        if h > 0: parts.append(f'{h}h')
        if m > 0: parts.append(f'{m}m')
        if not parts: return '0m'
        return ' '.join(parts)

    def _fmt_cd(exh_until, reset_ms=0):
        now_ms = time.time() * 1000
        parts = []

        cd_str = ""
        if exh_until and exh_until > now_ms:
            cd_str = _format_duration(exh_until - now_ms)

        rt = reset_ms or exh_until or 0
        rn_str = ""
        if rt and rt > now_ms:
            rn_str = '\u21bb ' + _format_duration(rt - now_ms)

        if cd_str and rn_str and cd_str == rn_str[2:]:
            parts.append(rn_str)
        else:
            if cd_str: parts.append(cd_str)
            if rn_str: parts.append(rn_str)

        return '  '.join(parts)

    # ── App chính ─────────────────────────────────────────────────────────
    class QuotaDBApp(tk.Tk):
        def __init__(self):
            super().__init__()
            self.title('⚡ Quota Tracker — Antigravity Account Manager')
            self.geometry('1080x600')
            try:
                self.state('zoomed')  # Phóng to toàn màn hình mặc định
            except:
                pass
            self.configure(bg=BG)
            self.minsize(720, 420)

            self._dat_path   = _find_dat()
            self._codex_path = _find_codex_dat(self._dat_path)
            self._data       = {}
            self._codex_data = {}
            self._ag_emails  = set()
            self._status_var = tk.StringVar(value='Sẵn sàng')
            self._sort_col   = 'email'
            self._sort_rev   = False

            self._build_ui()
            self._refresh()
            self._auto_poll()

        # ── Xây dựng giao diện ──────────────────────────────────────────
        def _build_ui(self):
            # Header
            hdr = tk.Frame(self, bg=BG2, height=54)
            hdr.pack(fill=tk.X)
            hdr.pack_propagate(False)
            tk.Label(hdr, text='⚡  Quota Tracker',
                     font=('Segoe UI', 15, 'bold'), bg=BG2, fg=ACCENT
                     ).pack(side=tk.LEFT, padx=16, pady=10)
            self._path_lbl = tk.Label(hdr, text=self._short_path(),
                                       font=('Segoe UI', 9), bg=BG2, fg=SUBTEXT)
            self._path_lbl.pack(side=tk.LEFT, padx=6)

            # Toolbar
            tb = tk.Frame(self, bg=BG3, height=46)
            tb.pack(fill=tk.X)
            tb.pack_propagate(False)

            def _btn(parent, text, cmd, bg=BG3, fg=TEXT, abg=ACCENT):
                b = tk.Button(parent, text=text, command=cmd, bg=bg, fg=fg,
                              font=('Segoe UI', 9, 'bold'), relief=tk.FLAT,
                              bd=0, padx=14, pady=7, activebackground=abg,
                              activeforeground='#fff', cursor='hand2')
                b.pack(side=tk.LEFT, padx=4, pady=6)
                return b

            _btn(tb, '➕  Thêm (qua Antigravity Account)', self._add, ACCENT, '#fff', '#6350ff')
            _btn(tb, '✓  Check All (Sync từ AG)',          self._check_all, '#1a4731', GREEN, '#2d7a55')
            _btn(tb, '⌁  Sync Codex',                       self._sync_codex, '#11354a', '#8be9fd', '#1f6687')
            _btn(tb, '📁  Chọn Data',                      self._choose_dat)
            _btn(tb, '🔄  Làm mới',                        self._refresh)

            self._del_btn = tk.Button(tb, text='🗑️  Xóa', command=self._delete_sel,
                                       bg='#3a1111', fg=RED, font=('Segoe UI', 9, 'bold'),
                                       relief=tk.FLAT, bd=0, padx=14, pady=7,
                                       activebackground='#5c1a1a', cursor='hand2')
            self._del_btn.pack(side=tk.RIGHT, padx=10, pady=6)

            # Bảng tài khoản
            wrap = tk.Frame(self, bg=BG)
            wrap.pack(fill=tk.BOTH, expand=True, padx=12, pady=(10, 0))

            style = ttk.Style()
            style.theme_use('clam')
            style.configure('Q.Treeview',
                            background=CARD, foreground=TEXT,
                            fieldbackground=CARD, rowheight=34,
                            font=('Segoe UI', 10))
            style.configure('Q.Treeview.Heading',
                            background=BG3, foreground=ACCENT,
                            font=('Segoe UI', 9, 'bold'), relief='flat')
            style.map('Q.Treeview',
                      background=[('selected', ACCENT)],
                      foreground=[('selected', '#fff')])

            cols = ('email', 'status', 'groups', 'cd', 'note')
            self._tv = ttk.Treeview(wrap, columns=cols, show='headings',
                                     style='Q.Treeview', selectmode='browse')
            hdrs = [('email',  'Email',         260, tk.W),
                    ('status', 'Trạng thái %',  180, tk.CENTER),
                    ('groups', 'Groups OK',     180, tk.CENTER),
                    ('cd',     'Đếm ngược',     160, tk.CENTER),
                    ('note',   'Ghi chú',       250, tk.W)]
            for col, lbl, w, anc in hdrs:
                self._tv.heading(col, text=lbl,
                                 command=lambda c=col: self._sort_by(c))
                self._tv.column(col, width=w, minwidth=w, anchor=anc,
                                stretch=(col == 'note'))

            # Row tags
            self._tv.tag_configure('ok',    background='#142b14', foreground=GREEN)
            self._tv.tag_configure('exh',   background='#2b1414', foreground=RED)
            self._tv.tag_configure('part',  background='#2b2010', foreground=YELLOW)
            self._tv.tag_configure('noag',  background='#2b1428', foreground=PINK)
            self._tv.tag_configure('nodata',background=CARD,       foreground=SUBTEXT)
            self._tv.tag_configure('codexok', background='#102b2b', foreground='#8be9fd')
            self._tv.tag_configure('codexexh',background='#2b1d14', foreground=YELLOW)

            sb_x = ttk.Scrollbar(wrap, orient=tk.HORIZONTAL, command=self._tv.xview)
            sb_y = ttk.Scrollbar(wrap, orient=tk.VERTICAL, command=self._tv.yview)
            self._tv.configure(xscrollcommand=sb_x.set, yscrollcommand=sb_y.set)
            
            sb_x.pack(side=tk.BOTTOM, fill=tk.X)
            sb_y.pack(side=tk.RIGHT, fill=tk.Y)
            self._tv.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            # Status bar
            sf = tk.Frame(self, bg=BG2, height=32)
            sf.pack(fill=tk.X, side=tk.BOTTOM)
            sf.pack_propagate(False)
            tk.Label(sf, textvariable=self._status_var,
                     font=('Segoe UI', 9), bg=BG2, fg=SUBTEXT
                     ).pack(side=tk.LEFT, padx=12, pady=6)
            self._count_lbl = tk.Label(sf, text='',
                                        font=('Segoe UI', 9), bg=BG2, fg=SUBTEXT)
            self._count_lbl.pack(side=tk.RIGHT, padx=12, pady=6)

        def _short_path(self):
            if self._dat_path:
                p = Path(self._dat_path)
                return f'📂 …\\{p.parent.name}\\{p.name}'
            return '📂 Chưa chọn file Data'

        # ── Render bảng ─────────────────────────────────────────────────
        def _refresh(self):
            self._data = _load_dat(self._dat_path)
            self._codex_path = _find_codex_dat(self._dat_path)
            self._codex_data = _load_codex_dat(self._codex_path)
            self._render()

        def _render(self):
            for r in self._tv.get_children():
                self._tv.delete(r)

            now_ms = time.time() * 1000
            rows = []
            for email, info in self._data.items():
                gs        = info.get('groupStatus') or {}
                avail     = info.get('availableGroups') or []
                exh_grps  = info.get('exhaustedGroups') or []
                last_err  = info.get('lastError', '')
                exh_until = info.get('exhaustedUntil') or 0

                # Cột Trạng thái %
                gem_pct = gs.get('gemini', {}).get('percent')
                cld_pct = gs.get('claude', {}).get('percent')
                if gem_pct is not None:
                    status = f'Gemini: {gem_pct}%'
                    if cld_pct is not None:
                        status += f'  Claude: {cld_pct}%'
                else:
                    status = '— —' if gs else 'Chưa có data'

                # Cột Groups OK
                if avail:
                    groups = ' ✓ '.join(g.capitalize() for g in avail)
                    if exh_grps:
                        groups += '  🔴 ' + ', '.join(g.capitalize() for g in exh_grps)
                else:
                    groups = '🔴 Tất cả hết' if gs else '—'

                # C\u1ed9t \u0110\u1ebfm ng\u01b0\u1ee3c + Renews (gi\u1ed1ng Antigravity Account)
                reset_ms = info.get('overallResetTime') or 0
                cd = _fmt_cd(exh_until, reset_ms) if (exh_until > now_ms or reset_ms > now_ms) else ''
                note = last_err[:60] + ('…' if len(last_err) > 60 else '') if last_err else ''

                # Tag màu
                not_in_ag = self._ag_emails and email not in self._ag_emails
                ag_err    = 'Antigravity Account' in last_err
                if not_in_ag or ag_err:
                    tag = 'noag'
                elif not gs:
                    tag = 'nodata'
                elif not avail:
                    tag = 'exh'
                elif exh_grps:
                    tag = 'part'
                else:
                    tag = 'ok'

                # —— Sort keys ——
                sk_email = email.lower()
                # Status: Ưu tiên tổng % (100+100 = 200 lớn nhất).
                g = gem_pct if gem_pct is not None else -1
                c = cld_pct if cld_pct is not None else -1
                if gem_pct is not None and cld_pct is not None:
                    sk_status = (0, -(g + c), -g, -c)
                elif gem_pct is not None or cld_pct is not None:
                    sk_status = (1, -max(g, c), 0, 0)
                else:
                    sk_status = (2, 0, 0, 0)
                # Groups: Còn → Partial → Hết tất cả → không data
                if avail and not exh_grps:
                    sk_groups = 0
                elif avail and exh_grps:
                    sk_groups = 1
                elif exh_grps:
                    sk_groups = 2
                else:
                    sk_groups = 3
                # CD: ms còn lại (nhỏ nhất = sớm nhất = đầu tiên)
                rt_s = reset_ms if (reset_ms and reset_ms > now_ms) else (
                    exh_until if (exh_until and exh_until > now_ms) else float('inf'))
                sk_cd   = rt_s
                sk_note = note.lower()
                rows.append((email, status, groups, cd, note, tag,
                             sk_email, sk_status, sk_groups, sk_cd, sk_note))

            # Codex snapshot is stored separately so it never changes Antigravity data.
            for label, info in (self._codex_data.get('accounts') or {}).items():
                primary = info.get('primary') or {}
                secondary = info.get('secondary') or {}
                used = primary.get('usedPercent')
                remaining = primary.get('remainingPercent')
                reset_s = primary.get('resetsAt') or 0
                reset_ms = reset_s * 1000 if reset_s else 0
                status = f'Codex: {remaining}% còn lại' if remaining is not None else 'Codex: chưa có data'
                if secondary.get('remainingPercent') is not None:
                    status += f' | Tuần: {secondary["remainingPercent"]}%'
                groups = f'5h/chu kỳ: {used if used is not None else "—"}% đã dùng'
                if secondary:
                    groups += ' | Weekly'
                cd = _fmt_cd(0, reset_ms) if reset_ms > now_ms else ''
                machine = self._codex_data.get('sourceMachine', '')
                note = f'Máy: {machine}' if machine else 'Snapshot Codex local'
                tag = 'codexexh' if remaining == 0 else 'codexok'
                display = f'[Codex] {label}'
                rows.append((display, status, groups, cd, note, tag,
                             display.lower(), (0, -(remaining if remaining is not None else -1), 0, 0),
                             0 if remaining else 2, reset_ms or float('inf'), note.lower()))

            # Sort — mỗi cột dùng sort key riêng (idx 6–10)
            _SORT_IDX = {'email': 6, 'status': 7, 'groups': 8, 'cd': 9, 'note': 10}
            idx = _SORT_IDX.get(self._sort_col, 6)
            rows.sort(key=lambda r: r[idx], reverse=self._sort_rev)

            for r in rows:
                self._tv.insert('', tk.END, values=r[:5], tags=(r[5],))

            total = len(rows)
            ok_n   = sum(1 for r in rows if r[5] == 'ok')
            exh_n  = sum(1 for r in rows if r[5] == 'exh')
            noag_n = sum(1 for r in rows if r[5] == 'noag')
            codex_n = sum(1 for r in rows if r[5].startswith('codex'))
            self._count_lbl.config(
                text=f'Tổng: {total}  |  Antigravity OK: {ok_n}  |  🔴 Hết: {exh_n}  |  Codex: {codex_n}  |  ⚠️ Chưa trong AG: {noag_n}')

        def _sort_by(self, col):
            self._sort_rev = (not self._sort_rev) if self._sort_col == col else False
            self._sort_col = col
            self._render()

        # ── Hành động ────────────────────────────────────────────────────
        def _choose_dat(self):
            d = filedialog.askdirectory(title='Chọn thư mục chứa quota_data.dat')
            if not d:
                return
            p = os.path.join(d, 'quota_data.dat')
            if not os.path.exists(p):
                raw = base64.b64encode(b'{}').decode('ascii')
                open(p, 'w', encoding='utf-8').write(raw)
            self._dat_path = p
            self._codex_path = _find_codex_dat(p)
            _save_cfg(p)
            self._path_lbl.config(text=self._short_path())
            self._refresh()

        def _add(self):
            """Mở Antigravity Account để thêm tài khoản rồi auto-sync."""
            launched = False
            for exe in ['antigravity-ide', 'antigravity-ide.exe', 'antigravity']:
                try:
                    subprocess.Popen(
                        [exe, '--command', 'antigravity-account.addAccount'],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    launched = True
                    break
                except (FileNotFoundError, OSError):
                    continue

            if launched:
                self._status_var.set('🔐 Đã mở Antigravity Account — Đang chờ đăng nhập (auto-sync sau 8s)…')
                self.after(8000, self._check_all)
            else:
                messagebox.showinfo(
                    '➕ Thêm tài khoản qua Antigravity Account',
                    'Để thêm tài khoản:\n\n'
                    '  1. Mở Antigravity IDE\n'
                    '  2. Mở panel Quota Tracker hoặc Antigravity Account\n'
                    '  3. Bấm ➕ Đăng nhập / Thêm để đăng nhập Google\n'
                    '  4. Quay lại đây bấm  ✓ Check All  để đồng bộ\n\n'
                    'Lý do: Antigravity Account dùng đúng OAuth của IDE,\n'
                    'nên không bao giờ bị lỗi 403 khi thêm tài khoản mới.'
                )

        def _check_all(self):
            if not self._dat_path:
                messagebox.showwarning('Chưa chọn Data', 'Vui lòng bấm 📁 Chọn Data trước.')
                return
            script = _find_sync_script()
            if not script:
                messagebox.showerror('Không tìm thấy script',
                                     'Không tìm thấy sync_antigravity.py.\n'
                                     'Đảm bảo file tồn tại trong thư mục QuotaApp.')
                return

            self._status_var.set('⏳ Đang đồng bộ từ Antigravity Account…')
            self.update_idletasks()

            def _run():
                try:
                    r = subprocess.run(
                        [sys.executable, script, self._dat_path, '--json'],
                        capture_output=True, text=True, timeout=25,
                        encoding='utf-8', errors='replace')
                    try:
                        res = json.loads(r.stdout.strip())
                    except Exception:
                        res = {'status': 'error',
                               'message': r.stdout or r.stderr,
                               'ag_emails': [], 'synced': 0}
                    self.after(0, lambda: self._on_sync_done(res))
                except subprocess.TimeoutExpired:
                    self.after(0, lambda: self._status_var.set('❌ Timeout — sync quá 25 giây'))
                except Exception as exc:
                    self.after(0, lambda: self._status_var.set(f'❌ Lỗi: {exc}'))

            threading.Thread(target=_run, daemon=True).start()

        def _on_sync_done(self, res):
            ag = res.get('ag_emails') or []
            self._ag_emails = set(ag)
            synced = res.get('synced', 0)

            # Đánh dấu email không có trong Antigravity Account
            self._data = _load_dat(self._dat_path)
            changed = False
            not_in_ag = 0
            for email, entry in self._data.items():
                if email not in self._ag_emails:
                    note = 'Chưa có trong Antigravity Account — bấm ➕ Thêm để thêm vào'
                    if entry.get('lastError') != note:
                        entry['lastError'] = note
                        changed = True
                    not_in_ag += 1
                else:
                    # Email có trong AG → xóa TOÀN BỘ lastError cũ
                    # (kể cả lỗi API, Token hết hạn, Không có token — AG đã xác nhận email hợp lệ)
                    if entry.get('lastError'):
                        del entry['lastError']
                        changed = True
            if changed:
                _save_dat(self._dat_path, self._data)

            self._render()

            if res.get('status') == 'error':
                msg = f'❌ {res.get("message", "Lỗi đồng bộ")}'
            elif synced == 0 and not ag:
                msg = '⚠️ Không tìm thấy tài khoản nào trong Antigravity Account. Hãy Thêm trước.'
            else:
                msg = f'✅ Đồng bộ {synced} tài khoản từ Antigravity Account'
                if not_in_ag:
                    msg += f'  |  ⚠️ {not_in_ag} chưa có trong AG'
            self._status_var.set(msg)

        def _sync_codex(self):
            script = _find_codex_sync_script()
            if not script:
                messagebox.showerror('Không tìm thấy script', 'Không tìm thấy QuotaApp/sync_codex.py.')
                return
            self._codex_path = _find_codex_dat(self._dat_path)
            self._status_var.set('⌁ Đang đồng bộ quota Codex local…')

            def _run():
                try:
                    r = subprocess.run([sys.executable, script, self._codex_path, '--json'],
                                       capture_output=True, text=True, timeout=20,
                                       encoding='utf-8', errors='replace')
                    try:
                        result = json.loads(r.stdout.strip())
                    except Exception:
                        result = {'status': 'error', 'message': r.stderr or r.stdout}
                    self.after(0, lambda: self._on_codex_sync_done(result))
                except Exception as exc:
                    self.after(0, lambda: self._status_var.set(f'❌ Codex sync lỗi: {exc}'))

            threading.Thread(target=_run, daemon=True).start()

        def _on_codex_sync_done(self, result):
            self._refresh()
            if result.get('status') == 'ok':
                self._status_var.set(f'✅ Codex đã đồng bộ: {result.get("account", "active account")}')
            else:
                self._status_var.set(f'⚠️ Codex: {result.get("message", "chưa có dữ liệu")})')

        def _delete_sel(self):
            sel = self._tv.selection()
            if not sel:
                return
            email = self._tv.item(sel[0])['values'][0]
            if email.startswith('[Codex] '):
                if not messagebox.askyesno('Xác nhận', f'Xóa snapshot "{email}"?'):
                    return
                label = email[len('[Codex] '):]
                accounts = self._codex_data.get('accounts') or {}
                accounts.pop(label, None)
                self._codex_data['accounts'] = accounts
                _save_dat(self._codex_path, self._codex_data)
                self._render()
                self._status_var.set(f'🗑️ Đã xóa snapshot {label}')
                return
            if not messagebox.askyesno('Xác nhận', f'Xóa "{email}" khỏi Quota Tracker?'):
                return
            self._data.pop(email, None)
            _save_dat(self._dat_path, self._data)
            self._render()
            self._status_var.set(f'🗑️ Đã xóa {email}')

        def _auto_poll(self):
            self._refresh()
            self.after(30_000, self._auto_poll)

    QuotaDBApp().mainloop()

