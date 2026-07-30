"""
sync_antigravity.py — Đọc SQLite state.vscdb của Antigravity IDE, phân tích quota theo GROUP model.

Option B: Tách riêng Gemini / Claude / GPT
  - Mỗi group có status riêng (exhausted / ok + resetTime)
  - overall exhaustedUntil = 0 nếu còn bất kỳ group nào OK
  - quota_data.json lưu thêm field `groupStatus`, `availableGroups`

Data format in DB (key: Davissss2.antigravity-account):
  antigravity.accounts.list: [
    { email, status, balances: { model_id: { value: 0-100, resetTime: ISO } } }
  ]
"""

import sqlite3
import json
import os
import shutil
import sys
import time
import base64
from pathlib import Path
from datetime import datetime

# Import quota_db (same directory)
try:
    import quota_db as _qdb
    _HAS_QUOTA_DB = True
except ImportError:
    _HAS_QUOTA_DB = False

# --- Model Group definitions ---
def _is_gemini(m): return m.startswith('gemini-') or m == 'gemini-pro-agent'
def _is_claude(m): return m.startswith('claude-')
def _is_gpt(m): return m.startswith('gpt-')

MODEL_GROUPS = {
    'gemini': _is_gemini,
    'claude': _is_claude,
    'gpt': _is_gpt,
}

# Human-readable labels
GROUP_LABELS = {
    'gemini': 'Gemini',
    'claude': 'Claude',
    'gpt': 'GPT',
}


def get_db_paths():
    """Tìm tất cả file state.vscdb trong Antigravity IDE (global + profiles)."""
    roaming = Path(os.environ.get('APPDATA', '')) / 'Antigravity IDE' / 'User'
    paths = []

    global_db = roaming / 'globalStorage' / 'state.vscdb'
    if global_db.exists():
        paths.append(global_db)

    profiles_dir = roaming / 'profiles'
    if profiles_dir.exists():
        for p in profiles_dir.iterdir():
            if p.is_dir():
                profile_db = p / 'globalStorage' / 'state.vscdb'
                if profile_db.exists():
                    paths.append(profile_db)

    return paths


def parse_iso_ms(date_str):
    """ISO 8601 UTC string → timestamp milliseconds."""
    if not date_str:
        return 0
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return int(dt.timestamp() * 1000)
    except Exception:
        return 0


def assess_account(acc):
    """
    Phân tích balance theo nhóm model (Option B).

    Returns dict hoặc None nếu skip:
    {
        'exhaustedUntil': int,        # 0 nếu còn group OK, else max resetTime của ALL groups
        'groupStatus': {
            'gemini': { 'exhausted': bool, 'resetTime': int_ms },
            'claude': { 'exhausted': bool, 'resetTime': int_ms },
            'gpt':    { 'exhausted': bool, 'resetTime': int_ms },
        },
        'availableGroups': ['claude', 'gpt'],  # groups còn dùng được
        'exhaustedGroups': ['gemini'],          # groups đã hết
        'hasAnyIssue': bool,                    # True nếu ít nhất 1 group hết
        'allExhausted': bool,                   # True nếu tất cả groups hết
    }
    """
    status = acc.get('status', '')
    balances = acc.get('balances', {})

    if status == 'error' or not balances:
        return None

    now_ms = int(time.time() * 1000)
    group_status = {}

    for group_name, matcher in MODEL_GROUPS.items():
        # Lấy tất cả model thuộc group này
        group_balances = {m: info for m, info in balances.items() if matcher(m) and isinstance(info, dict)}

        if not group_balances:
            continue

        key_model = None
        if group_name == 'claude':
            key_model = 'claude-sonnet-4-6'
        elif group_name == 'gemini':
            key_model = 'gemini-3.1-pro-high'
        elif group_name == 'gpt':
            key_model = 'gpt-oss-120b-medium'

        is_exhausted = False
        reset_time = 0
        percent = 100

        # Lấy trạng thái của Key Model làm chuẩn cho cả Group
        if key_model and key_model in group_balances:
            info = group_balances[key_model]
            percent = info.get('value', 100)
            reset_time = parse_iso_ms(info.get('resetTime', ''))

            if percent == 0 and reset_time > now_ms:
                is_exhausted = True
            elif percent == 0 and reset_time <= now_ms:
                # reset đã qua → ok rồi
                is_exhausted = False
                percent = 100
                reset_time = 0
        else:
            # Fallback nếu không tìm thấy key model
            depleted = [(m, info) for m, info in group_balances.items()
                        if info.get('value', -1) == 0 and info.get('resetTime')]
            total = len(group_balances)

            # Group exhausted nếu > 50% model của group = 0
            if len(depleted) >= max(1, total // 2):
                max_reset = max((parse_iso_ms(info.get('resetTime', '')) for _, info in depleted), default=0)
                if max_reset > now_ms:
                    is_exhausted = True
                    reset_time = max_reset
                    percent = 0
                else:
                    is_exhausted = False
                    reset_time = 0
                    percent = 100
            else:
                ok_models = [info for m, info in group_balances.items() if info.get('value', -1) > 0]
                percent = min((info.get('value', 100) for info in ok_models), default=100) if ok_models else 100
                dep_resets = [parse_iso_ms(info.get('resetTime', '')) for _, info in depleted if parse_iso_ms(info.get('resetTime', '')) > now_ms]
                reset_time = min(dep_resets) if dep_resets else 0

        group_status[group_name] = {'exhausted': is_exhausted, 'resetTime': reset_time, 'percent': percent}

    if not group_status:
        return None

    available_groups = [g for g, info in group_status.items() if not info['exhausted']]
    exhausted_groups = [g for g, info in group_status.items() if info['exhausted']]
    all_exhausted = len(available_groups) == 0
    has_any_issue = len(exhausted_groups) > 0

    # overallResetTime tính theo thời điểm phục hồi của các KEY MODELS thay vì toàn bộ model
    key_resets = []
    for group_name, info in group_status.items():
        rt = info.get('resetTime', 0)
        if rt > now_ms:
            key_resets.append(rt)
    
    # Lấy thời gian phục hồi gần nhất trong số các group đang có resetTime
    overall_reset = min(key_resets) if key_resets else 0
    exhausted_until = overall_reset if all_exhausted else 0

    return {
        'exhaustedUntil': exhausted_until,
        'overallResetTime': overall_reset,
        'groupStatus': group_status,
        'availableGroups': available_groups,
        'exhaustedGroups': exhausted_groups,
        'hasAnyIssue': has_any_issue,
        'allExhausted': all_exhausted,
    }


def extract_accounts_from_db(db_path):
    """Copy DB → temp → query accounts list. Safe khi IDE đang chạy (file lock).
    Đọc cả 2 nguồn: Antigravity Account + Quota Tracker extension.
    """
    temp_db = Path(os.environ.get('TEMP', '/tmp')) / f'ag_state_{int(time.time()*1000)}.vscdb'
    all_accs = {}  # email → acc (merge 2 nguồn)
    try:
        shutil.copy2(db_path, temp_db)
        conn = sqlite3.connect(temp_db)
        c = conn.cursor()

        # Key 'Davissss2.antigravity-account' là NGUỒN SỰ THẬT duy nhất từ Antigravity Account extension
        key = 'Davissss2.antigravity-account'
        try:
            c.execute("SELECT value FROM ItemTable WHERE key=?", (key,))
            row = c.fetchone()
            if row:
                data = json.loads(row[0])
                for acc in data.get('antigravity.accounts.list', []):
                    email = acc.get('email')
                    if email:
                        all_accs[email] = acc
        except Exception as e:
            print(f"[sync] Error reading {key}: {e}")

        conn.close()
        return list(all_accs.values())
    except Exception as e:
        print(f'[sync] Warning - reading {db_path.name}: {e}')
        return list(all_accs.values())
    finally:
        if temp_db.exists():
            try:
                temp_db.unlink()
            except Exception:
                pass


def sync_quota_data(quota_json_path, email_filter=None):
    """
    Hàm chính: đọc tất cả DB → phân tích quota theo nhóm → ghi vào quota_data.dat.
    """
    db_paths = get_db_paths()
    if not db_paths:
        return {
            'status': 'no_db',
            'message': 'Không tìm thấy Antigravity IDE Database.',
            'synced': 0, 'skipped': 0, 'accounts': []
        }

    all_accounts = {}
    for db in db_paths:
        for acc in extract_accounts_from_db(db):
            email = acc.get('email')
            if email:
                all_accounts[email] = acc

    if not all_accounts:
        return {
            'status': 'ok',
            'message': 'Không tìm thấy tài khoản nào trong IDE.',
            'synced': 0, 'skipped': 0, 'accounts': []
        }

    # Load quota_data.dat
    quota_data = {}
    if os.path.exists(quota_json_path):
        try:
            with open(quota_json_path, 'r', encoding='utf-8') as f:
                raw = f.read().strip()
                if raw:
                    decoded = base64.b64decode(raw).decode('utf-8')
                    quota_data = json.loads(decoded)
        except Exception as e:
            print(f"[sync] Warning: Could not read existing {quota_json_path}: {e}")

    now_ms = int(time.time() * 1000)
    synced_count = 0
    skipped_count = 0
    account_summaries = []

    # Tập hợp tất cả emails cần xử lý:
    # - từ SQLite (all_accounts) — đây là nguồn sự thật từ Antigravity Account
    # - từ quota_data.dat — chỉ cho email Quota Tracker quản lý riêng (không có trong DB)
    all_emails = set(all_accounts.keys()) | set(quota_data.keys())

    for email in all_emails:
        if email_filter and email.lower() != email_filter.lower():
            skipped_count += 1
            continue

        # Lấy acc từ SQLite (Antigravity Account DB) và từ quota_data.dat (API live data)
        acc_db = all_accounts.get(email)
        dat_entry = quota_data.get(email, {})
        dat_balances = dat_entry.get('balances', {})

        bals_db = acc_db.get('balances', {}) if (acc_db and isinstance(acc_db, dict)) else {}

        # Conservative merge: Kết hợp cả DB và Live API data
        # Nếu BẤT KỲ nguồn nào (IDE DB hoặc Live API) ghi nhận model = 0 (hết quota),
        # ta lấy min(value_db, value_api) = 0 để phản ánh chính xác trạng thái thực tế.
        all_models = set(bals_db.keys()) | set(dat_balances.keys())

        if all_models:
            merged_bals = {}
            for m in all_models:
                info_db = bals_db.get(m)
                info_api = dat_balances.get(m)

                val_db = info_db.get('value', 100) if isinstance(info_db, dict) else 100
                val_api = info_api.get('value', 100) if isinstance(info_api, dict) else 100

                # Giá trị xấu nhất sẽ quyết định (nếu 1 trong 2 nguồn ghi 0% thì model = 0%)
                final_val = min(val_db, val_api)

                rst_db = info_db.get('resetTime') if isinstance(info_db, dict) else None
                rst_api = info_api.get('resetTime') if isinstance(info_api, dict) else None
                final_rst = rst_db or rst_api or ''

                merged_bals[m] = {
                    'value': final_val,
                    'resetTime': final_rst
                }
            acc = {
                'email': email,
                'status': 'active',
                'balances': merged_bals,
            }
        elif acc_db is not None:
            acc = acc_db
        else:
            skipped_count += 1
            continue

        result = assess_account(acc)

        if result is None:
            skipped_count += 1
            continue

        entry = quota_data.get(email, {})
        # Bảo tồn tokens field nếu có (dùng để di chuyển cross-machine)
        existing_tokens = entry.get('tokens')
        # Chỉ cập nhật các field tính toán (computed), không ghi đè tokens
        entry.update({
            'balances': merged_bals,
            'exhaustedUntil': result['exhaustedUntil'],
            'overallResetTime': result['overallResetTime'],
            'lastUpdate': now_ms,
            'source': 'auto-sync',
            'groupStatus': result['groupStatus'],
            'availableGroups': result['availableGroups'],
            'exhaustedGroups': result['exhaustedGroups'],
        })
        # Khôi phục tokens nếu có (tránh bị ghi đè bởi entry.update)
        if existing_tokens:
            entry['tokens'] = existing_tokens

        quota_data[email] = entry
        synced_count += 1

        account_summaries.append({
            'email': email,
            'allExhausted': result['allExhausted'],
            'hasAnyIssue': result['hasAnyIssue'],
            'availableGroups': result['availableGroups'],
            'exhaustedGroups': result['exhaustedGroups'],
        })

    # Ghi lại quota_data.dat (Base64)
    try:
        json_str = json.dumps(quota_data, ensure_ascii=False)
        encoded = base64.b64encode(json_str.encode('utf-8')).decode('ascii')
        with open(quota_json_path, 'w', encoding='utf-8') as f:
            f.write(encoded)
    except Exception as e:
        return {'status': 'error', 'message': f'Loi ghi file Data: {e}', 'synced': synced_count, 'skipped': skipped_count, 'accounts': []}

    # Đồng bộ vào SQLite DB (nếu quota_db đã cài)
    if _HAS_QUOTA_DB:
        try:
            db_path = _qdb.get_db_path(quota_json_path)
            _qdb.merge_and_sync(quota_data, db_path)
        except Exception as e:
            print(f'[sync] Warning: quota_db sync failed: {e}')

    msg_parts = [f'Sync {synced_count} tai khoan tu IDE.']
    fully_exhausted = [a for a in account_summaries if a['allExhausted']]
    partial = [a for a in account_summaries if a['hasAnyIssue'] and not a['allExhausted']]
    if fully_exhausted:
        msg_parts.append(f'{len(fully_exhausted)} het quota hoan toan.')
    if partial:
        msgs = [f"{a['email'].split('@')[0]}: con {','.join(a['availableGroups'])}" for a in partial]
        msg_parts.append(f'{len(partial)} het mot so model ({"; ".join(msgs)}).')
    if skipped_count:
        msg_parts.append(f'{skipped_count} bo qua (chua co balance data).')

    return {
        'status': 'ok',
        'message': ' '.join(msg_parts),
        'synced': synced_count,
        'skipped': skipped_count,
        'accounts': account_summaries,
        'ag_emails': list(all_accounts.keys()),  # danh sách email THỰC SỰ từ Antigravity Account DB
    }


def db_available():
    """Trả về True nếu tìm thấy DB của Antigravity IDE (dùng để check từ máy khác)."""
    return len(get_db_paths()) > 0


if __name__ == '__main__':
    import argparse
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    parser = argparse.ArgumentParser(description='Sync Antigravity quota data from IDE DB')
    parser.add_argument('data_path', nargs='?', default='quota_data.dat',
                        help='Path to quota_data.dat file')
    parser.add_argument('--email', default=None,
                        help='Only sync this specific email (case-insensitive)')
    parser.add_argument('--json', action='store_true',
                        help='Output JSON result instead of human-readable text')
    args = parser.parse_args()

    res = sync_quota_data(args.data_path, email_filter=args.email)

    if args.json:
        # Output JSON từ chương trình để extension.js có thể parse
        print(json.dumps(res, ensure_ascii=False))
    else:
        print(f'[sync] Target: {args.data_path}')
        print(f'[sync] Email filter: {args.email or "ALL"}')
        print(f'[sync] DB found: {db_available()}')
        print(f'[sync] Status : {res["status"]}')
        print(f'[sync] Synced : {res["synced"]} | Skipped: {res.get("skipped", 0)}')
        print(f'[sync] Message: {res["message"]}')
        if res.get('accounts'):
            print('[sync] Detail:')
            for a in res['accounts']:
                ok = ','.join(a['availableGroups']) or 'NONE'
                ex = ','.join(a['exhaustedGroups']) or 'NONE'
                print(f'  {a["email"]}: OK=[{ok}] EX=[{ex}]')
