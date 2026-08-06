import glob
import re
import urllib.request
from urllib.error import URLError, HTTPError
import ssl
import time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

files = glob.glob('data_*.md')
files = [f for f in files if f != 'data_Tuong.md']

dead_links = {}

# Pass 1: Identify dead links
for fpath in files:
    try:
        with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
    except Exception as e:
        print(f'Skipping {fpath}: {e}')
        continue
    
    links = list(set(re.findall(r'https?://[^\s*\)\"\]]+', text)))
    dead_links[fpath] = []
    
    print(f'--- Checking {fpath} ({len(links)} links) ---')
    for link in links:
        try:
            req = urllib.request.Request(link, headers={'User-Agent': 'Mozilla/5.0'})
            res = urllib.request.urlopen(req, context=ctx, timeout=3)
        except HTTPError as e:
            if e.code == 404:
                print(f'404 DEAD: {link}')
                dead_links[fpath].append(link)
        except Exception as e:
            pass
        time.sleep(0.05)

# Pass 2: Clean up dead links from files
for fpath, d_links in dead_links.items():
    if not d_links:
        continue
    with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    new_lines = []
    for line in lines:
        for dl in d_links:
            if f'({dl})' in line:
                line = line.replace(f'({dl})', ' *(Link đã 404)*')
            elif dl in line:
                line = line.replace(dl, '*(Link đã 404)*')
        new_lines.append(line)
        
    with open(fpath, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print(f'Cleaned {len(d_links)} dead links from {fpath}')
