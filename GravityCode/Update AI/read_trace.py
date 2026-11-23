with open('trace_00', encoding='utf-8', errors='ignore') as f:
    text = f.read()

idx = text.find('"main" prio=')
if idx != -1:
    print(text[idx:idx+2000])
else:
    print('main thread not found')
