"""
switch_account.py  - Ghi truc tiep active account vao state.vscdb cua Antigravity IDE
Usage: python switch_account.py <email>
Output: JSON {success: bool, message: str}
"""
import sys, os, json, shutil, tempfile, sqlite3

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "message": "Usage: switch_account.py <email>"}))
        sys.exit(1)

    target_email = sys.argv[1].strip()
    db_path = os.path.join(os.environ.get("APPDATA", ""), "Antigravity IDE", "User", "globalStorage", "state.vscdb")

    if not os.path.exists(db_path):
        print(json.dumps({"success": False, "message": "Khong tim thay state.vscdb: " + db_path}))
        sys.exit(1)

    tmp = tempfile.mktemp(suffix=".vscdb")
    shutil.copy2(db_path, tmp)

    try:
        conn = sqlite3.connect(tmp)
        c = conn.cursor()
        c.execute("SELECT key, value FROM ItemTable WHERE key = 'Davissss2.antigravity-account'")
        row = c.fetchone()
        if not row:
            conn.close()
            print(json.dumps({"success": False, "message": "Khong tim thay key Davissss2.antigravity-account trong DB"}))
            sys.exit(1)

        state = json.loads(row[1])
        old_active = state.get("antigravity.accounts.active", "")

        accounts = state.get("antigravity.accounts.list", [])
        if isinstance(accounts, str):
            accounts = json.loads(accounts)

        emails = [a.get("email", "") for a in accounts]
        if target_email not in emails:
            conn.close()
            print(json.dumps({"success": False, "message": "Email " + target_email + " khong co trong danh sach: " + str(emails)}))
            sys.exit(1)

        state["antigravity.accounts.active"] = target_email
        c.execute("UPDATE ItemTable SET value = ? WHERE key = 'Davissss2.antigravity-account'", [json.dumps(state)])
        conn.commit()
        conn.close()

        shutil.copy2(tmp, db_path)
        os.remove(tmp)

        print(json.dumps({"success": True, "message": "Da chuyen " + old_active + " -> " + target_email + ". Hay Reload Window de IDE nhan."}))
    except Exception as e:
        try:
            os.remove(tmp)
        except:
            pass
        print(json.dumps({"success": False, "message": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()
