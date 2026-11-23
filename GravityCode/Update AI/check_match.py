with open('sheet_before_click.xml', encoding='utf-8') as f:
    s = f.read()
import re
for m in re.finditer(r'text="([^"]*)"', s):
    t = m.group(1)
    if any(k in t.lower() for k in ['mật khẩu', 'password', 'xác minh']):
        print('Matched:', t)
