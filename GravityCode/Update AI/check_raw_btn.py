with open('sheet_before_click.xml', encoding='utf-8') as f:
    xml = f.read()

import re
for m in re.finditer(r'<node[^>]*text="Đăng ký"[^>]*>', xml):
    print(m.group(0))
