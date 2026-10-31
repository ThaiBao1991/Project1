---
name: add_host_checklist
description: >
  Quy trinh kiem tra bat buoc khi them host moi vao ghfuConfig.json cho ung dung GetHtmlFromUrl Python.
  Bao gom checklist xac minh: lay danh sach chuong, phan trang, noi dung chuong, tieu de chuong,
  cung cac loi pho bien da gap (id vs class, pagingPattern nham CSS, domain aliasing).
---

# Quy trinh Them Host Moi - Checklist Bat Buoc

## Buoc 0: Phan tich cau truc trang truoc khi cau hinh

Truoc khi viet bat ky entry nao vao ghfuConfig.json, phai chay phan tich thuc te:

```python
import requests
from bs4 import BeautifulSoup

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
url = "<STORY_URL>"
r = requests.get(url, headers=headers, timeout=15)
soup = BeautifulSoup(r.text, "html.parser")
```

---

## GATE 1 - Xac minh Danh Sach Chuong (Chapter List)

### 1.1 Tim CSS selector danh sach chuong

```python
for css in ["#list-chapter ul a", "div.list-chap ul a", ".chapter-list a", "ul.list-chapter a"]:
    els = soup.select(css)
    chap_links = [e["href"] for e in els if "/chuong-" in e.get("href", "") or "chapter" in e.get("href", "")]
    if chap_links:
        print(f"CSS: {css} -> {len(chap_links)} links")
        print(f"  First: {chap_links[0]}")
        print(f"  Last:  {chap_links[-1]}")
        break
```

Kiem tra bat buoc:
- [ ] Selector phai lay duoc TAT CA the <a> link chuong tren trang (khong phai chi 1)
- [ ] Neu selector la parent (vi du ul), engine chi lay <a> dau tien -> phai them "a" vao cuoi selector (vd: div.list-chap ul a)
- [ ] Xac nhan link format: absolute (https://...) hay relative (/chuong-X/)

LOI KINH DIEN #1: Dung "div.list-chap ul" thay vi "div.list-chap ul a" -> chi lay duoc 1 link/ul

---

### 1.2 Xac minh Phan Trang (Pagination)

pagingPattern trong Java la CHUOI NOI VAO URL, KHONG PHAI CSS SELECTOR
vi du: "?page=" -> URL = story_url + "?page=2"
vi du: "/trang-" -> URL = story_url + "/trang-2"

```python
pattern = "?page="
for page in range(1, 4):
    test_url = url.split("?")[0].rstrip("/") + ("" if page == 1 else pattern + str(page))
    r = requests.get(test_url, headers=headers, timeout=15)
    soup_p = BeautifulSoup(r.text, "html.parser")
    chap_links = [e["href"] for e in soup_p.select(css) if "/chuong-" in e.get("href", "")]
    print(f"Page {page}: {len(chap_links)} links | First: {chap_links[0] if chap_links else 'NONE'}")
```

Kiem tra bat buoc:
- [ ] So chuong/trang co nhat quan khong
- [ ] Link chuong tu trang 2+ co doi domain khong (vi du: trang 1 -> domain-a.com, trang 2 -> domain-b.com)
  Neu co doi domain -> phai them domain alias vao config
- [ ] Trang cuoi (last page) co link khong

LOI KINH DIEN #2: pagingPattern = "?page=" bi dung nhu CSS selector -> "Invalid character ? position 0"
Day la chuoi noi URL, engine se build: url + "?page=" + str(page_num)

---

## GATE 2 - Xac minh Noi Dung Chuong (Chapter Content)

### 2.1 Tim CSS selector noi dung chuong

QUAN TRONG: Phan biet ro id (#) va class (.) - rat hay bi nham!

```python
chap_url = chap_links[0]
r2 = requests.get(chap_url, headers=headers, timeout=15)
soup2 = BeautifulSoup(r2.text, "html.parser")

print("=== TIM THEO ID (dung # trong CSS) ===")
for cid in ["chapter-c", "chapter-content", "content", "nd-chuong", "j_content", "chapt-content"]:
    el = soup2.find(id=cid)
    if el:
        text = el.get_text(strip=True)
        print(f"id={cid}: {len(text)} chars | {text[:60]}")

print("=== TIM THEO CLASS (dung . trong CSS) ===")
for cname in ["chapter-c", "chapter-content", "content", "nd-chuong"]:
    el = soup2.find(class_=cname)
    if el:
        text = el.get_text(strip=True)
        print(f"class={cname}: {len(text)} chars | {text[:60]}")
```

Kiem tra bat buoc:
- [ ] Phan tu tim thay co NOI DUNG THUC (> 200 chars)? Neu < 100 chars -> sai selector
- [ ] Xac dinh ro la id hay class:
  HTML <div id="chapter-c"> -> CSS selector: #chapter-c
  HTML <div class="chapter-c"> -> CSS selector: .chapter-c

LOI KINH DIEN #3: Ghi #chapter-c (id) nhung trang dung class="chapter-c" -> content trong hoan toan

---

### 2.2 Test chapter tu domain phu (neu co)

```python
alt_url = "https://domain-phu.com/truyen/chuong-51/"
r3 = requests.get(alt_url, headers=headers, timeout=15)
soup3 = BeautifulSoup(r3.text, "html.parser")
el = soup3.find(class_="chapter-c") or soup3.find(id="chapter-c")
print(f"Domain phu content: {len(el.get_text()) if el else 'NOT FOUND'} chars")
```

---

## GATE 3 - Xac minh Tieu De Chuong (Chapter Title)

```python
for sel in [".chapter-title", "h1", "h2", "h3", ".title", "#chapter-title"]:
    t = soup2.select_one(sel)
    if t and len(t.get_text(strip=True)) > 3:
        print(f"Title selector: {sel} -> {t.get_text(strip=True)}")
        break
```

Kiem tra bat buoc:
- [ ] Selector lay duoc tieu de chinh xac (dang "Chuong X: Ten chuong")
- [ ] Khong lay nham tieu de sach hoac breadcrumb

---

## GATE 4 - Viet Config Entry & Verify

Template config entry chuan:

```json
{
  "pageCode": "domain.com",
  "pagingPattern": "?page=",
  "cssQueryGetListChapter": "div.list-chap ul a",
  "cssQueryGetChapterTitle": "h2",
  "cssQueryGetChapterContent": ".chapter-c",
  "urlPageTest": "https://domain.com/ten-truyen",
  "cssFilter": "[style];form;button;script;",
  "isManualGet": false,
  "isChapterLinkAsolute": true,
  "isEnableChapterSign": false,
  "isRevertChapterList": false,
  "isForumType": false,
  "overMaxSizePageCountState": "MOVE_TO_LAST",
  "isUseJsoupGet": true,
  "isVietNameseHost": true,
  "scriptJS": "",
  "byPassCloudFlare": false
}
```

Cac truong quan trong:

| Truong | Chu y |
|--------|-------|
| cssQueryGetListChapter | Ket thuc bang "a" de lay link truc tiep, vi du "ul.list a" |
| cssQueryGetChapterContent | Dung #id cho id, .class cho class - KHONG DUOC NHAM |
| pagingPattern | Chuoi noi URL, KHONG PHAI CSS selector |
| isChapterLinkAsolute | true neu href la URL day du, false neu la path relative |

---

## GATE 5 - Kiem Tra Toan Dien Sau Khi Them Config

1. Muc luc: Dan URL truyen -> nhan "Lay muc luc" -> xac nhan so chuong dung
2. Tai thu 3 chuong: Chuong 1, chuong giua, chuong cuoi (chuong tu trang 2+ de test domain alias)
3. Kiem tra HTML output: Mo file HTML -> xac nhan co noi dung that (khong trong)
4. Kiem tra tieu de: Muc luc HTML co hien thi ten chuong dung khong

---

## Bang loi pho bien da tung gap

| Trieu chung | Nguyen nhan | Cach fix |
|-------------|-------------|----------|
| "Invalid character ? position 0" | pagingPattern bi dung nhu CSS selector | Chuoi noi URL, engine build tu dong |
| Chi lay duoc 1 link/trang muc luc | CSS selector tro vao ul thay vi a | Them " a" vao cuoi selector |
| Noi dung chuong trong | Nham id thanh class hoac nguoc lai | Kiem tra HTML thuc te bang find(id=X) vs find(class_=X) |
| Chuong tu trang 2+ khong co noi dung | Link tro sang domain phu khong co content | Them domain phu vao config voi cung CSS selectors |
| Timeout o trang 19+ | Server rate-limit khi quet qua nhanh | Engine co delay 0.5s/trang; neu van loi tang delay |
| Font chu loi trong PRC | KindleGen doc sai encoding | Dung utf-8-sig BOM + meta http-equiv Content-Type |

---

## Ghi chu ve Domain Aliasing

Mot so site dung nhieu domain (CDN load balancing hoac mirror):
- Trang muc luc domain-a.com tra link chuong qua domain-b.com
- Can them entry rieng cho domain-b.com voi cung cssQueryGetChapterContent va cssQueryGetChapterTitle
- Vi du da xu ly: metruyenhotvn.com (muc luc) -> chuong trang 2+ link sang metruyenhot.me (cung cau truc HTML .chapter-c)
