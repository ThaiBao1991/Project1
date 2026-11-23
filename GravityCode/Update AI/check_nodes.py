with open('sheet_before_click.xml', encoding='utf-8') as f:
    xml = f.read()

import ultra0
for i, n in enumerate(ultra0.nodes(xml)):
    val = (n['text'] or '') + ' ' + (n['desc'] or '')
    if 'Đăng ký' in val or 'Subscribe' in val:
        print(f"Match {i}: {n['cls']} | text={n['text']!r} | desc={n['desc']!r} | x={n['x']}, y={n['y']}")
