import codecs, glob, os
os.environ['PYTHONIOENCODING'] = 'utf-8'

report = []
for f in sorted(glob.glob('data_*.md')):
    with codecs.open(f, 'r', 'utf-8') as fh:
        lines = fh.readlines()
    headers = [l.strip() for l in lines if l.startswith('## ') or l.startswith('### ')]
    report.append(f'\n=== {f} ({len(lines)} lines) ===')
    for h in headers:
        report.append('  ' + h)

with codecs.open('audit_report.txt', 'w', 'utf-8') as f:
    f.write('\n'.join(report))

print("Audit done")
