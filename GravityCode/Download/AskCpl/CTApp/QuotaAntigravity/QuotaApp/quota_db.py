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
                merged[email] = info  # dat m\u1edbi h\u01a1n, \u01b0u ti\u00ean dat

    write_accounts(db_path, merged)
    return merged


# --- CLI (test) ---
if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print('Usage: python quota_db.py <quota_data.dat>')
        sys.exit(1)

    dat_path = sys.argv[1]
    db_path  = get_db_path(dat_path)
    print(f'DB path: {db_path}')

    # Read existing dat
    if os.path.exists(dat_path):
        import base64 as b64
        raw = open(dat_path, encoding='utf-8').read().strip()
        if raw:
            dat_data = json.loads(b64.b64decode(raw).decode('utf-8'))
        else:
            dat_data = {}
    else:
        dat_data = {}

    merged = merge_and_sync(dat_data, db_path)
    print(f'Merged {len(merged)} accounts into DB.')
    for email, info in merged.items():
        avail = ','.join(info.get('availableGroups') or []) or 'NONE'
        exh   = ','.join(info.get('exhaustedGroups') or []) or 'NONE'
        print(f'  {email}: OK=[{avail}] EX=[{exh}]')
