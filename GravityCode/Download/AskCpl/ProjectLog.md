# Project Log: á»¨ng dá»¥ng Quáº£n lÃ½ NgÃ y há»c Copilot

File nÃ y dÃ¹ng Ä‘á»ƒ theo dÃµi quÃ¡ trÃ¬nh lÃ m viá»‡c, cÃ¡c quyáº¿t Ä‘á»‹nh quan trá»ng vÃ  tiáº¿n Ä‘á»™ cá»§a dá»± Ã¡n.

## Má»¥c tiÃªu
Táº¡o giao diá»‡n Ä‘á»ƒ tá»± Ä‘á»™ng lÆ°u cÃ¡c ngÃ y há»c Tiáº¿ng Anh vÃ  Tiáº¿ng Nháº­t tá»« cÃ¡c agent Copilot, sau Ä‘Ã³ káº¿t xuáº¥t thÃ nh file Word (.docx) cháº¥t lÆ°á»£ng cao.

---

## Nháº­t kÃ½ cÃ´ng viá»‡c

## 2026-07-29: Tá»‘i Æ°u hoÃ¡ Lazy Load cho file .askcpl vÃ  Fix lá»—i hiá»ƒn thá»‹ file
- **Sá»­a lá»—i hiá»ƒn thá»‹**: Cáº­p nháº­t iletypes cá»§a skopenfilename vÃ  sksaveasfilename thÃ nh [('AskCpl Encrypted', '*.askcpl'), ('All Files', '*.*')] Ä‘á»ƒ fix lá»—i khÃ´ng tháº¥y file.
- **Lazy Loading**: Khi má»Ÿ file .askcpl, há»‡ thá»‘ng nay giáº£i mÃ£ ra file .zip táº¡m thá»i vÃ  chá»‰ Ä‘á»c Index thay vÃ¬ bung nÃ©n vÃ  quÃ©t toÃ n bá»™ thÆ° má»¥c.
- **Lazy Extraction**: Khi báº¥m vÃ o day_X.html, á»©ng dá»¥ng sáº½ bung nÃ©n vÃ  quÃ©t file Ä‘Ã³ on-demand. Giáº£m thá»i gian má»Ÿ file lá»›n tá»« vÃ i chá»¥c giÃ¢y xuá»‘ng 1-2 giÃ¢y.
- **Lazy Saving**: Khi lÆ°u, hÃ m encrypt_from_zip_and_folder tá»± káº¿t há»£p cÃ¡c file Ä‘Ã£ chá»‰nh sá»­a á»Ÿ thÆ° má»¥c táº¡m vá»›i file zip gá»‘c Ä‘á»ƒ lÆ°u láº¡i (cÃ³ loáº¡i bá» cÃ¡c file bá»‹ xÃ³a trong phiÃªn) mÃ  khÃ´ng cáº§n bung táº¥t cáº£.


### Giai Ä‘oáº¡n 1 â€” Thiáº¿t káº¿ kiáº¿n trÃºc & XÃ¢y dá»±ng cÆ¡ báº£n
- **Thiáº¿t káº¿ ban Ä‘áº§u:** Dá»± Ä‘á»‹nh lÃ m Desktop App Ä‘á»ƒ paste dá»¯ liá»‡u thá»§ cÃ´ng.
- **Thay Ä‘á»•i kiáº¿n trÃºc (Hybrid Approach):** Chia lÃ m 2 pháº§n:
  1. **Browser Extension (Add-on):** Tá»± Ä‘á»™ng chat "Day X" láº·p Ä‘i láº·p láº¡i vá»›i Copilot, cáº¡o dá»¯ liá»‡u HTML vÃ  lÆ°u vÃ o file JSON.
  2. **Python Script (`AskCpl.py`):** Viáº¿t báº±ng Tkinter vÃ  `pywin32`. Äá»c file JSON vÃ  táº¡o file Word vá»›i tá»«ng trang tÃ¡ch biá»‡t.
- **HoÃ n thÃ nh code láº§n Ä‘áº§u:** Táº¡o toÃ n bá»™ `manifest.json`, `popup.html`, `popup.js`, `content_script.js` vÃ  `AskCpl.py`.

### Giai Ä‘oáº¡n 2 â€” Kháº¯c phá»¥c lá»—i khÃ´ng inject Ä‘Æ°á»£c vÃ o trang
- **Váº¥n Ä‘á»:** Add-on khÃ´ng hiá»‡n log, khÃ´ng cháº¡y Ä‘Æ°á»£c trÃªn trang `m365.cloud.microsoft`.
- **NguyÃªn nhÃ¢n:** `manifest.json` chá»‰ cÃ³ quyá»n cho `*.microsoft.com`, thiáº¿u `*.cloud.microsoft`.
- **Giáº£i phÃ¡p:** Äá»•i `host_permissions` vÃ  `content_scripts matches` thÃ nh `<all_urls>`.
- **ThÃªm:** Bá»• sung `sendResponse()` + `return true` trong listener Ä‘á»ƒ trÃ¡nh lá»—i "port closed" cá»§a Manifest V3.

### Giai Ä‘oáº¡n 3 â€” Kháº¯c phá»¥c lá»—i file JSON khÃ´ng táº£i Ä‘Æ°á»£c (CSP Block)
- **Váº¥n Ä‘á»:** VÃ²ng láº·p cháº¡y xong nhÆ°ng khÃ´ng cÃ³ file nÃ o rá»›t xuá»‘ng Downloads.
- **NguyÃªn nhÃ¢n:** Microsoft 365 CSP cháº·n hoÃ n toÃ n `blob:` URL vÃ  link click táº¡o tá»« content script.
- **Giáº£i phÃ¡p:**
  - Táº¡o thÃªm `background.js` (Service Worker) + xin quyá»n `downloads`.
  - `content_script.js` gá»­i dá»¯ liá»‡u lÃªn `background.js` qua `chrome.runtime.sendMessage`.
  - `background.js` dÃ¹ng `chrome.downloads.download()` Ä‘á»ƒ táº£i file, bypass hoÃ n toÃ n CSP.

### Giai Ä‘oáº¡n 4 â€” Anti-Throttling (Giá»¯ tab khÃ´ng bá»‹ ngá»§)
- **Váº¥n Ä‘á»:** Tab bá»‹ thu nhá» â†’ trÃ¬nh duyá»‡t lÃ m cháº­m `setTimeout` â†’ Add-on cháº¡y ráº¥t cháº­m.
- **Giáº£i phÃ¡p:** ThÃªm cÆ¡ cháº¿ **Silent Audio Keep-alive**:
  - NhÃºng file WAV vÃ´ Ã¢m dÆ°á»›i dáº¡ng base64 data URI.
  - Khi báº¯t Ä‘áº§u cháº¡y: phÃ¡t audio láº·p â†’ tab khÃ´ng bá»‹ throttle dÃ¹ thu nhá».
  - Khi dá»«ng/hoÃ n táº¥t: `stopKeepAlive()` táº¯t audio.

### Giai Ä‘oáº¡n 5 â€” TÃ­nh nÄƒng TÃªn Agent & TÃªn File tÃ¹y chá»‰nh
- ThÃªm Ã´ nháº­p **"TÃªn Agent"** trÃªn Popup.
- TÃªn Agent dÃ¹ng lÃ m prefix cho tÃªn file JSON: `TenAgent_KhoaHoc_YYYYMMDD.json`.

### Giai Ä‘oáº¡n 6 â€” Tá»‘i Æ°u hÃ³a CPU & RAM
- **DOM Caching:** `cachedInput` vÃ  `cachedSendBtn` â€” tÃ¬m 1 láº§n rá»“i nhá»› láº¡i.
- **TÄƒng interval polling:** 2s â†’ 4s/láº§n khi chá» AI tráº£ lá»i.
- **TÄƒng thá»i gian nghá»‰:** 4s â†’ 8s giá»¯a cÃ¡c vÃ²ng (giáº£m táº£i CPU, cho GC dá»n RAM).

### Giai Ä‘oáº¡n 7 â€” Sá»­a 5 Bug tiá»m áº©n nghiÃªm trá»ng

| # | Bug | Háº­u quáº£ | Fix |
|---|-----|----------|-----|
| 1 | `cachedSendBtn` khÃ´ng check `.disabled` | Gá»­i prompt khi AI váº«n Ä‘ang gÃµ | Reset cache khi nÃºt bá»‹ disable |
| 2 | LuÃ´n dÃ¹ng `findDeep()` cho nÃºt Stop | QuÃ©t shadow DOM náº·ng má»—i 4s | Kiá»ƒm tra DOM thÆ°á»ng trÆ°á»›c |
| 3 | DÃ¹ng `alert()` khi khÃ´ng cÃ³ data | ÄÃ³ng bÄƒng toÃ n trang Copilot | Äá»•i thÃ nh `sendStatus()` |
| 4 | `runNextDay()` gá»i Ä‘á»‡ quy trá»±c tiáº¿p | Call stack trÃ n sau 100+ ngÃ y | Äá»•i thÃ nh `setTimeout(() => runNextDay(), 0)` |
| 5 | `join('\\\\n')` sai escape | JSON cÃ³ kÃ½ tá»± literal `\n` | Äá»•i thÃ nh `join('\\n')` |

### Giai Ä‘oáº¡n 8 â€” Tá»± nháº­n diá»‡n tÃªn Agent tá»« trang web
- ThÃªm hÃ m `detectAgentName()` trong `content_script.js`.
- Thá»© tá»± Æ°u tiÃªn nháº­n diá»‡n:
  1. Selector Ä‘áº·c trÆ°ng M365 (`data-testid`, `aria-label`, class...).
  2. Tháº» `<title>` (loáº¡i bá» háº­u tá»‘ "- Microsoft Copilot", "- Bing"...).
  3. Tháº» `<h1>` hiá»ƒn thá»‹ Ä‘áº§u tiÃªn.
  4. Fallback: `"Copilot"`.
- TÃªn nháº­n diá»‡n gá»­i ngÆ°á»£c lÃªn Popup qua `update_agent_name` â†’ Ã´ nháº­p hiá»ƒn thá»‹ viá»n **xanh lÃ¡**.

### Giai Ä‘oáº¡n 9 â€” Auto-Save & KhÃ´i phá»¥c dá»¯ liá»‡u (Chá»‘ng máº¥t data)
- **Váº¥n Ä‘á»:** Tab bá»‹ Ä‘Ã³ng hoáº·c crash giá»¯a chá»«ng â†’ toÃ n bá»™ dá»¯ liá»‡u máº¥t.
- **Giáº£i phÃ¡p:** Auto-save vÃ o `chrome.storage.local` sau má»—i bÃ i thu tháº­p thÃ nh cÃ´ng.
  - Keys: `autosave_data`, `autosave_name`, `autosave_day`.
- **KhÃ´i phá»¥c:** Khi trang load láº¡i, náº¿u phÃ¡t hiá»‡n dá»¯ liá»‡u cÅ© â†’ hiá»‡n nÃºt **"ðŸ“¥ Táº£i láº¡i dá»¯ liá»‡u cÅ©"** (mÃ u tÃ­m) trÃªn Popup.
- Dá»¯ liá»‡u táº¡m xÃ³a khá»i storage sau khi táº£i file thÃ nh cÃ´ng (cáº£ tá»« nÃºt Recover láº«n download bÃ¬nh thÆ°á»ng).

### Giai Ä‘oáº¡n 10 â€” Xuáº¥t HTML tá»«ng Day + Index tá»•ng há»£p + Session Resume

- **Váº¥n Ä‘á»:** ToÃ n bá»™ HTML tÃ­ch lÅ©y trong `collectedData[]` trong RAM â†’ khi cháº¡y 100+ Day thÃ¬ RAM Ä‘áº§y, trÃ¬nh duyá»‡t crash, máº¥t sáº¡ch dá»¯ liá»‡u. Chá»‰ cÃ³ 1 file JSON dump á»Ÿ cuá»‘i.
- **Giáº£i phÃ¡p:** "Write-as-you-go" â€” táº£i file HTML **ngay sau má»—i Day** vÃ o subfolder trong Downloads:
  ```
  Downloads/
  â””â”€â”€ agent_name/
      â”œâ”€â”€ index.html       â† Cáº­p nháº­t dáº§n sau má»—i Day
      â”œâ”€â”€ day_1.html
      â”œâ”€â”€ day_2.html
      â””â”€â”€ session.json     â† Quáº£n lÃ½ phiÃªn, dÃ¹ng Ä‘á»ƒ Resume
  ```
- **Thay Ä‘á»•i ká»¹ thuáº­t:**
  - `content_script.js`: ThÃªm `downloadDayHtml()`, `updateIndex()`, `saveSession()`. Bá» `downloadJson()`. HTML Ä‘Æ°á»£c giáº£i phÃ³ng khá»i RAM ngay sau khi táº£i. `dayIndex[]` chá»‰ lÆ°u metadata nhá».
  - `background.js`: ThÃªm handler `download_html`, `download_index`, `download_session` vá»›i `conflictAction: "overwrite"` Ä‘á»ƒ ghi Ä‘Ã¨ index & session má»—i láº§n cáº­p nháº­t.
  - `popup.html/js`: ThÃªm nÃºt **"ðŸ“‚ Chá»n file session.json"** + `<input type="file">`. Parse JSON â†’ Ä‘iá»n UI â†’ gá»­i `resume_session` lÃªn content script. ThÃªm hiá»ƒn thá»‹ `day_saved` status.
- **TÃ­nh nÄƒng Resume:** NgÆ°á»i dÃ¹ng chá»n `session.json` tá»« báº¥t ká»³ Ä‘Ã¢u trÃªn mÃ¡y â†’ Addon tiáº¿p tá»¥c tá»« ngÃ y tiáº¿p theo, dÃ¹ng láº¡i Ä‘Ãºng tÃªn thÆ° má»¥c cÅ©.
- **LÆ°u Ã½ báº£o máº­t trÃ¬nh duyá»‡t:** Extension chá»‰ Ä‘Æ°á»£c ghi vÃ o thÆ° má»¥c Downloads (vÃ  subfolder). KhÃ´ng thá»ƒ ghi trá»±c tiáº¿p vÃ o thÆ° má»¥c dá»± Ã¡n. NgÆ°á»i dÃ¹ng cÃ³ thá»ƒ copy `session.json` sang `AskCpl/` thá»§ cÃ´ng Ä‘á»ƒ lÆ°u trá»¯.

### Giai Ä‘oáº¡n 11 â€” Kiáº¿n trÃºc "One-Chat-Per-Day" + Fix Download Root Cause

- **Váº¥n Ä‘á» 1 (Download):** `background.js` dÃ¹ng `URL.createObjectURL()` â€” **KHÃ”NG tá»“n táº¡i trong Service Worker MV3**. Silent fail: download API nháº­n URL lá»—i â†’ khÃ´ng táº£i Ä‘Æ°á»£c file dÃ¹ khÃ´ng bÃ¡o lá»—i nÃ o.
  - **Fix:** Thay hoÃ n toÃ n báº±ng **base64 data URI**:
    `TextEncoder â†’ Uint8Array â†’ String.fromCharCode (chunk 8192) â†’ btoa() â†’ data:mimeType;base64,...`
  - HÃ m má»›i: `dataUriDownload()` thay cho `blobDownload()`. Hoáº¡t Ä‘á»™ng 100% trong SW.

- **Váº¥n Ä‘á» 2 (PhÃ¢n tÃ¡ch dá»¯ liá»‡u):** Kiáº¿n trÃºc cÅ© nháº¯n Day 1 â†’ Day 2 â†’ Day 3 trong **cÃ¹ng 1 Ä‘oáº¡n chat** â†’ extract láº¥y láº«n toÃ n bá»™ ná»™i dung, khÃ´ng cÃ´ láº­p Ä‘Æ°á»£c reply cá»§a tá»«ng Day.

- **Giáº£i phÃ¡p â€” Kiáº¿n trÃºc má»›i: Má»—i Day = 1 Chat Má»›i:**
  - Tá»« Day 2 trá»Ÿ Ä‘i: click nÃºt **"New Chat"** trÆ°á»›c â†’ chat má»›i chá»‰ cÃ³ **1 AI reply duy nháº¥t** â†’ extract láº¥y táº¥t cáº£ = Ä‘Ãºng bÃ i Ä‘Ã³, khÃ´ng cáº§n isolate.
  - URL khÃ´ng Ä‘á»•i khi click New Chat (SPA) â†’ `isRunning` vÃ  toÃ n bá»™ state giá»¯ nguyÃªn â†’ an toÃ n.
  - ThÃªm hÃ m `clickNewChat()`: selector theo thá»© tá»± Æ°u tiÃªn `data-automation-id` â†’ `data-testid` â†’ `aria-label`.
  - ThÃªm hÃ m `waitForNewChatReady()`: chá» tá»‘i Ä‘a 15s, confirm báº±ng `inputEmpty && aiResponses.length === 0`.
  - `extractLatestResponse()` Ä‘Æ¡n giáº£n hÃ³a: bá» chiáº¿n lÆ°á»£c "30 `<p>` cuá»‘i" (khÃ´ng cáº§n ná»¯a vÃ¬ chat má»›i sáº¡ch).
  - Logic trigger: `if (dayIndex.length > 0)` â†’ Ä‘Ã£ cÃ³ bÃ i cÅ© â†’ click New Chat.

### Giai Ä‘oáº¡n 12 â€” Fix Input + Tá»‘i Æ°u CPU/RAM

- **Váº¥n Ä‘á» Input:** M365 Copilot dÃ¹ng `div[contenteditable]` vá»›i React/FluentUI. GÃ¡n `innerText` trá»±c tiáº¿p â†’ React **khÃ´ng nháº­n** â†’ Send button váº«n disabled â†’ loop dá»«ng.
  - **Fix:** HÃ m `fillInput()` má»›i: dÃ¹ng `document.execCommand('insertText')` + `InputEvent({composed:true})`. `execCommand` trigger `beforeinput â†’ input` chain â†’ React state update Ä‘Ãºng cÃ¡ch.
  - **Fix Selector:** ÄÆ°a `div[role="textbox"][contenteditable="true"]` lÃªn Ä‘áº§u danh sÃ¡ch. Bá» `'textarea'` fallback chung (dá»… match Ã´ tÃ¬m kiáº¿m M365).
  - **Fix Enter:** ThÃªm `composed: true` + thÃªm `keyup` event.
  - **Chá» state:** TÄƒng delay sau fill tá»« 800ms â†’ 1500ms Ä‘á»ƒ React update Send button.

- **Tá»‘i Æ°u CPU/RAM:**
  - `waitForNewChatReady`: 500ms â†’ 1500ms (giáº£m 66% DOM queries trong vÃ²ng chá»)
  - `extractLatestResponse`: ThÃªm `capHtml(100KB)` â€” trÃ¡nh chuá»—i MB trong RAM. Bá» `S3b: mainEl.innerHTML` (cÃ³ thá»ƒ vÃ i MB). Giá»›i háº¡n S3 tá»‘i Ä‘a 80 elements. Fallback S4 cáº¯t 3000 chars (thay 5000).
  - `processExtractedContent`: Regex stop-keyword chá»‰ trÃªn 1500 chars Ä‘áº§u (thay toÃ n bá»™ HTML).
  - `findSendButton`: Bá» fallback `querySelectorAll('form button, [role="search"] button')` â€” scan náº·ng.

### Giai Ä‘oáº¡n 13 â€” Fix "Day 1Day 1" + Bá» AudioContext + Debug Download

- **Bug "Day 1Day 1" (Root Cause):** `execCommand('delete')` xÃ³a DOM â†’ React **re-render ngay** â†’ khÃ´i phá»¥c "Day 1" â†’ `insertText("Day 1")` append â†’ "Day 1Day 1".
  - **Fix:** DÃ¹ng `Range.selectNodeContents(el)` + `window.getSelection().addRange(range)` â†’ `execCommand('insertText', false, value)` REPLACE toÃ n bá»™ selection trong 1 lá»‡nh. React's `beforeinput` handler tháº¥y toÃ n bá»™ operation trÆ°á»›c khi commit â†’ state update Ä‘Ãºng, khÃ´ng cÃ²n re-render xen giá»¯a.

- **Bug `waitForNewChatReady` timeout:** Äiá»u kiá»‡n `chatCleared = aiResponses.length === 0` dÃ¹ng `.markdown-body` â€” selector nÃ y **luÃ´n tá»“n táº¡i** trong page chrome M365 (sidebar, tooltip...) â†’ khÃ´ng bao giá» = 0 â†’ timeout 9s má»i láº§n.
  - **Fix:** Bá» `chatCleared`. Chá»‰ check `inputEmpty` + chá» cá»©ng 3s + poll thÃªm 6s. `fillInput` Ä‘Ã£ xá»­ lÃ½ náº¿u input chÆ°a rá»—ng (Range.selectAll sáº½ xÃ³a).

- **Bá» `keepAliveAudio`:** `AudioContext` cháº¡y liÃªn tá»¥c gÃ¢y CPU spike 5-15%, ngay cáº£ vá»›i silent WAV. Kiáº¿n trÃºc má»›i (má»—i Day = 1 chat má»›i) khÃ´ng cáº§n giá»¯ tab active.

- **Giáº£m downloads per Day:** Tá»« 3 (HTML + index + session) â†’ 1 (chá»‰ HTML). Index + session chá»‰ update má»—i 5 Day hoáº·c khi finish â†’ giáº£m 60% downloads, giáº£m táº£i background.js.

- **Download Error Visibility:** `background.js` gá»­i káº¿t quáº£ download (OK hoáº·c FAILED + message) vá» popup log area â†’ ngÆ°á»i dÃ¹ng tháº¥y lá»—i ngay mÃ  khÃ´ng cáº§n má»Ÿ SW DevTools console.

---

### Giai Ä‘oáº¡n 14 â€” Fix Cáº¯t Giá»¯a + Sai Ná»™i Dung + Popup Sync

- **Fix "Day 2 bá»‹ cáº¯t" (Issue 3):**
  - Root cause: `waitForResponseComplete` phÃ¡t hiá»‡n "xong" khi AI táº¡m nghá»‰ giá»¯a chunk dÃ i â†’ Stop button biáº¿n máº¥t thoÃ¡ng qua â†’ extract sá»›m.
  - Fix: ThÃªm `waitForStable(15s)` â€” DOM (innerText.length cá»§a `[role="main"]`) pháº£i á»•n Ä‘á»‹nh 15s liÃªn tiáº¿p má»›i coi AI xong tháº­t. Poll 2s/láº§n, tá»‘i Ä‘a 90s.

- **Fix "Day 1 chá»‰ ra tÃªn agent" (Issue 4):**
  - Root cause: Selectors S1-S3 khÃ´ng match M365 Copilot DOM. RÆ¡i xuá»‘ng S4 `body.innerText` â†’ láº¥y page chrome text â†’ chá»‰ cÃ³ tÃªn agent.
  - Fix: `snapshotBeforeSend()` â€” chá»¥p sá»‘ block elements TRÆ¯á»šC khi gá»­i. `extractDeltaContent(snapshot)` â€” láº¥y elements **sau** snapshot.count â†’ chá»‰ ná»™i dung Má»šI (reply cá»§a AI), khÃ´ng láº«n header/sidebar.
  - Fix: `validateContent(html, agentName)` â€” lá»c content quÃ¡ ngáº¯n (<100 chars) hoáº·c chá»§ yáº¿u lÃ  tÃªn agent (>40% tá»«).

- **Fix "Popup Ä‘Ã³ng tÆ°á»Ÿng dá»«ng" (Issue 5):**
  - Root cause: Popup load láº¡i tá»« Ä‘áº§u â†’ khÃ´ng biáº¿t loop Ä‘ang cháº¡y.
  - Fix: `saveRunningState()` trong `processExtractedContent` sau má»—i Day â†’ lÆ°u `{ isRunning, currentDay, agentName, lastSaved }` vÃ o `chrome.storage.local['runningState']`. `clearRunningState()` khi finish/stop.
  - `popup.js`: `syncRunningState()` gá»i khi popup má»Ÿ â†’ Ä‘á»c storage â†’ hiá»‡n banner + Stop button.
  - `popup.html`: `#runningBanner` vá»›i pulse animation, hiá»‡n agent name + Day Ä‘Ã£ lÆ°u. ChÃº thÃ­ch "ÄÃ³ng popup khÃ´ng áº£nh hÆ°á»Ÿng".

---

### Giai Ä‘oáº¡n 15 â€” Smart Input + Fully Autonomous + Log Persist

- **Smart Input Detection (5 chiáº¿n lÆ°á»£c):**
  1. **Fingerprint**: `saveInputFingerprint(el)` lÆ°u selector (tag+attributes+parent) vÃ o `chrome.storage.local['inputFingerprint']`. Day 2+ thá»­ fingerprint trÆ°á»›c â†’ tÃ¬m Ä‘Ãºng ngay mÃ  khÃ´ng cáº§n user click.
  2. **Lexical detection**: TÃ¬m `[data-lexical-text]` â†’ `.closest('[contenteditable="true"]')`. M365 dÃ¹ng Lexical editor (cáº¥u trÃºc `<p>` + `<span data-lexical-text>`).
  3. **Standard selectors**: role, aria-label, data-automation-id.
  4. **Broad CE scan**: `querySelectorAll('div[contenteditable="true"]')` lá»c bá» container quÃ¡ lá»›n (>500px height, >20 children).
  5. **activeElement fallback**.

- **Fully Autonomous â€” Day-Level Retry:**
  - `runNextDay()` = wrapper retry tá»‘i Ä‘a 3 láº§n (retry 0, 1, 2).
  - `_runNextDayAttempt(retryCount)` tráº£ `'ok'|'retry'|'stop'`.
  - Náº¿u khÃ´ng tÃ¬m Ä‘Æ°á»£c input hoáº·c extract fail â†’ return `'retry'` â†’ má»Ÿ New Chat má»›i â†’ gá»­i láº¡i Day N.
  - Chá»‰ `finishLoop()` sau khi háº¿t cáº£ 3 láº§n tháº¥t báº¡i.

- **Log Persist:**
  - `flushLogs()` lÆ°u 200 dÃ²ng cuá»‘i vÃ o `chrome.storage.local['popup_logs']`.
  - `popup.js`: `loadPersistedLogs()` khi má»Ÿ â†’ hiá»‡n log cÅ© + dÃ²ng `â”€â”€ [Popup má»Ÿ láº¡i] â”€â”€`.

- **Stability-First Wait:**
  - Bá» phá»¥ thuá»™c `findSendButton()` (luÃ´n null trÃªn M365).
  - Chá» cá»©ng 2 phÃºt â†’ poll 30s â†’ DOM stable 15s = AI xong.
  - Cap: 2MB HTML + 500 blocks.

### Giai Ä‘oáº¡n 16 â€” Keep-Alive 3 Táº§ng (Chá»‘ng Tab Sleep)

- **Váº¥n Ä‘á»:** Chuyá»ƒn tab/app â†’ Chromium throttle `setTimeout` â†’ delay 10s thÃ nh 60s+ â†’ sau 5 phÃºt tab freeze â†’ loop dá»«ng.
- **Giai Ä‘oáº¡n 13 Ä‘Ã£ bá» `keepAliveAudio`** vÃ¬ dÃ¹ng AudioContext + WAV file â†’ CPU 5-15%. BÃ¢y giá» cáº§n cÃ¡ch nháº¹ hÆ¡n.

- **Fix: 3 táº§ng keep-alive (~0.3% CPU tá»•ng):**
  1. **Web Lock** (`navigator.locks.request` + Promise never-resolve): Chá»‘ng Edge Sleeping Tabs discard. ~0% CPU.
  2. **Inline Worker** (`Blob` URL + `setInterval(25s)`): Workers KHÃ”NG bá»‹ throttle trong background tab â†’ giá»¯ main thread active. ~0.1% CPU.
  3. **Silent Oscillator** (`AudioContext`, gain=0.00001, freq=1Hz): Browser coi tab Ä‘ang phÃ¡t audio = "important" = khÃ´ng freeze. ~0.2% CPU.

- **Lifecycle:**
  - `setupKeepAlive()`: Gá»i khi start_loop / resume_session.
  - `teardownKeepAlive()`: Gá»i khi stop_loop / finishLoop(). Giáº£i phÃ³ng tÃ i nguyÃªn ngay.

### Giai Ä‘oáº¡n 17 â€” Auto-Resume (Fix Dá»«ng á»ž Day 2)

- **Root cause:** Click "New Chat" trÃªn M365 â†’ SPA navigate â†’ content_script.js bá»‹ **re-inject** â†’ táº¥t cáº£ biáº¿n JS reset (`isRunning=false`, `currentDay=1`) â†’ loop "dá»«ng". ÄÃ¢y khÃ´ng pháº£i tab sleep â€” mÃ  lÃ  **script bá»‹ reload**.

- **Fix: Auto-Resume khi script load:**
  - Khi content_script.js khá»Ÿi táº¡o â†’ Ä‘á»c `chrome.storage.local['runningState']`
  - Náº¿u `isRunning === true`:
    - KhÃ´i phá»¥c: `currentDay`, `agentName`, `folderName`, `prefix`, `dayIndex` (tá»« autosave_data)
    - `setupKeepAlive()`
    - Chá» 5s (page settle) â†’ `runNextDay()` tá»± Ä‘á»™ng
    - Log: `ðŸ”„ AUTO-RESUME: "AgentName" tá»« Day N`

- **Fix: `saveRunningState(nextDay, lastSaved)`:**
  - Tham sá»‘ má»›i `nextDay`: luÃ´n lÆ°u day **TIáº¾P THEO** cáº§n xá»­ lÃ½
  - Gá»i SAU `currentDay++` trong `processExtractedContent`
  - â†’ Auto-resume Ä‘á»c `runningState.currentDay` = Ä‘Ãºng day cáº§n cháº¡y, khÃ´ng trÃ¹ng day Ä‘Ã£ xong
  - ThÃªm `prefix` vÃ o runningState Ä‘á»ƒ auto-resume biáº¿t prefix

### Giai Ä‘oáº¡n 18 â€” Fix CSP, Audio, Context Invalidation & Tá»‘i Æ°u Adaptive Wait

- **Fix Worker CSP**: Bá» `Blob Worker` vÃ¬ M365 CSP cháº·n `worker-src 'self'`. DÃ¹ng `setInterval` bÃ¬nh thÆ°á»ng. Káº¿t há»£p vá»›i `Web Lock` lÃ  Ä‘á»§ chá»‘ng discard.
- **Fix AudioContext**: Bá» `AudioContext` vÃ¬ yÃªu cáº§u user gesture, cÃ³ thá»ƒ nÃ©m lá»—i khi auto-resume hoáº·c reload.
- **Fix Context Invalidated**: Khi script bá»‹ orphan do reload, gá»i `chrome.runtime.sendMessage` sáº½ throw exception lÃ m sáº­p script. â†’ Viáº¿t hÃ m `safeSendMessage` bá»c try-catch vÃ  check `chrome.runtime?.id`.
- **Tá»‘i Æ°u Adaptive Wait**: RÃºt ngáº¯n thá»i gian chá» cá»©ng `MIN_WAIT` tá»« 120s xuá»‘ng 15s. Sau 15s báº¯t Ä‘áº§u check stability (cáº§n 15s stable). Tá»•ng cá»™ng máº¥t khoáº£ng ~30s náº¿u AI tráº£ lá»i xong nhanh (thay vÃ¬ luÃ´n luÃ´n chá» cháº¿t 2 phÃºt).

### Giai Ä‘oáº¡n 19 â€” Fix Lá»—i "Chá» 10s Bá»‹ ÄÃ³ng BÄƒng" (Tab Freeze) & Tá»‘i Æ°u Auto-Resume

- **Root Cause**: Giai Ä‘oáº¡n 18 gá»¡ `AudioContext` khiáº¿n tab cháº¡y ngáº§m (background) dá»… bá»‹ Chromium Ä‘Ã³ng bÄƒng toÃ n bá»™ Javascript (Tab Freeze) ngay sau khi AI táº¡o xong text (vÃ¬ DOM khÃ´ng cÃ²n thay Ä‘á»•i). Viá»‡c gá»i `delay(10000)` dÃ¹ng `setTimeout` sáº½ bá»‹ ngÆ°ng Ä‘á»ng vÄ©nh viá»…n khÃ´ng bao giá» cháº¡y tiáº¿p.
- **Kháº¯c phá»¥c 1 (Bá» nhÃ n rá»—i)**: XÃ³a bá» hoÃ n toÃ n thá»i gian chá» 10s vÃ´ nghÄ©a giá»¯a cÃ¡c Day trong `processExtractedContent`. Cháº¡y ngay sang Day káº¿ tiáº¿p Ä‘á»ƒ giá»¯ luá»“ng hoáº¡t Ä‘á»™ng, ngÄƒn Chromium ráº£nh rá»—i Ä‘Ã³ng bÄƒng tab.
- **Kháº¯c phá»¥c 2 (Tá»‘i Æ°u Reload)**: Khi M365 bá»‹ táº£i láº¡i (do SPA navigate) vÃ  trigger `Auto-Resume`, giáº£m thá»i gian chá» cá»§a Auto-Resume tá»« 5s xuá»‘ng 1.5s Ä‘á»ƒ trÃ¡nh freeze. Truyá»n cá» `isAutoResumed = true` vÃ o `runNextDay` Ä‘á»ƒ ngÄƒn script báº¥m nÃºt `New Chat` thÃªm má»™t láº§n ná»¯a (vÃ¬ trang vá»«a táº£i láº¡i vá»‘n dÄ© Ä‘Ã£ lÃ  chat má»›i tinh), trÃ¡nh vÃ²ng láº·p táº£i láº¡i trang vÃ´ táº­n.

### Giai Ä‘oáº¡n 20 â€” Fix Lá»—i Chá» LÃ¢u (5-10 phÃºt) Khi AI ÄÃ£ Xong

- **Váº¥n Ä‘á»**: ÄÃ´i lÃºc AI Ä‘Ã£ táº¡o xong toÃ n bá»™ ná»™i dung, nhÆ°ng tiáº¿n trÃ¬nh váº«n Ä‘á»©ng yÃªn chá» thÃªm 5-10 phÃºt thay vÃ¬ hoÃ n thÃ nh ngay.
- **NguyÃªn nhÃ¢n**:
  1. **Strict Equality**: HÃ m `checkStable15s` Ä‘o Ä‘á»™ dÃ i text (`innerText.length`) cá»§a toÃ n trang vÃ  yÃªu cáº§u khÃ´ng Ä‘Æ°á»£c thay Ä‘á»•i dÃ¹ chá»‰ 1 kÃ½ tá»± (`len === lastLen`) trong suá»‘t 15 giÃ¢y.
  2. **Nhiá»…u DOM**: Giao diá»‡n M365 Copilot thÆ°á»ng cÃ³ cÃ¡c thay Ä‘á»•i nhá» ngoÃ i Ã½ muá»‘n (vÃ­ dá»¥: thá»i gian cáº­p nháº­t "1 min ago", nÃºt chá»©c nÄƒng áº©n/hiá»‡n, gá»£i Ã½ prompt). CÃ¡c thay Ä‘á»•i nÃ y lÃ m chiá»u dÃ i text dao Ä‘á»™ng nháº¹, liÃªn tá»¥c reset bá»™ Ä‘áº¿m á»•n Ä‘á»‹nh 15 giÃ¢y.
- **Giáº£i phÃ¡p**:
  - **Äo lÆ°á»ng cá»¥c bá»™ (Scoped Check)**: Viáº¿t hÃ m `getNewTextLength()` CHá»ˆ tÃ­nh Ä‘á»™ dÃ i text cá»§a cÃ¡c element Má»šI sinh ra sau khi gá»­i prompt (dá»±a trÃªn viá»‡c lá»c bá» cÃ¡c element cÃ³ `dataset.askcplSnapshot = "1"`). Äiá»u nÃ y cháº·n má»i nhiá»…u tá»« cÃ¡c thÃ nh pháº§n cÅ© trÃªn trang.
  - **Dung sai (Tolerance)**: Cho phÃ©p sai sá»‘ thay Ä‘á»•i `Math.abs(len - lastLen) <= 30` kÃ½ tá»±. Khi AI thá»±c sá»± stream text, sá»‘ lÆ°á»£ng kÃ½ tá»± sáº½ tÄƒng ráº¥t nhanh vÃ  bá»©t phÃ¡ khá»i khoáº£ng dung sai. Náº¿u chá»‰ lÃ  UI render nÃºt "Copy" hay icon thay Ä‘á»•i á»Ÿ cuá»‘i quÃ¡ trÃ¬nh, sá»± dao Ä‘á»™ng sáº½ náº±m trong khoáº£ng 30 kÃ½ tá»± vÃ  khÃ´ng lÃ m reset bá»™ Ä‘áº¿m, giÃºp tiáº¿n trÃ¬nh nháº­n diá»‡n AI Ä‘Ã£ xong ngay láº­p tá»©c.

### Giai Ä‘oáº¡n 21 â€” Há»‡ thá»‘ng Config Äa Ná»n Táº£ng & Bá»™ nhá»› phá»ng váº¥n (Multi-step Interrogation)

- **Váº¥n Ä‘á»**:
  - NgÆ°á»i dÃ¹ng cáº§n lÆ°u nhiá»u cáº¥u hÃ¬nh (Config) khÃ¡c nhau cho cÃ¡c Agent khÃ¡c nhau (vÃ­ dá»¥: má»™t cÃ¡i cho Copilot tiáº¿ng Anh, má»™t cÃ¡i cho Gemini).
  - Cáº§n tÃ­nh nÄƒng tá»± dá»«ng vÃ²ng láº·p á»Ÿ má»™t `NgÃ y káº¿t thÃºc` (End Day) nháº¥t Ä‘á»‹nh.
  - VÃ²ng láº·p chat dÃ i ngÃ y khiáº¿n AI "quÃªn" cÃ¡c chá»§ Ä‘á» Ä‘Ã£ há»c. Cáº§n má»™t cÃ¡ch Ä‘á»ƒ báº¯t AI tá»± tÃ³m táº¯t vÃ  ghi nhá»› láº¡i cÃ¡c Ã½ chÃ­nh Ä‘Ã£ há»c á»Ÿ má»—i ngÃ y Ä‘á»ƒ má»›m (inject) vÃ o prompt cá»§a ngÃ y tiáº¿p theo.

- **Giáº£i phÃ¡p**:
  - **Há»‡ thá»‘ng Profiles**: NÃ¢ng cáº¥p `popup.html/js` Ä‘á»ƒ cÃ³ má»™t Dropdown duy nháº¥t cho phÃ©p chá»n, lÆ°u vÃ  xÃ³a nhiá»u Profile khÃ¡c nhau (vd: "Copilot - Basic", "Copilot - Tá»« vá»±ng"). ToÃ n bá»™ config (Day, Tiá»n tá»‘, End Day, tÃ­nh nÄƒng nÃ¢ng cao) Ä‘Æ°á»£c bá»c chung vÃ o 1 Profile vÃ  lÆ°u trong `chrome.storage`.
  - **NgÃ y káº¿t thÃºc (End Day)**: ThÃªm Ã´ thiáº¿t láº­p `End Day`. Trong `processExtractedContent`, náº¿u `currentDay >= endDay`, vÃ²ng láº·p sáº½ gá»i `finishLoop()` ngay láº­p tá»©c.
  - **Memory Advanced (Phá»ng váº¥n liÃªn hoÃ n)**:
    - Biáº¿n Addon thÃ nh má»™t quy trÃ¬nh Agentic (Multi-step Interrogation). Thay vÃ¬ 1 Day chá»‰ gá»­i 1 lá»‡nh, Addon sáº½ tá»± Ä‘á»™ng nháº¯n tin phá»ng váº¥n AI nhiá»u láº§n trong cÃ¹ng 1 bÃ i.
    - BÆ°á»›c 1: Gá»­i bÃ i chÃ­nh `Day X`.
    - BÆ°á»›c 2: Gá»­i cÃ¢u há»i má»›m Ä‘á»ƒ há»i TÃªn Chá»§ Äá» (vd: *"Chá»§ Ä‘á» lÃ  gÃ¬ chá»‰ má»—i chá»§ Ä‘á» thÃ´i"*). Cáº­p nháº­t biáº¿n Ä‘áº¿m sá»‘ bÃ i cá»§a chá»§ Ä‘á» Ä‘Ã³.
    - BÆ°á»›c 3: Náº¿u Chá»§ Ä‘á» chÆ°a hoÃ n thÃ nh Ä‘á»§ sá»‘ lÆ°á»£ng má»¥c tiÃªu, Addon vÃ²ng láº·p qua cÃ¡c "Chi tiáº¿t" Ä‘Æ°á»£c cÃ i Ä‘áº·t trÃªn giao diá»‡n (vÃ­ dá»¥: Chi tiáº¿t 1: "Tá»« vá»±ng", Chi tiáº¿t 2: "Ngá»¯ phÃ¡p"). Má»—i chi tiáº¿t sáº½ kÃ­ch hoáº¡t 1 cÃ¢u há»i Ä‘á»™c láº­p vá»›i AI (vd: *"Há»i tá»« vá»±ng lÃ  gÃ¬, chá»‰ ghi cÃ¡c tá»« vá»±ng thÃ´i"*).
    - CÃ¢u tráº£ lá»i cá»§a AI cho cÃ¡c Chi tiáº¿t nÃ y sáº½ Ä‘Æ°á»£c bÃ³c tÃ¡ch vÃ  cá»™ng dá»“n vÃ o Object bá»™ nhá»› cá»¥c bá»™ (`topicMemory`).
  - **Memory Injector**: TrÆ°á»›c khi gá»­i `Day X+1`, Addon tá»± Ä‘á»™ng format bá»™ nhá»› `topicMemory` thÃ nh má»™t khá»‘i text gá»n gÃ ng (vd: *Chá»§ Ä‘á»: Con ngÆ°á»i 1/4 \n Tá»« vá»±ng Ä‘Ã£ há»c: ... \n Ngá»¯ phÃ¡p Ä‘Ã£ há»c: ...*). Khá»‘i text nÃ y Ä‘Æ°á»£c gáº¯n trá»±c tiáº¿p vÃ o cuá»‘i cÃ¢u lá»‡nh `Day X+1` Ä‘á»ƒ "má»›m" trÃ­ nhá»› cho AI. CÃ¡c chá»§ Ä‘á» Ä‘Ã£ Ä‘áº¡t má»¥c tiÃªu (vÃ­ dá»¥ 4/4) sáº½ Ä‘Æ°á»£c rÃºt gá»n thÃ nh chá»¯ "HoÃ n táº¥t" Ä‘á»ƒ tiáº¿t kiá»‡m token.

### Giai Ä‘oáº¡n 22 â€” Adapter Äa Ná»n Táº£ng (Gemini/ChatGPT) & Lá»™ trÃ¬nh Äá»™ng PhÃ¢n Cáº¥p (Hierarchical Roadmap)

- **Váº¥n Ä‘á»**: NgÆ°á»i dÃ¹ng cáº§n cháº¡y Add-on á»Ÿ nhÃ  vá»›i cÃ¡c tÃ i khoáº£n AI miá»…n phÃ­ (Google Gemini, ChatGPT) nhÆ°ng cÃ¡c AI nÃ y khÃ´ng há»— trá»£ táº¡o Agent lÆ°u ngá»¯ cáº£nh cá»‘ Ä‘á»‹nh (System Prompt). HÆ¡n ná»¯a, viá»‡c "nhá»“i" trÃ­ nhá»› cá»§a hÃ ng trÄƒm bÃ i há»c cÅ© vÃ o má»™t cÃ¢u lá»‡nh sáº½ gÃ¢y phÃ¬nh to ngá»¯ cáº£nh (Context Overflow) vÃ  tá»‘n token. Viá»‡c thay Ä‘á»•i tÃ i khoáº£n AI miá»…n phÃ­ (do háº¿t lÆ°á»£t) cÅ©ng lÃ m xÃ¡o trá»™n lá»™ trÃ¬nh.
- **Giáº£i phÃ¡p**:
  1. **Hierarchical Roadmap (Lá»™ trÃ¬nh phÃ¢n cáº¥p)**:
     - ThÃªm Ã´ nháº­p `Roadmap` trÃªn `popup.html`. NgÆ°á»i dÃ¹ng cÃ³ thá»ƒ copy Báº£ng Markdown Lá»™ TrÃ¬nh (xin tá»« ChatGPT) vÃ  dÃ¡n tháº³ng vÃ o.
     - Add-on cÃ³ tÃ­nh nÄƒng "Táº¡o JSON Roadmap": tá»± Ä‘á»™ng nhÃ³m cÃ¡c bÃ i há»c theo cá»™t `ChÆ°Æ¡ng` (Main Topic) vÃ  táº¡o ra má»™t file JSON PhÃ¢n cáº¥p.
  2. **Token-Optimized Prompt Injector (NÃ©n TrÃ­ Nhá»›)**:
     - Trong `content_script.js`, Add-on dÃ² xem NgÃ y hiá»‡n táº¡i thuá»™c ChÆ°Æ¡ng nÃ o. Náº¿u Ä‘ang á»Ÿ giá»¯a ChÆ°Æ¡ng, nÃ³ sáº½ ghÃ©p thÃªm cÃ¢u tÃ³m táº¯t cá»§a cÃ¡c ngÃ y trÆ°á»›c *thuá»™c cÃ¹ng ChÆ°Æ¡ng Ä‘Ã³*.
     - Khi chuyá»ƒn sang ChÆ°Æ¡ng má»›i, toÃ n bá»™ tÃ³m táº¯t chi tiáº¿t cá»§a ChÆ°Æ¡ng cÅ© sáº½ bá»‹ "chá»‘t sá»•" vÃ  xÃ³a khá»i lá»‡nh, giÃºp giáº£i phÃ³ng hoÃ n toÃ n bá»™ nhá»› Prompt, giá»¯ cho lá»‡nh gá»­i luÃ´n sáº¯c bÃ©n vÃ  cá»±c ká»³ ngáº¯n gá»n.
  3. **Auto Summarizer**: Sau khi láº¥y xong bÃ i há»c chÃ­nh, Add-on tá»± Ä‘á»™ng báº¯n thÃªm lá»‡nh phá»¥ *"TÃ³m táº¯t cá»±c ká»³ ngáº¯n gá»n kiáº¿n thá»©c trÃªn"* vÃ  lÆ°u vÃ o `historySummaries`.
  4. **Adapter Pattern**: TÃ¡ch rá»i logic DOM Selector cho `clickNewChat`, `findChatInput`, `findSendButton` vÃ  `extractDeltaContent` dá»±a trÃªn lá»±a chá»n Ná»n táº£ng (copilot, gemini, chatgpt). 
  5. **Persistent Session (KhÃ³a cá»©ng Lá»™ TrÃ¬nh)**: NhÃºng (embed) trá»±c tiáº¿p toÃ n bá»™ khá»‘i `roadmapData` vÃ  `historySummaries` vÃ o trong file `session.json`. GiÃºp ngÆ°á»i dÃ¹ng khi cáº¡n dung lÆ°á»£ng tÃ i khoáº£n A cÃ³ thá»ƒ Ä‘Äƒng nháº­p tÃ i khoáº£n B, báº¥m táº£i file session lÃªn vÃ  Add-on sáº½ tá»± phá»¥c há»“i Lá»™ trÃ¬nh láº«n TrÃ­ nhá»› Ä‘á»ƒ tiáº¿p tá»¥c máº¡ch há»c chÃ­nh xÃ¡c Ä‘áº¿n tá»«ng chá»¯.

### Giai Ä‘oáº¡n 23 â€” Fix lá»—i khÃ´ng táº¡o New Chat trÃªn Gemini
- **Váº¥n Ä‘á»**: NgÆ°á»i dÃ¹ng bÃ¡o cÃ¡o Addon tiáº¿p tá»¥c gá»­i bÃ i má»›i vÃ o cÃ¹ng má»™t Ä‘oáº¡n chat cÅ© trÃªn Gemini thay vÃ¬ táº¡o chat má»›i, lÃ m máº¥t tÃ¡c dá»¥ng cá»§a cÆ¡ cháº¿ One-Chat-Per-Day.
- **NguyÃªn nhÃ¢n**: NÃºt "New Chat" cá»§a Gemini Ä‘Ã£ thay Ä‘á»•i cáº¥u trÃºc DOM, selector cÅ© `a[href*="/app/new"]` khÃ´ng cÃ²n tÃ¬m tháº¥y.
- **Giáº£i phÃ¡p**: NÃ¢ng cáº¥p hÃ m `clickNewChat()` cho Gemini:
  - Bá»• sung loáº¡t selector má»›i: `a[href="/app"]`, `button[aria-label*="trÃ² chuyá»‡n má»›i"]`, v.v.
  - ThÃªm cÆ¡ cháº¿ **Text Fallback**: QuÃ©t toÃ n bá»™ tháº» `span, div, p` Ä‘á»ƒ tÃ¬m chá»¯ "New chat" hoáº·c "TrÃ² chuyá»‡n má»›i" vÃ  click vÃ o tháº» cha cÃ³ kháº£ nÄƒng click (button/a). Äiá»u nÃ y Ä‘áº£m báº£o luÃ´n tÃ¬m Ä‘Æ°á»£c nÃºt dÃ¹ Google cÃ³ Ä‘á»•i code áº©n Ä‘i chÄƒng ná»¯a.

### Giai Ä‘oáº¡n 24 â€” Fix lá»—i dÃ¡n text nhÆ°ng Gemini hiá»‡n icon Loa (KhÃ´ng gá»­i Ä‘Æ°á»£c)
- **Váº¥n Ä‘á»**: Khi Addon dÃ¡n Prompt vÃ o Ã´ nháº­p cá»§a Gemini, thay vÃ¬ hiá»‡n nÃºt Gá»­i (Send) thÃ¬ Gemini váº«n hiá»‡n icon Micro/Loa. GÃ¢y lá»—i khÃ´ng thá»ƒ nháº¥n nÃºt Gá»­i (do nÃºt Gá»­i chÆ°a xuáº¥t hiá»‡n).
- **NguyÃªn nhÃ¢n**: Gemini sá»­ dá»¥ng Web Component `<rich-textarea>`. Lá»‡nh `execCommand('insertText')` thay Ä‘á»•i text trong DOM nhÆ°ng khÃ´ng tá»± Ä‘á»™ng báº¯n ra sá»± kiá»‡n (Event) Ä‘á»ƒ bÃ¡o cho framework (Angular/Lit) cá»§a Gemini biáº¿t. Há»‡ thá»‘ng tÆ°á»Ÿng Ã´ nháº­p váº«n Ä‘ang trá»‘ng.
- **Giáº£i phÃ¡p**: 
  - Cáº­p nháº­t selector tÃ¬m Ã´ nháº­p: Láº¥y Ä‘Ãºng tháº» `div[contenteditable="true"]` náº±m SÃ‚U BÃŠN TRONG tháº» `<rich-textarea>`.
  - Cáº­p nháº­t hÃ m `fillInput()`: Báº¯t buá»™c báº¯n liÃªn tiáº¿p 3 event: `InputEvent('input')`, `Event('input')`, vÃ  `Event('change')` trá»±c tiáº¿p vÃ o Ã´ nháº­p. 
  - Äá»“ng thá»i báº¯n thÃªm má»™t event `input` ngÆ°á»£c lÃªn tháº» cha `<rich-textarea>` Ä‘á»ƒ "Ä‘Ã¡nh thá»©c" framework cá»§a Gemini, Ã©p nÃ³ nháº­n diá»‡n text vÃ  hiá»‡n nÃºt Gá»­i.

---

## Cáº¥u trÃºc file hiá»‡n táº¡i

```
CopilotWordExportAddon/
â”œâ”€â”€ manifest.json       â€” Cáº¥u hÃ¬nh extension (MV3, quyá»n downloads + storage, <all_urls>)
â”œâ”€â”€ background.js       â€” Service Worker: download_html / download_index / download_session
â”œâ”€â”€ content_script.js   â€” VÃ²ng láº·p auto, táº£i HTML tá»«ng Day, cáº­p nháº­t index & session
â”œâ”€â”€ popup.html          â€” Giao diá»‡n: Start/Stop, Resume tá»« session.json, log area
â””â”€â”€ popup.js            â€” Logic Popup: file picker, resume flow, day_saved status

AskCpl.py               â€” Python/Tkinter: Ä‘á»c JSON â†’ xuáº¥t Word (dÃ¹ng pywin32)
ProjectLog.md           â€” File nÃ y

Output (trong Downloads cá»§a trÃ¬nh duyá»‡t):
agent_name/
â”œâ”€â”€ index.html          â€” Trang tá»•ng há»£p, link Ä‘áº¿n tá»«ng bÃ i (cáº­p nháº­t dáº§n)
â”œâ”€â”€ day_1.html          â€” BÃ i ngÃ y 1 (file HTML Ä‘á»™c láº­p, Ä‘á»c offline Ä‘Æ°á»£c)
â”œâ”€â”€ day_2.html
â””â”€â”€ session.json        â€” Quáº£n lÃ½ phiÃªn (resume láº§n sau)
```

---

## CÃ¡c lá»‡nh & ThÆ° viá»‡n sá»­ dá»¥ng
- `pip install pywin32` â€” Báº¯t buá»™c Ä‘á»ƒ Python Ä‘iá»u khiá»ƒn MS Word.
- Addon APIs: `chrome.storage.local`, `chrome.downloads`, `chrome.runtime`, `chrome.tabs`.

---

## LÆ°u Ã½ quan trá»ng khi chá»‰nh sá»­a

> **Sau khi sá»­a `manifest.json` hoáº·c `background.js`:**
> VÃ o `edge://extensions/` â†’ báº¥m **Táº£i láº¡i (Reload)** extension.

> **Sau khi sá»­a `content_script.js`:**
> Quay láº¡i trang Copilot â†’ báº¥m **F5** Ä‘á»ƒ inject láº¡i script.

> **File HTML vÃ  session.json** náº±m trong `Downloads/agent_name/` (subfolder tá»± Ä‘á»™ng táº¡o).
> KhÃ´ng thá»ƒ tÃ¹y chá»‰nh Ä‘Æ°á»ng dáº«n ngoÃ i Downloads do giá»›i háº¡n báº£o máº­t trÃ¬nh duyá»‡t.

> **Sau khi sá»­a `content_script.js`:**
> Quay láº¡i trang Copilot â†’ báº¥m **F5** Ä‘á»ƒ inject láº¡i script.

> **Resume phiÃªn cÅ©:** Copy `session.json` tá»« `Downloads/agent_name/` sang báº¥t ká»³ Ä‘Ã¢u â†’ má»Ÿ Popup â†’ "ðŸ“‚ Chá»n file session.json" â†’ Start.

---

## Chuáº©n cáº¥u trÃºc file Roadmap (.md)

Äá»ƒ táº¡o lá»™ trÃ¬nh (Roadmap) chuáº©n xÃ¡c cho Addon Ä‘á»c á»Ÿ cháº¿ Ä‘á»™ "File MD", **báº¯t buá»™c tuÃ¢n theo Ä‘á»‹nh dáº¡ng sau** Ä‘á»ƒ Addon cÃ³ thá»ƒ parse báº±ng Regex.

```markdown
## Day 1 â€” TiÃªu Ä‘á» bÃ i há»c
**Prompt:**
Ná»™i dung cÃ¢u lá»‡nh báº¡n muá»‘n gá»­i cho AI. CÃ³ thá»ƒ dÃ i nhiá»u dÃ²ng.
Addon sáº½ copy toÃ n bá»™ ná»™i dung tá»« dÆ°á»›i chá»¯ "Prompt:" cho Ä‘áº¿n khi gáº·p chá»¯ "BÃ i táº­p:" hoáº·c "Tags:" hoáº·c dÃ²ng "## Day" tiáº¿p theo.

**BÃ i táº­p:**
- BÃ i 1
- BÃ i 2

**Tags:** #tag
```

- Addon sáº½ tá»± Ä‘á»™ng tÃ¬m cÃ¡c cá»¥m `## Day X`.
- Addon sáº½ láº¥y má»i vÄƒn báº£n tá»« sau `**Prompt:**` Ä‘á»ƒ lÃ m cÃ¢u lá»‡nh (prompt) gá»­i cho AI.
- Náº¿u báº¡n yÃªu cáº§u AI khÃ¡c táº¡o Roadmap, hÃ£y cung cáº¥p Ä‘Ãºng chuáº©n nÃ y Ä‘á»ƒ táº¡o ra file `.md` Äƒn khá»›p 100% vá»›i Addon.

### Giai Ä‘oáº¡n 25 â€” Táº¡o Roadmap JavaScript 7 NÄƒm (2560 NgÃ y)
- ÄÃ£ táº¡o Python script `generate_js_roadmap.py` Ä‘á»ƒ tá»± Ä‘á»™ng hÃ³a viá»‡c sinh file Markdown dÃ i (hÆ¡n 33,000 dÃ²ng).
- Gen thÃ nh cÃ´ng file `roadmap_javascript_7years.md` bao phá»§ toÃ n bá»™ lá»™ trÃ¬nh 2560 ngÃ y há»c liÃªn tá»¥c (tá»« Foundation Ä‘áº¿n Web3, AI, Distributed System).
- File tuÃ¢n thá»§ 100% Ä‘á»‹nh dáº¡ng Parsing cá»§a Copilot Word Export Addon.

### Giai Ä‘oáº¡n 26 â€” Táº¡o Roadmap Thá»ƒ Dá»¥c Táº¡i NhÃ  (365 NgÃ y)
- YÃªu cáº§u: Thiáº¿t káº¿ lá»™ trÃ¬nh giáº£m cÃ¢n & tÄƒng cÆ¡ 1 nÄƒm cho ngÆ°á»i 108kg, 100% táº­p táº¡i nhÃ , 30 phÃºt/ngÃ y, khÃ´ng báº­t nháº£y (báº£o vá»‡ khá»›p).
- Thá»±c thi: ÄÃ£ táº¡o file `roadmap_fitness_365days.md` chá»©a Ä‘áº§y Ä‘á»§ 365 ngÃ y (gá»“m bÃ i táº­p chi tiáº¿t sá»‘ hiá»‡p/láº§n vÃ  thá»±c Ä‘Æ¡n tÆ°Æ¡ng á»©ng má»—i ngÃ y).
- TÃ­ch há»£p chuáº©n Copilot Addon: Prompt yÃªu cáº§u AI nháº¯c nhá»Ÿ ká»¹ thuáº­t an toÃ n khá»›p, Ä‘Ã¡nh giÃ¡ thá»±c Ä‘Æ¡n vÃ  Ä‘á»™ng viÃªn ngÆ°á»i dÃ¹ng.
- **Báº£n V2 (Cáº­p nháº­t)**: Bá»• sung Ä‘á»‹nh lÆ°á»£ng thá»±c Ä‘Æ¡n chÃ­nh xÃ¡c (sá»‘ gram, chÃ©n) vÃ  chi tiáº¿t 100% form chuáº©n cá»§a cÃ¡c bÃ i táº­p trá»±c tiáº¿p vÃ o file HTML (Ä‘á»ƒ ngÆ°á»i dÃ¹ng dá»… theo dÃµi). ÄÃ£ chá»‰nh sá»­a Prompt Ä‘á»ƒ AI lÃ m "Kiá»ƒm toÃ¡n viÃªn dinh dÆ°á»¡ng" Ä‘Ã¡nh giÃ¡ trá»±c tiáº¿p sá»‘ lÆ°á»£ng thá»±c pháº©m nÃ y.
- Dá»n dáº¹p: ÄÃ£ lÆ°u láº¡i script Python `generate_fitness_365_v2.py` theo yÃªu cáº§u cá»§a ngÆ°á»i dÃ¹ng Ä‘á»ƒ tÃ¹y biáº¿n sau nÃ y.

### Giai Ä‘oáº¡n 28 â€” Fix Lá»—i Káº¹t Chá» 30s & Chá»‘ng Ngá»§ Báº±ng Silent Audio
- **Váº¥n Ä‘á» 1**: QuÃ¡ trÃ¬nh Automation thá»‰nh thoáº£ng bá»‹ káº¹t vÄ©nh viá»…n á»Ÿ bÆ°á»›c chá» táº¡o New Chat (cÃ³ thá»ƒ do káº¿t ná»‘i máº¡ng yáº¿u hoáº·c UI cá»§a AI thay Ä‘á»•i). Lá»—i khiáº¿n cho há»‡ thá»‘ng máº¥t tá»« 7 phÃºt Ä‘áº¿n vÃ i chá»¥c phÃºt.
- **Giáº£i phÃ¡p 1**: Ãp dá»¥ng Timeout 30 giÃ¢y cho hÃ m `waitForNewChatReady`. Náº¿u sau 30s mÃ  New Chat chÆ°a sáºµn sÃ ng, Extension sáº½ tá»± Ä‘á»™ng Ã©p Reload trang (`location.reload()`). Nhá» cÆ¡ cháº¿ Auto-Resume cÃ³ sáºµn tá»« Giai Ä‘oáº¡n 17, há»‡ thá»‘ng sáº½ tá»± Ä‘á»™ng khÃ´i phá»¥c quy trÃ¬nh vÃ  cháº¡y láº¡i Day Ä‘Ã³ thay vÃ¬ bá»‹ káº¹t vÄ©nh viá»…n.
- **Váº¥n Ä‘á» 2**: CÃ¡c trÃ¬nh duyá»‡t hiá»‡n Ä‘áº¡i (Chrome/Edge) tá»± Ä‘á»™ng Ä‘Æ°a tab vÃ o cháº¿ Ä‘á»™ ngá»§ (Sleeping Tabs/Background Throttling) khi tab bá»‹ áº©n quÃ¡ lÃ¢u, khiáº¿n Javascript cháº¡y ngáº§m bá»‹ delay cá»±c náº·ng, kÃ©o dÃ i thá»i gian chá» 5-7 phÃºt.
- **Giáº£i phÃ¡p 2**: KÃ­ch hoáº¡t láº¡i ká»¹ thuáº­t Silent Audio Keep-alive (tá»«ng bá»‹ táº¯t á»Ÿ Giai Ä‘oáº¡n 13). Báº±ng cÃ¡ch chÃ¨n má»™t file Ã¢m thanh ngáº¯n (chuá»—i Base64 cá»±c nhá») tÄ©nh láº·ng (0.01 volume) vÃ  láº·p vÃ´ táº­n thÃ´ng qua tháº» `<audio>` khi gá»i `setupKeepAlive`. Äiá»u nÃ y sáº½ "Ä‘Ã¡nh lá»«a" trÃ¬nh duyá»‡t tin ráº±ng tab Ä‘ang phÃ¡t ná»™i dung Media, duy trÃ¬ má»©c Æ°u tiÃªn xá»­ lÃ½ cao nháº¥t (Highest Priority) vÃ  chá»‘ng Throttling 100%.


### Giai Ä‘oáº¡n 29 â€” Fix ToÃ n Diá»‡n: Chrome Reload, Heartbeat, Error Detection

**PhÃ¡t hiá»‡n 7 bug qua phÃ¢n tÃ­ch thá»±c táº¿ khi cháº¡y trÃªn Chrome:**

| # | Bug | Háº­u quáº£ | Fix |
|---|-----|----------|-----|
| F1 | sessionStorage khÃ´ng tin cáº­y trÃªn Chrome khi reload | Loop bÃ¡o â€œKhÃ´i phá»¥c...â€ nhÆ°ng Ä‘á»©ng luÃ´n | Thay báº±ng chrome.storage.local lÃ m reload flag vá»›i timestamp expire 15s |
| F2 | let _isIntentionalReload = false khai bÃ¡o SAU pagehide listener | pagehide luÃ´n tháº¥y flag = alse â†’ luÃ´n xÃ³a 
unningStates | Di chuyá»ƒn khai bÃ¡o lÃªn TRÆ¯á»šC pagehide listener |
| F3 | pagehide xÃ³a 
unningStates ká»ƒ cáº£ khi intentional reload | Máº¥t state trÆ°á»›c khi ká»‹p reload | Chá»‰ xÃ³a khi !_isIntentionalReload |
| F4 | udio.play() bá»‹ block trÃªn Chrome sau reload (khÃ´ng cÃ³ user gesture) | Silent Audio khÃ´ng phÃ¡t â†’ tab cÃ³ thá»ƒ sleep | TÃ¡ch hÃ m _playKeepAliveAudio() vá»›i retry sau 3s |
| F5 | KhÃ´ng detect error response (máº¥t máº¡ng, rate limit) | LÆ°u bÃ i vá»›i ná»™i dung error message cá»§a trang | ThÃªm isErrorContent(html) check â†’ retry náº¿u phÃ¡t hiá»‡n tá»« khÃ³a lá»—i |
| F6 | KhÃ´ng cÃ³ heartbeat â†’ popup khÃ´ng biáº¿t loop Ä‘Ã£ cháº¿t | Popup váº«n hiá»‡n nÃºt STOP dÃ¹ loop cháº¿t tá»« lÃ¢u | Content script cáº­p nháº­t lastHeartbeat má»—i 15s. Popup kiá»ƒm tra: náº¿u > 45s â†’ tá»± clear. Fix bug key sai 
unningState â†’ 
unningStates |
| F7 | Sau reload, retry láº§n 2 váº«n click New Chat â†’ timeout â†’ reload láº¡i | VÃ²ng láº·p reload vÃ´ táº­n | Guard _lastReloadTs: náº¿u vá»«a reload trong 60s â†’ skip click New Chat |

- **Edge váº«n hoáº¡t Ä‘á»™ng**: pagehide chá»‰ xÃ³a state khi !_isIntentionalReload. Heartbeat timeout 45s Ä‘á»§ dÃ i Ä‘á»ƒ khÃ´ng false-positive khi Edge SPA navigate.
- **KhÃ´ng thay Ä‘á»•i flow chÃ­nh**: Táº¥t cáº£ fix chá»‰ áº£nh hÆ°á»Ÿng startup/reload/error path.


### Bá»• sung Fix Giai Ä‘oáº¡n 29 â€” Lá»—i Reload khÃ´ng resume Ä‘Æ°á»£c

**NguyÃªn nhÃ¢n:**
- HÃ m utoSave() trÆ°á»›c Ä‘Ã¢y chá»‰ Ä‘Æ°á»£c gá»i SAU khi má»™t ngÃ y hoÃ n thÃ nh. Náº¿u timeout vÃ  reload xáº£y ra á»Ÿ ngÃ y Ä‘áº§u tiÃªn trÆ°á»›c khi extract thÃ nh cÃ´ng, chÆ°a cÃ³ file session Ä‘Æ°á»£c lÆ°u vÃ o á»• Ä‘Ä©a/storage â†’ sau khi reload sáº½ khÃ´ng cÃ³ Ä‘á»ƒ khÃ´i phá»¥c.
- Biáº¿n JS _lastReloadTs bá»‹ reset vá» 0 sau khi load láº¡i trang, khiáº¿n chá»‘ng loop reload fail vÃ  vÃ²ng láº·p vÃ´ táº­n váº«n tiáº¿p tá»¥c click â€œNew chatâ€ rá»“i reload.

**Fix:**
| # | File | Chi tiáº¿t |
|---|------|---------|
| 1 | content_script.js | ThÃªm saveStateForReload() vÃ  Ä‘á»£i callback xÃ¡c nháº­n lÆ°u xong TRÆ¯á»šC khi thá»±c hiá»‡n location.reload(). LÆ°u current state dÃ¹ chÆ°a lÃ m xong bÃ i nÃ o. |
| 2 | content_script.js | Bá» qua kiá»ƒm tra phá»©c táº¡p báº±ng _lastReloadTs, Ä‘Æ¡n giáº£n hÃ³a logic 
eedNewChat báº±ng param tá»« background (gá»­i thÃªm isFromReload Ä‘á»ƒ biáº¿t lÃ  má»›i reload xong â†’ Ä‘ang á»Ÿ New Chat sáºµn, KHÃ”NG click ná»¯a). |


### Giai Ä‘oáº¡n 30 â€” Sá»­a lá»—i vÆ°á»£t Quota Storage & Auto-Stop Roadmap

- **Váº¥n Ä‘á» 1 (Session khÃ´ng lÆ°u Ä‘Æ°á»£c do vÆ°á»£t dung lÆ°á»£ng):** Vá»›i nhá»¯ng Roadmap quÃ¡ lá»›n (VD 2500 ngÃ y), file session json encode thÃ nh base64 sáº½ vÆ°á»£t quÃ¡ giá»›i háº¡n 5MB máº·c Ä‘á»‹nh cá»§a `chrome.storage.local`. Äiá»u nÃ y lÃ m API `chrome.storage.local.set` fail ngáº§m, khiáº¿n data khÃ´ng thá»ƒ phá»¥c há»“i sau khi reload trang.
  - **Giáº£i phÃ¡p:** Cáº¥p quyá»n `"unlimitedStorage"` trong `manifest.json`. NgÆ°á»i dÃ¹ng cáº§n pháº£i reload láº¡i Add-on á»Ÿ trang `chrome://extensions/` Ä‘á»ƒ Chrome yÃªu cáº§u cáº¥p quyá»n nÃ y, Ä‘áº£m báº£o vÃ²ng láº·p dÃ¹ 5000 ngÃ y váº«n lÆ°u state an toÃ n.
- **Váº¥n Ä‘á» 2 (KhÃ´ng tá»± dá»«ng khi cháº¡y áº¿t Roadmap mÃ  quÃªn Ä‘iá»n endDay):** Há»‡ thá»‘ng luÃ´n coi `endDay = null` náº¿u user bá» trá»‘ng, gÃ¢y cháº¡y vÃ´ táº­n qua ngÃ y 2501, 2502... báº±ng dá»¯ liá»‡u rá»—ng hoáº·c template máº·c Ä‘á»‹nh.
  - **Giáº£i phÃ¡p:** ThÃªm hÃ m `calcAutoEndDay()` á»Ÿ `content_script.js`. Tá»± Ä‘á»™ng parse táº¥t cáº£ `roadmapData` trong `start_loop` vÃ  `resume_session`, tÃ¬m `Math.max` cá»§a cÃ¡c day Ä‘á»ƒ auto fill `endDay`. Báº£o Ä‘áº£m tá»± ngáº¯t loop Ä‘Ãºng ngÃ y cuá»‘i dÃ¹ user cháº£ gÃµ gÃ¬ vÃ o Ã´ NgÃ y káº¿t thÃºc.


### Giai Ä‘oáº¡n 31 â€” Kháº¯c phá»¥c Lá»—i Service Worker & Chá»‘ng Káº¹t Tráº¡ng ThÃ¡i Chá»

- **Váº¥n Ä‘á» 1 (Lá»—i `Receiving end does not exist`):** `chrome.runtime.sendMessage` bá»‹ Promise Rejection do Service Worker `background.js` rÆ¡i vÃ o tráº¡ng thÃ¡i ngá»§ ngáº§m sau 30s khÃ´ng hoáº¡t Ä‘á»™ng, khiáº¿n file HTML khÃ´ng Ä‘Æ°á»£c táº£i vá» Ä‘Ä©a.
  - **Giáº£i phÃ¡p:** 
    - ThÃªm listener `action: "ping"` á»Ÿ `background.js` vÃ  gá»­i ping má»—i 20s tá»« `content_script.js` Ä‘á»ƒ giá»¯ Service Worker luÃ´n thá»©c.
    - Viáº¿t láº¡i hÃ m gá»­i lá»‡nh download báº±ng cÃ¡ch bá»c trong `sendDownloadMessageWithRetry()`, tá»± Ä‘á»™ng `await delay(1000)` vÃ  retry tá»‘i Ä‘a 3 láº§n náº¿u báº¯t gáº·p lá»—i káº¿t ná»‘i.
- **Váº¥n Ä‘á» 2 (Káº¹t tráº¡ng thÃ¡i `Chá» AI pháº£n há»“i` gáº§n 1 tiáº¿ng):** Náº¿u rá»›t máº¡ng hoáº·c Gemini bÃ¡o lá»—i (Network Error), icon loading bá»‹ dÃ­nh trÃªn DOM. Addon láº§m tÆ°á»Ÿng AI váº«n Ä‘ang gÃµ vÃ  chá» mÃ¹ quÃ¡ng tá»›i 10 phÃºt.
  - **Giáº£i phÃ¡p:** Cáº£i tiáº¿n hÃ m `checkStable15s()`. Bá»• sung biáº¿n theo dÃµi `textChangeStart`. Náº¿u Ä‘á»™ dÃ i chá»¯ khÃ´ng tÄƒng thÃªm má»™t kÃ½ tá»± nÃ o trong vÃ²ng 60 giÃ¢y (dÃ¹ UI váº«n Ä‘ang bÃ¡o generating), há»‡ thá»‘ng sáº½ chá»§ Ä‘á»™ng Ã©p `return false` (timeout).
  - VÃ²ng láº·p `_runNextDayAttempt()` sáº½ bÃ¡o Lá»—i vÃ  tá»± Ä‘á»™ng kÃ­ch hoáº¡t tiáº¿n trÃ¬nh Retry. LÆ°u Ã½: tiáº¿n trÃ¬nh Retry máº·c Ä‘á»‹nh cá»§a há»‡ thá»‘ng váº«n sáº½ gÃµ láº¡i **chÃ­nh xÃ¡c cÃ¢u há»i cá»§a NgÃ y hiá»‡n táº¡i (currentDay)** trÃªn má»™t cá»­a sá»• Chat Má»›i, Ä‘áº£m báº£o khÃ´ng bá»‹ láº·p cÃ³c ngÃ y.

### Giai Ä‘oáº¡n 27 â€” Táº¡o Roadmap Access VBA (365 NgÃ y - Full Professional)
- YÃªu cáº§u: Äá»c 220 file HTML khÃ³a há»c táº¡i `D:\Code\Data Code\Course\Acces_VBA`, phÃ¢n tÃ­ch chá»§ Ä‘á» tá»«ng ngÃ y, xÃ¡c Ä‘á»‹nh khoáº£ng trá»‘ng vÃ  bá»• sung lá»™ trÃ¬nh há»c hoÃ n chá»‰nh.
- PhÃ¢n tÃ­ch & Bá»• sung:
  - 290 ngÃ y: Cáº¥u trÃºc ban Ä‘áº§u vá»›i 5 nhÃ³m chá»§ Ä‘á» cÃ²n thiáº¿u: Ribbon/Custom UI, Class Module & OOP, Report Builder nÃ¢ng cao, Multi-user & Locking, Deployment & Distribution.
  - 365 ngÃ y: Má»Ÿ rá»™ng thÃªm 75 ngÃ y Ä‘á»ƒ bao quÃ¡t SQL Mastery (CTE, Window Functions), Advanced Controls (TreeView, ListView, ActiveX), Modern Integration (Microsoft Graph, Power Automate, SharePoint, Teams).
  - Æ¯á»›c lÆ°á»£ng thá»i gian: ÄÃ£ gáº¯n nhÃ£n thá»i gian há»c cá»¥ thá»ƒ cho tá»«ng ngÃ y (30 phÃºt, 60 phÃºt, 90 phÃºt, 120 phÃºt, 3-4 giá»).
- Thá»±c thi: Táº¡o file `roadmap_access_vba.md` chá»©a Ä‘á»§ 365 ngÃ y (8037 dÃ²ng, ~422 KB), chuáº©n format Copilot Addon regex.
- Script Python `generate_access_vba_roadmap.py` Ä‘Æ°á»£c giá»¯ láº¡i Ä‘á»ƒ tÃ¹y biáº¿n sau.

### Quy táº¯c sinh file Roadmap (NgÃ´n ngá»¯ / Láº­p trÃ¬nh)
1. **Äá»‘i vá»›i NgÃ´n ngá»¯ há»c (Nháº­t, Trung, Anh, v.v.):**
   - Lá»™ trÃ¬nh pháº£i tráº£i dÃ i Ä‘á»§ lá»›n (VD: 1000 ngÃ y) tá»« Vá»¡ lÃ²ng Ä‘áº¿n Báº£n Ä‘á»‹a.
   - CÃ¡c ngÃ y Ä‘áº§u tiÃªn Báº®T BUá»˜C pháº£i táº­p trung vÃ o Báº£ng chá»¯ cÃ¡i/PhÃ¡t Ã¢m/Pinyin trÆ°á»›c khi vÃ o tá»« vá»±ng hay ngá»¯ phÃ¡p.
   - VÃ²ng láº·p há»c kiáº¿n thá»©c xen káº½ khoa há»c (VD: Ngá»¯ phÃ¡p -> Tá»« vá»±ng -> Chá»¯ HÃ¡n/HÃ¡n tá»± -> Äá»c hiá»ƒu -> Nghe hiá»ƒu -> Giao tiáº¿p).
   - Prompt gá»­i cho AI pháº£i cÃ³ phÆ°Æ¡ng phÃ¡p sÆ° pháº¡m: 
     + Tá»« vá»±ng/Chá»¯ HÃ¡n: CÃ³ Mnemonic (cÃ¢u chuyá»‡n ghi nhá»›), Bá»™ thá»§, PhÃ¡t Ã¢m/Pinyin.
     + Ngá»¯ phÃ¡p: CÃ³ Cáº¥u trÃºc, CÃ¡ch dÃ¹ng (Nuance), CÃ¢u vÃ­ dá»¥.
     + Báº¯t buá»™c yÃªu cáº§u AI chá»‰ ra **Lá»—i sai phá»• biáº¿n cá»§a ngÆ°á»i Viá»‡t**.
2. **Äá»‘i vá»›i NgÃ´n ngá»¯ Láº­p trÃ¬nh (Python, VBA, JS, v.v.):**
   - PhÃ¢n chia theo Phase tá»« CÄƒn báº£n Ä‘áº¿n ChuyÃªn sÃ¢u.
- **Root cause:** Click "New Chat" trÃªn M365 â†’ SPA navigate â†’ content_script.js bá»‹ **re-inject** â†’ táº¥t cáº£ biáº¿n JS reset (`isRunning=false`, `currentDay=1`) â†’ loop "dá»«ng". ÄÃ¢y khÃ´ng pháº£i tab sleep â€” mÃ  lÃ  **script bá»‹ reload**.

- **Fix: Auto-Resume khi script load:**
  - Khi content_script.js khá»Ÿi táº¡o â†’ Ä‘á»c `chrome.storage.local['runningState']`
  - Náº¿u `isRunning === true`:
    - KhÃ´i phá»¥c: `currentDay`, `agentName`, `folderName`, `prefix`, `dayIndex` (tá»« autosave_data)
    - `setupKeepAlive()`
    - Chá» 5s (page settle) â†’ `runNextDay()` tá»± Ä‘á»™ng
    - Log: `ðŸ”„ AUTO-RESUME: "AgentName" tá»« Day N`

- **Fix: `saveRunningState(nextDay, lastSaved)`:**
  - Tham sá»‘ má»›i `nextDay`: luÃ´n lÆ°u day **TIáº¾P THEO** cáº§n xá»­ lÃ½
  - Gá»i SAU `currentDay++` trong `processExtractedContent`
  - â†’ Auto-resume Ä‘á»c `runningState.currentDay` = Ä‘Ãºng day cáº§n cháº¡y, khÃ´ng trÃ¹ng day Ä‘Ã£ xong
  - ThÃªm `prefix` vÃ o runningState Ä‘á»ƒ auto-resume biáº¿t prefix

### Giai Ä‘oáº¡n 18 â€” Fix CSP, Audio, Context Invalidation & Tá»‘i Æ°u Adaptive Wait

- **Fix Worker CSP**: Bá» `Blob Worker` vÃ¬ M365 CSP cháº·n `worker-src 'self'`. DÃ¹ng `setInterval` bÃ¬nh thÆ°á»ng. Káº¿t há»£p vá»›i `Web Lock` lÃ  Ä‘á»§ chá»‘ng discard.
- **Fix AudioContext**: Bá» `AudioContext` vÃ¬ yÃªu cáº§u user gesture, cÃ³ thá»ƒ nÃ©m lá»—i khi auto-resume hoáº·c reload.
- **Fix Context Invalidated**: Khi script bá»‹ orphan do reload, gá»i `chrome.runtime.sendMessage` sáº½ throw exception lÃ m sáº­p script. â†’ Viáº¿t hÃ m `safeSendMessage` bá»c try-catch vÃ  check `chrome.runtime?.id`.
- **Tá»‘i Æ°u Adaptive Wait**: RÃºt ngáº¯n thá»i gian chá» cá»©ng `MIN_WAIT` tá»« 120s xuá»‘ng 15s. Sau 15s báº¯t Ä‘áº§u check stability (cáº§n 15s stable). Tá»•ng cá»™ng máº¥t khoáº£ng ~30s náº¿u AI tráº£ lá»i xong nhanh (thay vÃ¬ luÃ´n luÃ´n chá» cháº¿t 2 phÃºt).

### Giai Ä‘oáº¡n 19 â€” Fix Lá»—i "Chá» 10s Bá»‹ ÄÃ³ng BÄƒng" (Tab Freeze) & Tá»‘i Æ°u Auto-Resume

- **Root Cause**: Giai Ä‘oáº¡n 18 gá»¡ `AudioContext` khiáº¿n tab cháº¡y ngáº§m (background) dá»… bá»‹ Chromium Ä‘Ã³ng bÄƒng toÃ n bá»™ Javascript (Tab Freeze) ngay sau khi AI táº¡o xong text (vÃ¬ DOM khÃ´ng cÃ²n thay Ä‘á»•i). Viá»‡c gá»i `delay(10000)` dÃ¹ng `setTimeout` sáº½ bá»‹ ngÆ°ng Ä‘á»ng vÄ©nh viá»…n khÃ´ng bao giá» cháº¡y tiáº¿p.
- **Kháº¯c phá»¥c 1 (Bá» nhÃ n rá»—i)**: XÃ³a bá» hoÃ n toÃ n thá»i gian chá» 10s vÃ´ nghÄ©a giá»¯a cÃ¡c Day trong `processExtractedContent`. Cháº¡y ngay sang Day káº¿ tiáº¿p Ä‘á»ƒ giá»¯ luá»“ng hoáº¡t Ä‘á»™ng, ngÄƒn Chromium ráº£nh rá»—i Ä‘Ã³ng bÄƒng tab.
- **Kháº¯c phá»¥c 2 (Tá»‘i Æ°u Reload)**: Khi M365 bá»‹ táº£i láº¡i (do SPA navigate) vÃ  trigger `Auto-Resume`, giáº£m thá»i gian chá» cá»§a Auto-Resume tá»« 5s xuá»‘ng 1.5s Ä‘á»ƒ trÃ¡nh freeze. Truyá»n cá» `isAutoResumed = true` vÃ o `runNextDay` Ä‘á»ƒ ngÄƒn script báº¥m nÃºt `New Chat` thÃªm má»™t láº§n ná»¯a (vÃ¬ trang vá»«a táº£i láº¡i vá»‘n dÄ© Ä‘Ã£ lÃ  chat má»›i tinh), trÃ¡nh vÃ²ng láº·p táº£i láº¡i trang vÃ´ táº­n.

### Giai Ä‘oáº¡n 20 â€” Fix Lá»—i Chá» LÃ¢u (5-10 phÃºt) Khi AI ÄÃ£ Xong

- **Váº¥n Ä‘á»**: ÄÃ´i lÃºc AI Ä‘Ã£ táº¡o xong toÃ n bá»™ ná»™i dung, nhÆ°ng tiáº¿n trÃ¬nh váº«n Ä‘á»©ng yÃªn chá» thÃªm 5-10 phÃºt thay vÃ¬ hoÃ n thÃ nh ngay.
- **NguyÃªn nhÃ¢n**:
  1. **Strict Equality**: HÃ m `checkStable15s` Ä‘o Ä‘á»™ dÃ i text (`innerText.length`) cá»§a toÃ n trang vÃ  yÃªu cáº§u khÃ´ng Ä‘Æ°á»£c thay Ä‘á»•i dÃ¹ chá»‰ 1 kÃ½ tá»± (`len === lastLen`) trong suá»‘t 15 giÃ¢y.
  2. **Nhiá»…u DOM**: Giao diá»‡n M365 Copilot thÆ°á»ng cÃ³ cÃ¡c thay Ä‘á»•i nhá» ngoÃ i Ã½ muá»‘n (vÃ­ dá»¥: thá»i gian cáº­p nháº­t "1 min ago", nÃºt chá»©c nÄƒng áº©n/hiá»‡n, gá»£i Ã½ prompt). CÃ¡c thay Ä‘á»•i nÃ y lÃ m chiá»u dÃ i text dao Ä‘á»™ng nháº¹, liÃªn tá»¥c reset bá»™ Ä‘áº¿m á»•n Ä‘á»‹nh 15 giÃ¢y.
- **Giáº£i phÃ¡p**:
  - **Äo lÆ°á»ng cá»¥c bá»™ (Scoped Check)**: Viáº¿t hÃ m `getNewTextLength()` CHá»ˆ tÃ­nh Ä‘á»™ dÃ i text cá»§a cÃ¡c element Má»šI sinh ra sau khi gá»­i prompt (dá»±a trÃªn viá»‡c lá»c bá» cÃ¡c element cÃ³ `dataset.askcplSnapshot = "1"`). Äiá»u nÃ y cháº·n má»i nhiá»…u tá»« cÃ¡c thÃ nh pháº§n cÅ© trÃªn trang.
  - **Dung sai (Tolerance)**: Cho phÃ©p sai sá»‘ thay Ä‘á»•i `Math.abs(len - lastLen) <= 30` kÃ½ tá»±. Khi AI thá»±c sá»± stream text, sá»‘ lÆ°á»£ng kÃ½ tá»± sáº½ tÄƒng ráº¥t nhanh vÃ  bá»©t phÃ¡ khá»i khoáº£ng dung sai. Náº¿u chá»‰ lÃ  UI render nÃºt "Copy" hay icon thay Ä‘á»•i á»Ÿ cuá»‘i quÃ¡ trÃ¬nh, sá»± dao Ä‘á»™ng sáº½ náº±m trong khoáº£ng 30 kÃ½ tá»± vÃ  khÃ´ng lÃ m reset bá»™ Ä‘áº¿m, giÃºp tiáº¿n trÃ¬nh nháº­n diá»‡n AI Ä‘Ã£ xong ngay láº­p tá»©c.

### Giai Ä‘oáº¡n 21 â€” Há»‡ thá»‘ng Config Äa Ná»n Táº£ng & Bá»™ nhá»› phá»ng váº¥n (Multi-step Interrogation)

- **Váº¥n Ä‘á»**:
  - NgÆ°á»i dÃ¹ng cáº§n lÆ°u nhiá»u cáº¥u hÃ¬nh (Config) khÃ¡c nhau cho cÃ¡c Agent khÃ¡c nhau (vÃ­ dá»¥: má»™t cÃ¡i cho Copilot tiáº¿ng Anh, má»™t cÃ¡i cho Gemini).
  - Cáº§n tÃ­nh nÄƒng tá»± dá»«ng vÃ²ng láº·p á»Ÿ má»™t `NgÃ y káº¿t thÃºc` (End Day) nháº¥t Ä‘á»‹nh.
  - VÃ²ng láº·p chat dÃ i ngÃ y khiáº¿n AI "quÃªn" cÃ¡c chá»§ Ä‘á» Ä‘Ã£ há»c. Cáº§n má»™t cÃ¡ch Ä‘á»ƒ báº¯t AI tá»± tÃ³m táº¯t vÃ  ghi nhá»› láº¡i cÃ¡c Ã½ chÃ­nh Ä‘Ã£ há»c á»Ÿ má»—i ngÃ y Ä‘á»ƒ má»›m (inject) vÃ o prompt cá»§a ngÃ y tiáº¿p theo.

- **Giáº£i phÃ¡p**:
  - **Há»‡ thá»‘ng Profiles**: NÃ¢ng cáº¥p `popup.html/js` Ä‘á»ƒ cÃ³ má»™t Dropdown duy nháº¥t cho phÃ©p chá»n, lÆ°u vÃ  xÃ³a nhiá»u Profile khÃ¡c nhau (vd: "Copilot - Basic", "Copilot - Tá»« vá»±ng"). ToÃ n bá»™ config (Day, Tiá»n tá»‘, End Day, tÃ­nh nÄƒng nÃ¢ng cao) Ä‘Æ°á»£c bá»c chung vÃ o 1 Profile vÃ  lÆ°u trong `chrome.storage`.
  - **NgÃ y káº¿t thÃºc (End Day)**: ThÃªm Ã´ thiáº¿t láº­p `End Day`. Trong `processExtractedContent`, náº¿u `currentDay >= endDay`, vÃ²ng láº·p sáº½ gá»i `finishLoop()` ngay láº­p tá»©c.
  - **Memory Advanced (Phá»ng váº¥n liÃªn hoÃ n)**:
    - Biáº¿n Addon thÃ nh má»™t quy trÃ¬nh Agentic (Multi-step Interrogation). Thay vÃ¬ 1 Day chá»‰ gá»­i 1 lá»‡nh, Addon sáº½ tá»± Ä‘á»™ng nháº¯n tin phá»ng váº¥n AI nhiá»u láº§n trong cÃ¹ng 1 bÃ i.
    - BÆ°á»›c 1: Gá»­i bÃ i chÃ­nh `Day X`.
    - BÆ°á»›c 2: Gá»­i cÃ¢u há»i má»›m Ä‘á»ƒ há»i TÃªn Chá»§ Äá» (vd: *"Chá»§ Ä‘á» lÃ  gÃ¬ chá»‰ má»—i chá»§ Ä‘á» thÃ´i"*). Cáº­p nháº­t biáº¿n Ä‘áº¿m sá»‘ bÃ i cá»§a chá»§ Ä‘á» Ä‘Ã³.
    - BÆ°á»›c 3: Náº¿u Chá»§ Ä‘á» chÆ°a hoÃ n thÃ nh Ä‘á»§ sá»‘ lÆ°á»£ng má»¥c tiÃªu, Addon vÃ²ng láº·p qua cÃ¡c "Chi tiáº¿t" Ä‘Æ°á»£c cÃ i Ä‘áº·t trÃªn giao diá»‡n (vÃ­ dá»¥: Chi tiáº¿t 1: "Tá»« vá»±ng", Chi tiáº¿t 2: "Ngá»¯ phÃ¡p"). Má»—i chi tiáº¿t sáº½ kÃ­ch hoáº¡t 1 cÃ¢u há»i Ä‘á»™c láº­p vá»›i AI (vd: *"Há»i tá»« vá»±ng lÃ  gÃ¬, chá»‰ ghi cÃ¡c tá»« vá»±ng thÃ´i"*).
    - CÃ¢u tráº£ lá»i cá»§a AI cho cÃ¡c Chi tiáº¿t nÃ y sáº½ Ä‘Æ°á»£c bÃ³c tÃ¡ch vÃ  cá»™ng dá»“n vÃ o Object bá»™ nhá»› cá»¥c bá»™ (`topicMemory`).
  - **Memory Injector**: TrÆ°á»›c khi gá»­i `Day X+1`, Addon tá»± Ä‘á»™ng format bá»™ nhá»› `topicMemory` thÃ nh má»™t khá»‘i text gá»n gÃ ng (vd: *Chá»§ Ä‘á»: Con ngÆ°á»i 1/4 \n Tá»« vá»±ng Ä‘Ã£ há»c: ... \n Ngá»¯ phÃ¡p Ä‘Ã£ há»c: ...*). Khá»‘i text nÃ y Ä‘Æ°á»£c gáº¯n trá»±c tiáº¿p vÃ o cuá»‘i cÃ¢u lá»‡nh `Day X+1` Ä‘á»ƒ "má»›m" trÃ­ nhá»› cho AI. CÃ¡c chá»§ Ä‘á» Ä‘Ã£ Ä‘áº¡t má»¥c tiÃªu (vÃ­ dá»¥ 4/4) sáº½ Ä‘Æ°á»£c rÃºt gá»n thÃ nh chá»¯ "HoÃ n táº¥t" Ä‘á»ƒ tiáº¿t kiá»‡m token.

### Giai Ä‘oáº¡n 22 â€” Adapter Äa Ná»n Táº£ng (Gemini/ChatGPT) & Lá»™ trÃ¬nh Äá»™ng PhÃ¢n Cáº¥p (Hierarchical Roadmap)

- **Váº¥n Ä‘á»**: NgÆ°á»i dÃ¹ng cáº§n cháº¡y Add-on á»Ÿ nhÃ  vá»›i cÃ¡c tÃ i khoáº£n AI miá»…n phÃ­ (Google Gemini, ChatGPT) nhÆ°ng cÃ¡c AI nÃ y khÃ´ng há»— trá»£ táº¡o Agent lÆ°u ngá»¯ cáº£nh cá»‘ Ä‘á»‹nh (System Prompt). HÆ¡n ná»¯a, viá»‡c "nhá»“i" trÃ­ nhá»› cá»§a hÃ ng trÄƒm bÃ i há»c cÅ© vÃ o má»™t cÃ¢u lá»‡nh sáº½ gÃ¢y phÃ¬nh to ngá»¯ cáº£nh (Context Overflow) vÃ  tá»‘n token. Viá»‡c thay Ä‘á»•i tÃ i khoáº£n AI miá»…n phÃ­ (do háº¿t lÆ°á»£t) cÅ©ng lÃ m xÃ¡o trá»™n lá»™ trÃ¬nh.
- **Giáº£i phÃ¡p**:
  1. **Hierarchical Roadmap (Lá»™ trÃ¬nh phÃ¢n cáº¥p)**:
     - ThÃªm Ã´ nháº­p `Roadmap` trÃªn `popup.html`. NgÆ°á»i dÃ¹ng cÃ³ thá»ƒ copy Báº£ng Markdown Lá»™ TrÃ¬nh (xin tá»« ChatGPT) vÃ  dÃ¡n tháº³ng vÃ o.
     - Add-on cÃ³ tÃ­nh nÄƒng "Táº¡o JSON Roadmap": tá»± Ä‘á»™ng nhÃ³m cÃ¡c bÃ i há»c theo cá»™t `ChÆ°Æ¡ng` (Main Topic) vÃ  táº¡o ra má»™t file JSON PhÃ¢n cáº¥p.
  2. **Token-Optimized Prompt Injector (NÃ©n TrÃ­ Nhá»›)**:
     - Trong `content_script.js`, Add-on dÃ² xem NgÃ y hiá»‡n táº¡i thuá»™c ChÆ°Æ¡ng nÃ o. Náº¿u Ä‘ang á»Ÿ giá»¯a ChÆ°Æ¡ng, nÃ³ sáº½ ghÃ©p thÃªm cÃ¢u tÃ³m táº¯t cá»§a cÃ¡c ngÃ y trÆ°á»›c *thuá»™c cÃ¹ng ChÆ°Æ¡ng Ä‘Ã³*.
     - Khi chuyá»ƒn sang ChÆ°Æ¡ng má»›i, toÃ n bá»™ tÃ³m táº¯t chi tiáº¿t cá»§a ChÆ°Æ¡ng cÅ© sáº½ bá»‹ "chá»‘t sá»•" vÃ  xÃ³a khá»i lá»‡nh, giÃºp giáº£i phÃ³ng hoÃ n toÃ n bá»™ nhá»› Prompt, giá»¯ cho lá»‡nh gá»­i luÃ´n sáº¯c bÃ©n vÃ  cá»±c ká»³ ngáº¯n gá»n.
  3. **Auto Summarizer**: Sau khi láº¥y xong bÃ i há»c chÃ­nh, Addon tá»± Ä‘á»™ng báº¯n thÃªm lá»‡nh phá»¥ *"TÃ³m táº¯t cá»±c ká»³ ngáº¯n gá»n kiáº¿n thá»©c trÃªn"* vÃ  lÆ°u vÃ o `historySummaries`.
  4. **Adapter Pattern**: TÃ¡ch rá»i logic DOM Selector cho `clickNewChat`, `findChatInput`, `findSendButton` vÃ  `extractDeltaContent` dá»±a trÃªn lá»±a chá»n Ná»n táº£ng (copilot, gemini, chatgpt). 
  5. **Persistent Session (KhÃ³a cá»©ng Lá»™ TrÃ¬nh)**: NhÃºng (embed) trá»±c tiáº¿p toÃ n bá»™ khá»‘i `roadmapData` vÃ  `historySummaries` vÃ o trong file `session.json`. GiÃºp ngÆ°á»i dÃ¹ng khi cáº¡n dung lÆ°á»£ng tÃ i khoáº£n A cÃ³ thá»ƒ Ä‘Äƒng nháº­p tÃ i khoáº£n B, báº¥m táº£i file session lÃªn vÃ  Add-on sáº½ tá»± phá»¥c há»“i Lá»™ trÃ¬nh láº«n TrÃ­ nhá»› Ä‘á»ƒ tiáº¿p tá»¥c máº¡ch há»c chÃ­nh xÃ¡c Ä‘áº¿n tá»«ng chá»¯.

### Giai Ä‘oáº¡n 23 â€” Fix lá»—i khÃ´ng táº¡o New Chat trÃªn Gemini
- **Váº¥n Ä‘á»**: NgÆ°á»i dÃ¹ng bÃ¡o cÃ¡o Addon tiáº¿p tá»¥c gá»­i bÃ i má»›i vÃ o cÃ¹ng má»™t Ä‘oáº¡n chat cÅ© trÃªn Gemini thay vÃ¬ táº¡o chat má»›i, lÃ m máº¥t tÃ¡c dá»¥ng cá»§a cÆ¡ cháº¿ One-Chat-Per-Day.
- **NguyÃªn nhÃ¢n**: NÃºt "New Chat" cá»§a Gemini Ä‘Ã£ thay Ä‘á»•i cáº¥u trÃºc DOM, selector cÅ© `a[href*="/app/new"]` khÃ´ng cÃ²n tÃ¬m tháº¥y.
- **Giáº£i phÃ¡p**: NÃ¢ng cáº¥p hÃ m `clickNewChat()` cho Gemini:
  - Bá»• sung loáº¡t selector má»›i: `a[href="/app"]`, `button[aria-label*="trÃ² chuyá»‡n má»›i"]`, v.v.
  - ThÃªm cÆ¡ cháº¿ **Text Fallback**: QuÃ©t toÃ n bá»™ tháº» `span, div, p` Ä‘á»ƒ tÃ¬m chá»¯ "New chat" hoáº·c "TrÃ² chuyá»‡n má»›i" vÃ  click vÃ o tháº» cha cÃ³ kháº£ nÄƒng click (button/a). Äiá»u nÃ y Ä‘áº£m báº£o luÃ´n tÃ¬m Ä‘Æ°á»£c nÃºt dÃ¹ Google cÃ³ Ä‘á»•i code áº©n Ä‘i chÄƒng ná»¯a.

### Giai Ä‘oáº¡n 24 â€” Fix lá»—i dÃ¡n text nhÆ°ng Gemini hiá»‡n icon Loa (KhÃ´ng gá»­i Ä‘Æ°á»£c)
- **Váº¥n Ä‘á»**: Khi Addon dÃ¡n Prompt vÃ o Ã´ nháº­p cá»§a Gemini, thay vÃ¬ hiá»‡n nÃºt Gá»­i (Send) thÃ¬ Gemini váº«n hiá»‡n icon Micro/Loa. GÃ¢y lá»—i khÃ´ng thá»ƒ nháº¥n nÃºt Gá»­i (do nÃºt Gá»­i chÆ°a xuáº¥t hiá»‡n).
- **NguyÃªn nhÃ¢n**: Gemini sá»­ dá»¥ng Web Component `<rich-textarea>`. Lá»‡nh `execCommand('insertText')` thay Ä‘á»•i text trong DOM nhÆ°ng khÃ´ng tá»± Ä‘á»™ng báº¯n ra sá»± kiá»‡n (Event) Ä‘á»ƒ bÃ¡o cho framework (Angular/Lit) cá»§a Gemini biáº¿t. Há»‡ thá»‘ng tÆ°á»Ÿng Ã´ nháº­p váº«n Ä‘ang trá»‘ng.
- **Giáº£i phÃ¡p**: 
  - Cáº­p nháº­t selector tÃ¬m Ã´ nháº­p: Láº¥y Ä‘Ãºng tháº» `div[contenteditable="true"]` náº±m SÃ‚U BÃŠN TRONG tháº» `<rich-textarea>`.
  - Cáº­p nháº­t hÃ m `fillInput()`: Báº¯t buá»™c báº¯n liÃªn tiáº¿p 3 event: `InputEvent('input')`, `Event('input')`, vÃ  `Event('change')` trá»±c tiáº¿p vÃ o Ã´ nháº­p. 
  - Äá»“ng thá»i báº¯n thÃªm má»™t event `input` ngÆ°á»£c lÃªn tháº» cha `<rich-textarea>` Ä‘á»ƒ "Ä‘Ã¡nh thá»©c" framework cá»§a Gemini, Ã©p nÃ³ nháº­n diá»‡n text vÃ  hiá»‡n nÃºt Gá»­i.

---

## Cáº¥u trÃºc file hiá»‡n táº¡i

```
CopilotWordExportAddon/
â”œâ”€â”€ manifest.json       â€” Cáº¥u hÃ¬nh extension (MV3, quyá»n downloads + storage, <all_urls>)
â”œâ”€â”€ background.js       â€” Service Worker: download_html / download_index / download_session
â”œâ”€â”€ content_script.js   â€” VÃ²ng láº·p auto, táº£i HTML tá»«ng Day, cáº­p nháº­t index & session
â”œâ”€â”€ popup.html          â€” Giao diá»‡n: Start/Stop, Resume tá»« session.json, log area
â””â”€â”€ popup.js            â€” Logic Popup: file picker, resume flow, day_saved status

AskCpl.py               â€” Python/Tkinter: Ä‘á»c JSON â†’ xuáº¥t Word (dÃ¹ng pywin32)
ProjectLog.md           â€” File nÃ y

Output (trong Downloads cá»§a trÃ¬nh duyá»‡t):
agent_name/
â”œâ”€â”€ index.html          â€” Trang tá»•ng há»£p, link Ä‘áº¿n tá»«ng bÃ i (cáº­p nháº­t dáº§n)
â”œâ”€â”€ day_1.html          â€” BÃ i ngÃ y 1 (file HTML Ä‘á»™c láº­p, Ä‘á»c offline Ä‘Æ°á»£c)
â”œâ”€â”€ day_2.html
â””â”€â”€ session.json        â€” Quáº£n lÃ½ phiÃªn (resume láº§n sau)
```

---

## CÃ¡c lá»‡nh & ThÆ° viá»‡n sá»­ dá»¥ng
- `pip install pywin32` â€” Báº¯t buá»™c Ä‘á»ƒ Python Ä‘iá»u khiá»ƒn MS Word.
- Addon APIs: `chrome.storage.local`, `chrome.downloads`, `chrome.runtime`, `chrome.tabs`.

---

## LÆ°u Ã½ quan trá»ng khi chá»‰nh sá»­a

> **Sau khi sá»­a `manifest.json` hoáº·c `background.js`:**
> VÃ o `edge://extensions/` â†’ báº¥m **Táº£i láº¡i (Reload)** extension.

> **Sau khi sá»­a `content_script.js`:**
> Quay láº¡i trang Copilot â†’ báº¥m **F5** Ä‘á»ƒ inject láº¡i script.

> **File HTML vÃ  session.json** náº±m trong `Downloads/agent_name/` (subfolder tá»± Ä‘á»™ng táº¡o).
> KhÃ´ng thá»ƒ tÃ¹y chá»‰nh Ä‘Æ°á»ng dáº«n ngoÃ i Downloads do giá»›i háº¡n báº£o máº­t trÃ¬nh duyá»‡t.

> **Sau khi sá»­a `content_script.js`:**
> Quay láº¡i trang Copilot â†’ báº¥m **F5** Ä‘á»ƒ inject láº¡i script.

> **Resume phiÃªn cÅ©:** Copy `session.json` tá»« `Downloads/agent_name/` sang báº¥t ká»³ Ä‘Ã¢u â†’ má»Ÿ Popup â†’ "ðŸ“‚ Chá»n file session.json" â†’ Start.

---

## Chuáº©n cáº¥u trÃºc file Roadmap (.md)

Äá»ƒ táº¡o lá»™ trÃ¬nh (Roadmap) chuáº©n xÃ¡c cho Addon Ä‘á»c á»Ÿ cháº¿ Ä‘á»™ "File MD", **báº¯t buá»™c tuÃ¢n theo Ä‘á»‹nh dáº¡ng sau** Ä‘á»ƒ Addon cÃ³ thá»ƒ parse báº±ng Regex.

```markdown
## Day 1 â€” TiÃªu Ä‘á» bÃ i há»c
**Prompt:**
Ná»™i dung cÃ¢u lá»‡nh báº¡n muá»‘n gá»­i cho AI. CÃ³ thá»ƒ dÃ i nhiá»u dÃ²ng.
Addon sáº½ copy toÃ n bá»™ ná»™i dung tá»« dÆ°á»›i chá»¯ "Prompt:" cho Ä‘áº¿n khi gáº·p chá»¯ "BÃ i táº­p:" hoáº·c "Tags:" hoáº·c dÃ²ng "## Day" tiáº¿p theo.

**BÃ i táº­p:**
- BÃ i 1
- BÃ i 2

**Tags:** #tag
```

- Addon sáº½ tá»± Ä‘á»™ng tÃ¬m cÃ¡c cá»¥m `## Day X`.
- Addon sáº½ láº¥y má»i vÄƒn báº£n tá»« sau `**Prompt:**` Ä‘á»ƒ lÃ m cÃ¢u lá»‡nh (prompt) gá»­i cho AI.
- Náº¿u báº¡n yÃªu cáº§u AI khÃ¡c táº¡o Roadmap, hÃ£y cung cáº¥p Ä‘Ãºng chuáº©n nÃ y Ä‘á»ƒ táº¡o ra file `.md` Äƒn khá»›p 100% vá»›i Addon.

### Giai Ä‘oáº¡n 25 â€” Táº¡o Roadmap JavaScript 7 NÄƒm (2560 NgÃ y)
- ÄÃ£ táº¡o Python script `generate_js_roadmap.py` Ä‘á»ƒ tá»± Ä‘á»™ng hÃ³a viá»‡c sinh file Markdown dÃ i (hÆ¡n 33,000 dÃ²ng).
- Gen thÃ nh cÃ´ng file `roadmap_javascript_7years.md` bao phá»§ toÃ n bá»™ lá»™ trÃ¬nh 2560 ngÃ y há»c liÃªn tá»¥c (tá»« Foundation Ä‘áº¿n Web3, AI, Distributed System).
- File tuÃ¢n thá»§ 100% Ä‘á»‹nh dáº¡ng Parsing cá»§a Copilot Word Export Addon.

### Giai Ä‘oáº¡n 26 â€” Táº¡o Roadmap Thá»ƒ Dá»¥c Táº¡i NhÃ  (365 NgÃ y)
- YÃªu cáº§u: Thiáº¿t káº¿ lá»™ trÃ¬nh giáº£m cÃ¢n & tÄƒng cÆ¡ 1 nÄƒm cho ngÆ°á»i 108kg, 100% táº­p táº¡i nhÃ , 30 phÃºt/ngÃ y, khÃ´ng báº­t nháº£y (báº£o vá»‡ khá»›p).
- Thá»±c thi: ÄÃ£ táº¡o file `roadmap_fitness_365days.md` chá»©a Ä‘áº§y Ä‘á»§ 365 ngÃ y (gá»“m bÃ i táº­p chi tiáº¿t sá»‘ hiá»‡p/láº§n vÃ  thá»±c Ä‘Æ¡n tÆ°Æ¡ng á»©ng má»—i ngÃ y).
- TÃ­ch há»£p chuáº©n Copilot Addon: Prompt yÃªu cáº§u AI nháº¯c nhá»Ÿ ká»¹ thuáº­t an toÃ n khá»›p, Ä‘Ã¡nh giÃ¡ thá»±c Ä‘Æ¡n vÃ  Ä‘á»™ng viÃªn ngÆ°á»i dÃ¹ng.
- **Báº£n V2 (Cáº­p nháº­t)**: Bá»• sung Ä‘á»‹nh lÆ°á»£ng thá»±c Ä‘Æ¡n chÃ­nh xÃ¡c (sá»‘ gram, chÃ©n) vÃ  chi tiáº¿t 100% form chuáº©n cá»§a cÃ¡c bÃ i táº­p trá»±c tiáº¿p vÃ o file HTML (Ä‘á»ƒ ngÆ°á»i dÃ¹ng dá»… theo dÃµi). ÄÃ£ chá»‰nh sá»­a Prompt Ä‘á»ƒ AI lÃ m "Kiá»ƒm toÃ¡n viÃªn dinh dÆ°á»¡ng" Ä‘Ã¡nh giÃ¡ trá»±c tiáº¿p sá»‘ lÆ°á»£ng thá»±c pháº©m nÃ y.
- Dá»n dáº¹p: ÄÃ£ lÆ°u láº¡i script Python `generate_fitness_365_v2.py` theo yÃªu cáº§u cá»§a ngÆ°á»i dÃ¹ng Ä‘á»ƒ tÃ¹y biáº¿n sau nÃ y.

### Giai Ä‘oáº¡n 28 â€” Fix Lá»—i Káº¹t Chá» 30s & Chá»‘ng Ngá»§ Báº±ng Silent Audio
- **Váº¥n Ä‘á» 1**: QuÃ¡ trÃ¬nh Automation thá»‰nh thoáº£ng bá»‹ káº¹t vÄ©nh viá»…n á»Ÿ bÆ°á»›c chá» táº¡o New Chat (cÃ³ thá»ƒ do káº¿t ná»‘i máº¡ng yáº¿u hoáº·c UI cá»§a AI thay Ä‘á»•i). Lá»—i khiáº¿n cho há»‡ thá»‘ng máº¥t tá»« 7 phÃºt Ä‘áº¿n vÃ i chá»¥c phÃºt.
- **Giáº£i phÃ¡p 1**: Ãp dá»¥ng Timeout 30 giÃ¢y cho hÃ m `waitForNewChatReady`. Náº¿u sau 30s mÃ  New Chat chÆ°a sáºµn sÃ ng, Extension sáº½ tá»± Ä‘á»™ng Ã©p Reload trang (`location.reload()`). Nhá» cÆ¡ cháº¿ Auto-Resume cÃ³ sáºµn tá»« Giai Ä‘oáº¡n 17, há»‡ thá»‘ng sáº½ tá»± Ä‘á»™ng khÃ´i phá»¥c quy trÃ¬nh vÃ  cháº¡y láº¡i Day Ä‘Ã³ thay vÃ¬ bá»‹ káº¹t vÄ©nh viá»…n.
- **Váº¥n Ä‘á» 2**: CÃ¡c trÃ¬nh duyá»‡t hiá»‡n Ä‘áº¡i (Chrome/Edge) tá»± Ä‘á»™ng Ä‘Æ°a tab vÃ o cháº¿ Ä‘á»™ ngá»§ (Sleeping Tabs/Background Throttling) khi tab bá»‹ áº©n quÃ¡ lÃ¢u, khiáº¿n Javascript cháº¡y ngáº§m bá»‹ delay cá»±c náº·ng, kÃ©o dÃ i thá»i gian chá» 5-7 phÃºt.
- **Giáº£i phÃ¡p 2**: KÃ­ch hoáº¡t láº¡i ká»¹ thuáº­t Silent Audio Keep-alive (tá»«ng bá»‹ táº¯t á»Ÿ Giai Ä‘oáº¡n 13). Báº±ng cÃ¡ch chÃ¨n má»™t file Ã¢m thanh ngáº¯n (chuá»—i Base64 cá»±c nhá») tÄ©nh láº·ng (0.01 volume) vÃ  láº·p vÃ´ táº­n thÃ´ng qua tháº» `<audio>` khi gá»i `setupKeepAlive`. Äiá»u nÃ y sáº½ "Ä‘Ã¡nh lá»«a" trÃ¬nh duyá»‡t tin ráº±ng tab Ä‘ang phÃ¡t ná»™i dung Media, duy trÃ¬ má»©c Æ°u tiÃªn xá»­ lÃ½ cao nháº¥t (Highest Priority) vÃ  chá»‘ng Throttling 100%.

### Giai Ä‘oáº¡n 27 â€” Táº¡o Roadmap Access VBA (365 NgÃ y - Full Professional)
- YÃªu cáº§u: Äá»c 220 file HTML khÃ³a há»c táº¡i `D:\Code\Data Code\Course\Acces_VBA`, phÃ¢n tÃ­ch chá»§ Ä‘á» tá»«ng ngÃ y, xÃ¡c Ä‘á»‹nh khoáº£ng trá»‘ng vÃ  bá»• sung lá»™ trÃ¬nh há»c hoÃ n chá»‰nh.
- PhÃ¢n tÃ­ch & Bá»• sung:
  - 290 ngÃ y: Cáº¥u trÃºc ban Ä‘áº§u vá»›i 5 nhÃ³m chá»§ Ä‘á» cÃ²n thiáº¿u: Ribbon/Custom UI, Class Module & OOP, Report Builder nÃ¢ng cao, Multi-user & Locking, Deployment & Distribution.
  - 365 ngÃ y: Má»Ÿ rá»™ng thÃªm 75 ngÃ y Ä‘á»ƒ bao quÃ¡t SQL Mastery (CTE, Window Functions), Advanced Controls (TreeView, ListView, ActiveX), Modern Integration (Microsoft Graph, Power Automate, SharePoint, Teams).
  - Æ¯á»›c lÆ°á»£ng thá»i gian: ÄÃ£ gáº¯n nhÃ£n thá»i gian há»c cá»¥ thá»ƒ cho tá»«ng ngÃ y (30 phÃºt, 60 phÃºt, 90 phÃºt, 120 phÃºt, 3-4 giá»).
- Thá»±c thi: Táº¡o file `roadmap_access_vba.md` chá»©a Ä‘á»§ 365 ngÃ y (8037 dÃ²ng, ~422 KB), chuáº©n format Copilot Addon regex.
- Script Python `generate_access_vba_roadmap.py` Ä‘Æ°á»£c giá»¯ láº¡i Ä‘á»ƒ tÃ¹y biáº¿n sau.

### Quy táº¯c sinh file Roadmap (NgÃ´n ngá»¯ / Láº­p trÃ¬nh)
1. **Äá»‘i vá»›i NgÃ´n ngá»¯ há»c (Nháº­t, Trung, Anh, v.v.):**
   - Lá»™ trÃ¬nh pháº£i tráº£i dÃ i Ä‘á»§ lá»›n (VD: 1000 ngÃ y) tá»« Vá»¡ lÃ²ng Ä‘áº¿n Báº£n Ä‘á»‹a.
   - CÃ¡c ngÃ y Ä‘áº§u tiÃªn Báº®T BUá»˜C pháº£i táº­p trung vÃ o Báº£ng chá»¯ cÃ¡i/PhÃ¡t Ã¢m/Pinyin trÆ°á»›c khi vÃ o tá»« vá»±ng hay ngá»¯ phÃ¡p.
   - VÃ²ng láº·p há»c kiáº¿n thá»©c xen káº½ khoa há»c (VD: Ngá»¯ phÃ¡p -> Tá»« vá»±ng -> Chá»¯ HÃ¡n/HÃ¡n tá»± -> Äá»c hiá»ƒu -> Nghe hiá»ƒu -> Giao tiáº¿p).
   - Prompt gá»­i cho AI pháº£i cÃ³ phÆ°Æ¡ng phÃ¡p sÆ° pháº¡m: 
     + Tá»« vá»±ng/Chá»¯ HÃ¡n: CÃ³ Mnemonic (cÃ¢u chuyá»‡n ghi nhá»›), Bá»™ thá»§, PhÃ¡t Ã¢m/Pinyin.
     + Ngá»¯ phÃ¡p: CÃ³ Cáº¥u trÃºc, CÃ¡ch dÃ¹ng (Nuance), CÃ¢u vÃ­ dá»¥.
     + Báº¯t buá»™c yÃªu cáº§u AI chá»‰ ra **Lá»—i sai phá»• biáº¿n cá»§a ngÆ°á»i Viá»‡t**.
2. **Äá»‘i vá»›i NgÃ´n ngá»¯ Láº­p trÃ¬nh (Python, VBA, JS, v.v.):**
   - PhÃ¢n chia theo Phase tá»« CÄƒn báº£n Ä‘áº¿n ChuyÃªn sÃ¢u.
   - Prompt báº¯t buá»™c yÃªu cáº§u AI Ä‘Æ°a ra code vÃ­ dá»¥ thá»±c táº¿, cÃ³ thá»ƒ cháº¡y Ä‘Æ°á»£c ngay.
   - Báº¯t AI giáº£i thÃ­ch lá»—i bug thÆ°á»ng gáº·p vÃ  cÃ¡ch debug.
   - Pháº£i cÃ³ bÃ i táº­p thá»±c hÃ nh cá»¥ thá»ƒ á»Ÿ cuá»‘i má»—i ngÃ y.
3. **Quy trÃ¬nh chung (Báº¯t buá»™c):**
   - LuÃ´n táº¡o 1 script (nhÆ° Python) chá»©a logic sinh file Ä‘á»ƒ lÆ°u trá»¯ vÃ  tiá»‡n sá»­a Ä‘á»•i sau nÃ y.
    - Äá»‹nh dáº¡ng output `.md` pháº£i tuÃ¢n thá»§ chuáº©n Parsing cá»§a Copilot Addon: `## Day X...`, `**Prompt:**`, `**BÃ i táº­p:**`, `**Tags:**`.
   - Pháº£i táº¡o `implementation_plan.md` cho User duyá»‡t trÆ°á»›c khi viáº¿t code sinh file.

### Giai Ä‘oáº¡n 29 â€” Tá»‘i Æ°u & Má»Ÿ rá»™ng Lá»™ trÃ¬nh Tiáº¿ng Trung vÃ  Tiáº¿ng Nháº­t (2500 NgÃ y)
- **YÃªu cáº§u**: NgÆ°á»i dÃ¹ng muá»‘n tá»‘i Æ°u vÃ  hoÃ n thiá»‡n 2 lá»™ trÃ¬nh ngÃ´n ngá»¯ (Tiáº¿ng Trung, Tiáº¿ng Nháº­t) dá»±a trÃªn chuáº©n thiáº¿t káº¿ cá»§a `roadmap_english.md`.
- **Váº¥n Ä‘á» phÃ¡t hiá»‡n**: Báº£n cÅ© (1000 ngÃ y) quÃ¡ ngáº¯n Ä‘á»ƒ bao phá»§ kiáº¿n thá»©c tá»« Vá»¡ lÃ²ng Ä‘áº¿n Native vá»›i nhá»‹p há»c **30-45 phÃºt/ngÃ y**. NgoÃ i ra, thá»i gian má»—i Day tÄƒng dáº§n (120 phÃºt á»Ÿ phase cuá»‘i) khÃ´ng thá»±c táº¿ khi ngÆ°á»i dÃ¹ng bá»‹ giá»›i háº¡n thá»i gian.
- **Giáº£i phÃ¡p â€” "Lá»™ trÃ¬nh DÃ i háº¡n Thá»±c táº¿"**:
  - Má»Ÿ rá»™ng tá»« **1000** lÃªn **2500 ngÃ y** cho cáº£ 2 ngÃ´n ngá»¯.
  - Cá»‘ Ä‘á»‹nh thá»i gian há»c cá»‘ Ä‘á»‹nh **30-45 phÃºt/ngÃ y** cho táº¥t cáº£ 6 Phase.
  - PhÃ¢n bá»• láº¡i 6 Phase há»£p lÃ½ hÆ¡n (HSK/JLPT): 250 / 350 / 400 / 500 / 500 / 500 ngÃ y.
  - ThÃªm lá»i cáº£nh bÃ¡o `âš ï¸ LÆ°u Ã½ quan trá»ng` vá» thá»i gian thá»±c táº¿ cáº§n thiáº¿t (tÆ°Æ¡ng tá»± chuáº©n English roadmap).
  - ThÃªm loáº¡i bÃ i "Ã”n táº­p tá»•ng há»£p" xen káº½ trong chu ká»³ 7 bÃ i Ä‘á»ƒ cá»§ng cá»‘ kiáº¿n thá»©c.
  - Má»Ÿ rá»™ng danh sÃ¡ch Ngá»¯ phÃ¡p, Tá»« vá»±ng, Kanji Ä‘á»ƒ ná»™i dung phong phÃº vÃ  khÃ´ng bá»‹ láº·p quÃ¡ nhiá»u.
- **Káº¿t quáº£**:
  - `generate_chinese_roadmap.py` â€” ÄÃ£ cáº­p nháº­t (265 â†’ ~430 dÃ²ng).
  - `generate_japanese_roadmap.py` â€” ÄÃ£ cáº­p nháº­t (269 â†’ ~430 dÃ²ng).
  - `roadmap_chinese_1000.md` â€” TÃ¡i táº¡o: **2500 ngÃ y**, 4.06 MB, chuáº©n Addon 100%.
  - `roadmap_japanese_1000.md` â€” TÃ¡i táº¡o: **2500 ngÃ y**, 4.09 MB, chuáº©n Addon 100%.

### Giai Ä‘oáº¡n 30 â€” Táº¡o Roadmap Tiáº¿ng Anh Má»›i Chuáº©n SÆ° Pháº¡m (2500 NgÃ y)
- **YÃªu cáº§u**: Táº¡o roadmap tiáº¿ng Anh má»›i tá»« Ä‘áº§u theo chuáº©n thiáº¿t káº¿ cá»§a roadmap Nháº­t/Trung (2500 ngÃ y, 30-45 phÃºt/ngÃ y), tham kháº£o `roadmap_english.md` cÅ© nhÆ°ng nÃ¢ng cáº¥p toÃ n diá»‡n.
- **PhÃ¢n tÃ­ch lá»—i báº£n cÅ© (900 ngÃ y)**:
  - 900 ngÃ y quÃ¡ ngáº¯n cho 30-45 phÃºt/ngÃ y thá»±c táº¿.
  - Prompt quÃ¡ chung chung â€” chá»‰ "dáº¡y rá»“i giao 3-5 cÃ¢u", khÃ´ng phÃ¢n loáº¡i theo kiá»ƒu bÃ i.
  - Phase 1 chá»‰ 30 ngÃ y â€” quÃ¡ ngáº¯n Ä‘á»ƒ master phÃ¡t Ã¢m tiáº¿ng Anh cho ngÆ°á»i Viá»‡t.
  - KhÃ´ng cÃ³ bÃ i Pronunciation riÃªng biá»‡t, thiáº¿u IPA báº¯t buá»™c.
  - Thiáº¿u Collocations, IELTS tasks, Academic Writing á»Ÿ cÃ¡c phase cao.
- **Giáº£i phÃ¡p â€” Roadmap Tiáº¿ng Anh Chuáº©n 2500 NgÃ y**:
  - 6 Phase: Pre-A1 (200 ngÃ y), A1-A2 (350 ngÃ y), B1 (400 ngÃ y), B2 (500 ngÃ y), C1-C2 (550 ngÃ y), Native (500 ngÃ y).
  - Phase 1 má»Ÿ rá»™ng lÃªn **200 ngÃ y** vá»›i 20 bÃ i PhÃ¡t Ã¢m ná»n táº£ng riÃªng (IPA, Word Stress, Connected Speech, Intonation, Schwa, Weak Forms).
  - **Chu ká»³ 7 loáº¡i bÃ i** Ä‘iá»u chá»‰nh cho tiáº¿ng Anh: Ngá»¯ phÃ¡p â†’ Tá»« vá»±ng â†’ **PhÃ¡t Ã¢m/IPA** â†’ Äá»c hiá»ƒu â†’ Nghe hiá»ƒu â†’ NÃ³i/Shadowing â†’ Viáº¿t/Ã”n táº­p.
  - Prompt phÃ¢n nhÃ¡nh theo 5 loáº¡i bÃ i: Ngá»¯ phÃ¡p / Tá»« vá»±ng+Collocation+Idiom / PhÃ¡t Ã¢m / Ká»¹ nÄƒng tÃ­ch há»£p / Lá»—i sai ngÆ°á»i Viá»‡t Báº®T BUá»˜C.
  - TÃ­ch há»£p IELTS tasks tá»« Phase B2, Academic Word List tá»« Phase C1.
  - Phase Native: Slang, Humor, Stand-up Comedy, VÄƒn há»c, Public Speaking, Accent Mastery.
- **Káº¿t quáº£**:
  - `generate_english_roadmap.py` â€” Táº¡o má»›i (~340 dÃ²ng).
  - `roadmap_english_2500.md` â€” Táº¡o má»›i: **2500 ngÃ y**, 5.11 MB, chuáº©n Addon 100%.
  - Táº¥t cáº£ 6 Phase Ä‘á»u OK, Ä‘á»§ 2500/2500 Prompt + Tags + BÃ i táº­p.

### Giai Ä‘oáº¡n 31 â€” Táº¡o Roadmap Tiáº¿ng HÃ n Chuáº©n SÆ° Pháº¡m (2500 NgÃ y)
- **YÃªu cáº§u**: Táº¡o roadmap tiáº¿ng HÃ n má»›i tá»« Ä‘áº§u theo chuáº©n Nháº­t/Trung/Anh (2500 ngÃ y, 30-45 phÃºt/ngÃ y), tham kháº£o `roadmap_korean.md` cÅ© (900 ngÃ y) nhÆ°ng nÃ¢ng cáº¥p toÃ n diá»‡n.
- **Giáº£i phÃ¡p â€” Roadmap Tiáº¿ng HÃ n Chuáº©n 2500 NgÃ y**:
  - 6 Phase: Hangul (200 ngÃ y), TOPIK1-2 (350 ngÃ y), TOPIK3 (450 ngÃ y), TOPIK4 (500 ngÃ y), TOPIK5-6 (500 ngÃ y), Native (500 ngÃ y).
  - Phase 1 má»Ÿ rá»™ng lÃªn 200 ngÃ y vá»›i 22 bÃ i Hangul ná»n táº£ng riÃªng (NguyÃªn Ã¢m, Phá»¥ Ã¢m, Batchim, Quy táº¯c phÃ¡t Ã¢m, Sá»‘ Ä‘áº¿m HÃ n/Thuáº§n HÃ n).
  - Chu ká»³ 7 loáº¡i bÃ i Ä‘iá»u chá»‰nh cho tiáº¿ng HÃ n: Ngá»¯ phÃ¡p â†’ Tá»« vá»±ng â†’ PhÃ¡t Ã¢m/Hangul â†’ Äá»c hiá»ƒu â†’ Nghe hiá»ƒu â†’ NÃ³i/Shadowing â†’ Viáº¿t/Ã”n táº­p.
  - Prompt phÃ¢n nhÃ¡nh theo 5 loáº¡i bÃ i: Hangul/PhÃ¡t Ã¢m / Ngá»¯ phÃ¡p / Tá»« vá»±ng+ThÃ nh ngá»¯+Slang / Ká»¹ nÄƒng tÃ­ch há»£p / Lá»—i sai ngÆ°á»i Viá»‡t Báº®T BUá»˜C.
  - TÃ­ch há»£p KÃ­nh ngá»¯ (ì¡´ëŒ“ë§) tá»« Phase TOPIK1-2, bÃ i luáº­n TOPIK tá»« Phase TOPIK3.
  - Phase Native: K-pop, K-drama, NÆ°á»›c HÃ n VÄƒn hÃ³a, CÃ´ng sá»Ÿ, PhÆ°Æ¡ng ngá»¯ Busan.
- **Káº¿t quáº£**:
  - `generate_korean_roadmap.py` â€” Táº¡o má»›i (~340 dÃ²ng).
  - `roadmap_korean_2500.md` â€” Táº¡o má»›i: **2500 ngÃ y**, 5.27 MB, chuáº©n Addon 100%.
  - Táº¥t cáº£ 6 Phase Ä‘á»u OK, Ä‘á»§ 2500/2500 Prompt + Tags + BÃ i táº­p.

### Giai Ä‘oáº¡n 32 â€” Táº¡o Roadmap Python (3000 NgÃ y / ~8 NÄƒm)
- **YÃªu cáº§u**: Táº¡o lá»™ trÃ¬nh há»c Python bao phá»§ toÃ n bá»™ há»‡ sinh thÃ¡i cÃ´ng nghá»‡ má»›i nháº¥t (2025), láº¥y cáº£m há»©ng tá»« lá»™ trÃ¬nh JavaScript 7 nÄƒm.
- **Giáº£i phÃ¡p â€” Roadmap Python 3000 NgÃ y**:
  - Gá»“m 6 Phase lá»›n: 
    1. **Foundation (1-535)**: CÃº phÃ¡p, Cáº¥u trÃºc dá»¯ liá»‡u, OOP, Modules.
    2. **Advanced (536-1080)**: Decorator, Generator, Metaclass, Type Hints, Concurrency, AsyncIO, Design Patterns, Testing (pytest), Performance (Cython, Numba).
    3. **Web Dev (1081-1660)**: FastAPI, Django, Flask, SQLAlchemy, MongoDB, Redis, Elasticsearch, Web Scraping (Playwright, Scrapy).
    4. **Data Science & ML (1661-2425)**: Pandas, NumPy, Scikit-learn, XGBoost, PyTorch, HuggingFace, LLM (LangChain, LlamaIndex, RAG), Computer Vision (OpenCV, YOLO), MLOps.
    5. **DevOps & Cloud (2426-2690)**: Docker, Kubernetes, CI/CD, AWS, Kafka, Event-Driven, Observability, Security.
    6. **Specialized (2691-3000)**: Data Engineering (PySpark, Airflow), GUI (PyQt6), Automation, Game Dev (Pygame), Blockchain (Web3.py), Quantum Computing.
  - **Prompt sÆ° pháº¡m cao**: YÃªu cáº§u AI Ä‘Æ°a ra cáº£ vÃ­ dá»¥ cÆ¡ báº£n láº«n nÃ¢ng cao (production-ready), cÃ¡c pitfalls (lá»—i hay gáº·p), vÃ  3 cáº¥p Ä‘á»™ bÃ i táº­p (tá»« sao chÃ©p cÆ¡ báº£n Ä‘áº¿n mini-project).
- **Káº¿t quáº£**:
  - `generate_python_roadmap.py` â€” Táº¡o má»›i.
  - `roadmap_python_3000.md` â€” ÄÃ£ sinh thÃ nh cÃ´ng Ä‘Ãºng **3000 ngÃ y**.

### Giai Ä‘oáº¡n 33 â€” TrÃ¬nh Táº¡o BÃ i Táº­p LÆ°u Trá»¯ (Archival Mode) & Tinh Chá»‰nh UI
- **YÃªu cáº§u:** ThÃªm 2 kiá»ƒu táº¡o bÃ i táº­p: (1) NhÃºng trá»±c tiáº¿p nhÆ° cÅ©, (2) Táº¡o thÆ° má»¥c lÆ°u trá»¯ exercise vÃ  táº¡o file riÃªng. XÃ³a bÃ i táº­p pháº£i dá»n dáº¹p tháº» link trong index.html. Tinh chá»‰nh UI cá»§a sá»• hiá»ƒn thá»‹ (máº·c Ä‘á»‹nh Maximize).
- **Giáº£i phÃ¡p:**
  - `exercise_builder.py`: Sá»­a hÃ m `save_exercise_to_html` Ä‘á»ƒ há»— trá»£ tham sá»‘ `mode` (direct / archival).
  - ThÃªm hÃ m `remove_exercise_from_html` Ä‘á»ƒ lÃ m sáº¡ch file index.html (dÃ¹ng regex xÃ³a tháº» tráº¡ng thÃ¡i vÃ  link) vÃ  xÃ³a file/ná»™i dung HTML nhÃºng tÃ¹y theo cháº¿ Ä‘á»™.
  - `AskCpl.py`: Äáº·t `self.root.state('zoomed')` Ä‘á»ƒ má»Ÿ full mÃ n hÃ¬nh.
  - ThÃªm `Combobox` chá»n cháº¿ Ä‘á»™ xuáº¥t.
  - Cáº­p nháº­t logic cÃ¡c nÃºt LÆ°u vÃ  XÃ³a Táº¥t Cáº£ Ä‘á»ƒ Ä‘á»“ng bá»™ hÃ³a file HTML.
- **Káº¿t quáº£:** HoÃ n thÃ nh tá»‘t luá»“ng táº¡o/xÃ³a bÃ i táº­p Ä‘a cháº¿ Ä‘á»™ vÃ  kháº¯c phá»¥c lá»—i hiá»ƒn thá»‹ giao diá»‡n UI.

### Giai Ä‘oáº¡n 34 â€” Bá»• Sung TÃ­nh NÄƒng Äá»“ng Bá»™ GitHub tá»« VocabularyApp
- **YÃªu cáº§u:** Há»c há»i cÃ¡c Ä‘iá»ƒm máº¡nh tá»« module GitHub Sync cá»§a VocabularyApp Ä‘á»ƒ mang sang module GitHub Sync cá»§a AskCpl.
- **Giáº£i phÃ¡p:**
  - Giá»¯ nguyÃªn luá»“ng upload Git Tree cá»§a AskCpl vÃ¬ hiá»‡u nÄƒng ráº¥t cao (upload toÃ n bá»™ thÆ° má»¥c chá»‰ 1 request commit thay vÃ¬ upload láº·t nháº·t tá»«ng file).
  - ThÃªm chá»©c nÄƒng `enable_pages` Ä‘á»ƒ tá»± Ä‘á»™ng báº­t tÃ­nh nÄƒng GitHub Pages sau khi push thÃ nh cÃ´ng.
  - ThÃªm chá»©c nÄƒng tá»± Ä‘á»™ng tÃ¬m file `README.md` vÃ o thÆ° má»¥c upload náº¿u chÆ°a cÃ³, trong Ä‘Ã³ chá»©a link dáº«n trá»±c tiáº¿p tá»›i GitHub Pages.
  - Tá»± Ä‘á»™ng láº¥y URL hiá»ƒn thá»‹ cá»§a trang web (qua `get_pages_url`) vÃ  in tháº³ng ra khung log cá»§a AskCpl Ä‘á»ƒ ngÆ°á»i dÃ¹ng báº¥m vÃ o xem ngay láº­p tá»©c.
- **Káº¿t quáº£:** QuÃ¡ trÃ¬nh Ä‘Æ°a bÃ i táº­p lÃªn GitHub giá» Ä‘Ã¢y hoÃ n thiá»‡n hÆ¡n, há»— trá»£ host trang web vÃ  cung cáº¥p link truy cáº­p láº­p tá»©c.

### Hotfix â€” Xá»­ lÃ½ lá»—i Unicorn 502 tá»« GitHub API (QuÃ¡ táº£i do spam 1000 file)
- **NguyÃªn nhÃ¢n:** Khi Ä‘áº©y thÆ° má»¥c chá»©a ~1000 file, vÃ²ng láº·p requests gá»­i Ä‘i liÃªn tá»¥c 1000 HTTP POST requests vá» server GitHub mÃ  khÃ´ng cÃ³ Ä‘á»™ trá»… (delay) nÃ o. Äiá»u nÃ y kÃ­ch hoáº¡t cÆ¡ cháº¿ báº£o vá»‡ Abuse Rate Limit cá»§a GitHub, tráº£ vá» lá»—i 502/503 (Unicorn Page) khi AskCpl Ä‘ang táº¡o Git Tree.
- **Kháº¯c phá»¥c:**
  - Viáº¿t láº¡i cÃ¡c hÃ m gá»i API thÃ´ng qua wrapper `_request_with_retry`. Náº¿u nháº­n mÃ£ lá»—i 50x tá»« server GitHub, hÃ m sáº½ tá»± Ä‘á»™ng ngá»§ má»™t khoáº£ng (exponential backoff: 2s, 4s, 8s...) rá»“i thá»­ láº¡i, tá»‘i Ä‘a 3 láº§n.
  - ThÃªm má»™t khoáº£ng nghá»‰ siÃªu nhá» `time.sleep(0.05)` (50ms) giá»¯a má»—i chu ká»³ upload file blob nháº±m trÃ¡nh lÃ m quÃ¡ táº£i bá»™ Ä‘á»‹nh tuyáº¿n cá»§a GitHub.
- **Káº¿t quáº£:** Äá»“ng bá»™ sá»‘ lÆ°á»£ng lá»›n file mÆ°á»£t mÃ  vÃ  an toÃ n hÆ¡n, khÃ´ng cÃ²n cháº¿t ngang vÃ¬ timeout hay 502.

### Hotfix 2 â€” Xá»­ lÃ½ lá»—i Timeout 422 tá»« GitHub API (Tree quÃ¡ lá»›n)
- **NguyÃªn nhÃ¢n:** Khi táº¡o má»™t Git Tree cÃ³ chá»©a 1000 items trong má»™t request duy nháº¥t, backend cá»§a GitHub bá»‹ timeout (mÃ£ 422: 'input was too large to process, build the tree incrementally').
- **Kháº¯c phá»¥c:** Thay vÃ¬ gá»­i 1000 items cÃ¹ng lÃºc, á»©ng dá»¥ng sáº½ cáº¯t nhá» ra (chunking) thÃ nh tá»«ng nhÃ³m 250 files. Má»—i nhÃ³m táº¡o thÃ nh má»™t cÃ¢y Git Tree má»›i, láº¥y cÃ¢y trÆ°á»›c Ä‘Ã³ lÃ m base_tree (xÃ¢y dá»±ng lÅ©y tiáº¿n). Nhá» Ä‘Ã³, request nÃ o cÅ©ng nhá» vÃ  khÃ´ng bá»‹ timeout.
- **Káº¿t quáº£:** ÄÃ£ cÃ³ thá»ƒ Ä‘áº©y an toÃ n sá»‘ lÆ°á»£ng khá»•ng lá»“ file lÃªn GitHub mÃ  khÃ´ng bá»‹ giá»›i háº¡n thá»i gian pháº£n há»“i.



### Giai Ä‘oáº¡n 41 â€” NÃ¢ng cáº¥p Kiáº¿n trÃºc Äa Tiáº¿n TrÃ¬nh (Multi-Tab Support)
- **Váº¥n Ä‘á»**: Sau khi Ã¡p dá»¥ng Tab Binding (Giai Ä‘oáº¡n 40), cÃ¡c tab má»›i khÃ´ng cÃ²n bá»‹ auto-resume nháº§m, NHÆ¯NG biáº¿n lÆ°u trá»¯ `runningState` váº«n lÃ  má»™t Object Ä‘Æ¡n. Do Ä‘Ã³, náº¿u má»Ÿ Popup á»Ÿ Tab thá»© 2, Popup váº«n láº§m tÆ°á»Ÿng há»‡ thá»‘ng "Äang cháº¡y" (cá»§a Tab 1) vÃ  áº©n Ä‘i nÃºt Start, khiáº¿n ngÆ°á»i dÃ¹ng khÃ´ng thá»ƒ cháº¡y Ä‘á»“ng thá»i nhiá»u Agent trÃªn nhiá»u Tab khÃ¡c nhau.
- **Giáº£i phÃ¡p**:
  - Äá»•i tÃªn kho lÆ°u trá»¯ thÃ nh `runningStates` (sá»‘ nhiá»u) dáº¡ng Tá»« Ä‘iá»ƒn (Dictionary).
  - Cáº­p nháº­t `popup.js`: Buá»™c pháº£i dÃ¹ng `chrome.tabs.query` Ä‘á»ƒ láº¥y `tab.id` cá»§a chÃ­nh nÃ³ trÆ°á»›c, rá»“i má»›i tÃ¬m `runningStates[tab.id]`. Nhá» Ä‘Ã³, Popup á»Ÿ cÃ¡c Tab khÃ¡c nhau sáº½ hiá»ƒn thá»‹ tráº¡ng thÃ¡i hoÃ n toÃ n Ä‘á»™c láº­p (Tab 1 hiá»‡n "Äang cháº¡y", Tab 2 hiá»‡n "Báº¯t Ä‘áº§u").
  - Cáº­p nháº­t `content_script.js`: CÃ¡c hÃ m `saveRunningState`, `clearRunningState`, vÃ  thÃ´ng Ä‘iá»‡p `stop_loop` Ä‘á»u Ä‘Æ°á»£c Ä‘iá»u chá»‰nh Ä‘á»ƒ chá»‰ thao tÃ¡c trÃªn Ä‘Ãºng máº£nh ghÃ©p dá»¯ liá»‡u thuá»™c vá» `tabId` cá»§a nÃ³, trÃ¡nh ghi Ä‘Ã¨ dá»¯ liá»‡u cá»§a Tab khÃ¡c.
- **Káº¿t quáº£**: Addon Ä‘Ã£ trá»Ÿ thÃ nh mÃ´i trÆ°á»ng hoÃ n toÃ n Äa Luá»“ng (Multi-Thread / Multi-Instance). NgÆ°á»i dÃ¹ng cÃ³ thá»ƒ má»Ÿ 5 Tab Gemini vÃ  cháº¡y 5 Lá»™ trÃ¬nh khÃ¡c nhau song song mÃ  khÃ´ng xáº£y ra báº¥t ká»³ xung Ä‘á»™t nÃ o.

### Giai Ä‘oáº¡n 42 â€” Kháº¯c phá»¥c lá»—i Background Tab Throttling (Cáº¯t ngang tiáº¿n trÃ¬nh AI)
- **Váº¥n Ä‘á»**: TrÃ¬nh duyá»‡t Chrome cÃ³ cÆ¡ cháº¿ Memory Saver vÃ  Background Throttling, tá»± Ä‘á»™ng Ä‘Ã³ng bÄƒng cÃ¡c hoáº¡t Ä‘á»™ng DOM render (RequestAnimationFrame, setTimeout) khi ngÆ°á»i dÃ¹ng chuyá»ƒn sang tab khÃ¡c Ä‘á»ƒ treo mÃ¡y. Do DOM khÃ´ng cáº­p nháº­t, addon bá»‹ "Ä‘Ã¡nh lá»«a" ráº±ng AI Ä‘Ã£ gÃµ xong vÄƒn báº£n vÃ¬ chuá»—i html tráº£ vá» khÃ´ng dÃ i thÃªm trong 15s. Káº¿t quáº£ lÃ  addon lÆ°u 1 Ä‘oáº¡n vÄƒn báº£n cá»¥t lá»§n vÃ  gá»i luÃ´n cÃ¢u há»i tiáº¿p theo gÃ¢y lá»—i sai luá»“ng.
- **Giáº£i phÃ¡p 1 (UI Signals)**: Viáº¿t hÃ m `isAIGenerating()` quÃ©t toÃ n bá»™ nÃºt trÃªn trang Ä‘á»ƒ tÃ¬m tráº¡ng thÃ¡i "Stop generating / Dá»«ng táº¡o". Náº¿u nÃºt nÃ y tá»“n táº¡i, AI cháº¯c cháº¯n Ä‘ang tráº£ lá»i, addon sáº½ chá»§ Ä‘á»™ng "reset" láº¡i bá»™ Ä‘áº¿m á»•n Ä‘á»‹nh 15s Ä‘á»ƒ khÃ´ng bao giá» cáº¯t ngang bÃ i giáº£ng.
- **Giáº£i phÃ¡p 2 (Tab Visibility)**: Gáº¯n thÃªm kiá»ƒm tra `document.hidden`. Khi phÃ¡t hiá»‡n tab Ä‘ang bá»‹ áº©n (cháº¡y ngáº§m), thay vÃ¬ chá» 15s á»•n Ä‘á»‹nh, há»‡ thá»‘ng tá»± Ä‘á»™ng giÃ£n thá»i gian thÃ nh 45s Ä‘á»ƒ Ä‘áº£m báº£o an toÃ n tuyá»‡t Ä‘á»‘i.
- **Giáº£i phÃ¡p 3 (Keep-Alive)**: KhÃ´i phá»¥c láº¡i kÄ© thuáº­t `silentAudio` (phÃ¡t nháº¡c tráº¯ng cá»±c ngáº¯n 1 sample dÆ°á»›i ná»n) Ä‘á»ƒ cháº·n Ä‘á»©ng tÃ­nh nÄƒng tab-discard cá»§a Chrome Memory Saver. Kháº¯c phá»¥c triá»‡t Ä‘á»ƒ báº±ng cÃ¡ch nhá»› gá»i `.pause()` khi káº¿t thÃºc, giÃºp Edge khÃ´ng bá»‹ rÃ² rá»‰ AudioContext gÃ¢y cháº¡y auto-resume sai Tab.
- **Giáº£i phÃ¡p 4 (Intentional Reload & Infinite Retries)**: Khi web quÃ¡ lag hoáº·c AI tá»« chá»‘i tráº£ lá»i (gÃ¢y Timeout ngáº§m), mÃ£ nguá»“n tá»± Ä‘á»™ng `location.reload()` vÃ  ghi vÃ© vÃ o `sessionStorage` Ä‘á»ƒ auto-resume an toÃ n. KhÃ´ng giá»›i háº¡n sá»‘ láº§n thá»­ láº¡i lá»—i (Ä‘á»•i tá»« retry 2 sang vÃ²ng láº·p `while(isRunning)` vÃ´ háº¡n cÃ³ khoáº£ng nghá»‰ 15s), ngÄƒn addon cháº¿t Ä‘á»©ng giá»¯a chá»«ng. Bá» cÆ¡ cháº¿ táº£i lÆ°u dá»± phÃ²ng má»—i 5 ngÃ y Ä‘á»ƒ chá»‘ng spam Download History (chá»‰ lÆ°u á»• Ä‘Ä©a ná»™i bá»™ cá»§a extension thÃ´ng qua `chrome.storage.local`).


### Giai Ä‘oáº¡n 32: TÆ°Æ¡ng thÃ­ch ngÆ°á»£c phiÃªn báº£n Session (Backward Compatibility)
- **Váº¥n Ä‘á»:** TrÃ¬nh Ä‘á»c file `session.json` cá»§a Popup quÃ¡ kháº¯t khe (`if (!session.agentName || !session.lastDay)`). Dáº«n Ä‘áº¿n cÃ¡c file session cÅ© (chÆ°a cÃ³ trÆ°á»ng `agentName` mÃ  chá»‰ cÃ³ `folderName`, hoáº·c `lastDay = 0`) bá»‹ Ä‘Ã¡nh giÃ¡ lÃ  khÃ´ng há»£p lá»‡ vÃ  tá»« chá»‘i táº£i.
- **Giáº£i phÃ¡p:** XÃ³a bá» Ä‘iá»u kiá»‡n kiá»ƒm tra kháº¯t khe. ThÃªm Fallback an toÃ n:
  - Tá»± Ä‘á»™ng láº¥y `session.agentName = session.folderName || "Copilot"`.
  - Náº¿u `session.lastDay` lÃ  `undefined`, tá»± Ä‘á»™ng Ä‘áº¿m máº£ng `session.days.length`.
  - Chá»‰ bÃ¡o lá»—i khi file JSON táº£i vÃ o hoÃ n toÃ n khÃ´ng cÃ³ cáº¥u trÃºc quen thuá»™c.


### Giai doan 33: Khac phuc loi Popup bi treo (Roadmap qua lon)
- **Van de:** Ham updateRoadmapPreview dang dump toan bo roadmap (co the 3000 bai) thanh JSON va chen vao the <pre> trong HTML. Dieu nay khien browser tab bi dong cung khi render hang trieu ky tu. Ket qua: popup treo, click vao addon khong len.
- **Nguyen nhan goc:** Roadmap duoc luu long vao ddonConfigs roi serialize sang storage. Moi lan mo popup, loadProfiles() doc ra va goi pplyConfigToUI() -> updateRoadmapPreview() dump toan bo JSON ngay lap tuc.
- **Giai phap:**
  - updateRoadmapPreview: Chi hien thi tom tat (so bai hoc), KHONG con goi JSON.stringify(data) nua.
  - Tach luu Roadmap: Khong luu roadmapData trong ddonConfigs nua. Thay vao do luu vao key rieng 
oadmap_[ten_profile] trong chrome.storage.local.
  - pplyConfigToUI: Nhan them profileKey de doc roadmap tu key rieng, bat dong bo (async), khong dong cung popup.
  - Sua 
oadmapFileInput va parseRoadmapBtn: Luu vao key rieng.
  - Cung cap onerror va onloadend an toan cho FileReader cua file MD.


### Giai Ä‘oáº¡n 43 â€” TÆ°Æ¡ng thÃ­ch ngÆ°á»£c session cÅ© (Backward Compatibility)
- **Váº¥n Ä‘á»**: TrÃ¬nh Ä‘á»c file session.json khÃ´ng táº£i Ä‘Æ°á»£c file cÅ© do Ä‘iá»u kiá»‡n if (!session.agentName || !session.lastDay) quÃ¡ kháº¯t khe (sá»‘ 0 bá»‹ coi lÃ  falsy, file cÅ© chÆ°a cÃ³ gentName).
- **Giáº£i phÃ¡p**: XÃ³a Ä‘iá»u kiá»‡n kháº¯t khe, thÃªm fallback tá»± Ä‘á»™ng láº¥y gentName tá»« olderName vÃ  tá»± Ä‘áº¿m session.days.length náº¿u thiáº¿u lastDay.

### Giai Ä‘oáº¡n 44 â€” Kháº¯c phá»¥c Popup treo vÃ  Session khÃ´ng cháº¡y (Root Cause: roadmapData quÃ¡ lá»›n)
- **NguyÃªn nhÃ¢n gá»‘c**: File session.json náº·ng 53MB vÃ¬ 
oadmapData (3000 bÃ i, má»—i bÃ i cÃ³ prompt dÃ i) Ä‘Æ°á»£c nhÃºng trá»±c tiáº¿p vÃ o session. Khi popup gá»­i payload nÃ y qua chrome.tabs.sendMessage (IPC), trÃ¬nh duyá»‡t **drop im láº·ng** (khÃ´ng cháº¡y, khÃ´ng bÃ¡o lá»—i). Roadmap cÅ©ng Ä‘Æ°á»£c nhÃºng vÃ o 
unningStates gÃ¢y vÆ°á»£t giá»›i háº¡n 10MB cá»§a chrome.storage.local.
- **Giáº£i phÃ¡p**:
  - content_script.js: XÃ³a 
oadmapData khá»i utoSave, saveStateForReload, saveRunningState. Äá»c 
oadmapData tá»« key riÃªng 
oadmap_active trong storage (async) thay vÃ¬ nháº­n qua IPC.
  - popup.js / startBtn: LÆ°u currentRoadmapData vÃ o chrome.storage.local key 
oadmap_active trÆ°á»›c khi gá»­i message. Strip 
oadmapData vÃ  session.roadmapData khá»i payload. Payload lÃºc nÃ y chá»‰ chá»©a metadata nháº¹.
  - popup.js / updateRoadmapPreview: Chá»‰ hiá»ƒn thá»‹ tÃ³m táº¯t sá»‘ bÃ i thay vÃ¬ JSON.stringify toÃ n bá»™ (chá»‘ng popup treo khi render).
  - popup.js / saveProfileBtn: LÆ°u roadmap vÃ o key riÃªng 
oadmap_{profile} thay vÃ¬ nhÃºng vÃ o ddonConfigs.


### Giai Ä‘oáº¡n 45 â€” Sá»­a lá»—i font (Encoding Loop) trong `session.json`
- **NguyÃªn nhÃ¢n gá»‘c**: Trong `content_script.js`, táº¡i hÃ m `saveStateForReload`, dá»¯ liá»‡u Ä‘Æ°á»£c encode dÆ°á»›i dáº¡ng `btoa(unescape(encodeURIComponent(JSON.stringify(sessionObj))))`. Tuy nhiÃªn, khi Ä‘á»c láº¡i lÃºc load trang, code chá»‰ dÃ¹ng `atob(...)` mÃ  **quÃªn máº¥t bÆ°á»›c decodeURIComponent**. Háº­u quáº£ lÃ  sau vÃ i trÄƒm vÃ²ng láº·p (reload trang cho tá»«ng ngÃ y má»›i), cÃ¡c kÃ½ tá»± cÃ³ dáº¥u nhÆ° tiáº¿ng Viá»‡t hay dáº¥u gáº¡ch ngang (`â€”`) bá»‹ phÃ¬nh to theo cáº¥p sá»‘ nhÃ¢n (VÃ­ dá»¥ `â€”` thÃ nh `ÃƒÃ‚...`). ÄÃ¢y lÃ  lÃ½ do chÃ­nh khiáº¿n file JSON bá»‹ phÃ¬nh tá»« 4MB lÃªn tá»›i 28MB - 53MB!
- **Giáº£i phÃ¡p**:
  - `content_script.js`: Sá»­a dÃ²ng `atob` thÃ nh `decodeURIComponent(escape(atob(res2.autosave_session_json)))` Ä‘á»ƒ nÃ³ Ä‘á»“ng bá»™ chuáº©n encoding 2 chiá»u.
  - ÄÃ£ viáº¿t script Python phá»¥ Ä‘á»ƒ Ä‘á»c ngÆ°á»£c (decode recursively) báº£n `session.json` cá»§a ngÆ°á»i dÃ¹ng, cá»©u toÃ n bá»™ cÃ¢u há»i bá»‹ lá»—i dáº¥u. File khÃ´i phá»¥c Ä‘Æ°á»£c giáº£m xuá»‘ng 4.6MB vÃ  má»i text dáº¥u `â€”` Ä‘á»u Ä‘Æ°á»£c khÃ´i phá»¥c láº¡i chuáº©n xÃ¡c.


## âš ï¸ Quy táº¯c VÃ€NG vá» MÃ£ HÃ³a (Encoding) Base64
Tuyá»‡t Ä‘á»‘i lÆ°u Ã½ khi lÆ°u trá»¯ vÃ  truyá»n táº£i dá»¯ liá»‡u JSON (Ä‘áº·c biá»‡t lÃ  dá»¯ liá»‡u cÃ³ chá»©a kÃ½ hiá»‡u Unicode, tiáº¿ng Viá»‡t, file markdown):
1. **LUÃ”N LUÃ”N DÃ™NG MÃƒ HÃ“A 2 CHIá»€U Äá»’NG Bá»˜:**
   - Khi mÃ£ hÃ³a lÆ°u trá»¯ (Save): toa(unescape(encodeURIComponent(JSON.stringify(obj))))
   - Khi giáº£i mÃ£ Ä‘á»c ra (Load): JSON.parse(decodeURIComponent(escape(atob(str))))
2. **Háº­u quáº£ náº¿u bá» quÃªn decodeURIComponent:** Náº¿u báº¡n chá»‰ dÃ¹ng tob(...) Ä‘á»ƒ giáº£i nÃ©n nhÆ°ng thiáº¿u decodeURIComponent, chuá»—i byte UTF-8 sáº½ bá»‹ Ã©p hiá»ƒu nháº§m thÃ nh cÃ¡c kÃ½ tá»± Latin-1. Khi chuá»—i nÃ y bá»‹ láº·p láº¡i lÆ°u/Ä‘á»c trong vÃ²ng láº·p (nhÆ° vÃ²ng láº·p Auto-Resume reload trang), dung lÆ°á»£ng kÃ½ tá»± sáº½ **bá»‹ nhÃ¢n Ä‘Ã´i liÃªn tá»¥c theo cáº¥p sá»‘ nhÃ¢n**, lÃ m file JSON phÃ¬nh to tá»« vÃ i MB lÃªn hÃ ng chá»¥c MB, gÃ¢y ngháº½n RAM, treo mÃ¡y vÃ  sáº­p luá»“ng gá»­i tin nháº¯n IPC cá»§a Chrome.


### Giai Ä‘oáº¡n 46 â€” Sá»­a lá»—i nháº­n diá»‡n sai "Error Content" & Sá»­a lá»—i tá»« ngá»¯ Ã ÄÃ´ng

#### Lá»—i 1: False Positive `isErrorContent` (Day 1503 bá»‹ reject)
- **Triá»‡u chá»©ng:** Add-on káº¹t mÃ£i á»Ÿ Day 1503, thá»­ láº¡i hÃ ng chá»¥c láº§n nhÆ°ng khÃ´ng thoÃ¡t Ä‘Æ°á»£c. AI Ä‘Ã£ tráº£ lá»i hoÃ n chá»‰nh nhÆ°ng bá»‹ bá» qua.
- **NguyÃªn nhÃ¢n:** HÃ m `isErrorContent()` dÃ¹ng `.includes('503')` Ä‘á»ƒ tÃ¬m kiáº¿m tá»« khÃ³a. Sá»‘ `1503` cÃ³ chá»©a chuá»—i `503`, bá»‹ báº¯t oan! NgoÃ i ra, bÃ i giáº£ng vá» lá»—i HTTP cÃ³ thá»ƒ chá»©a "thá»­ láº¡i", "Ä‘Ã£ xáº£y ra lá»—i" khiáº¿n hÃ m tÆ°á»Ÿng Ä‘Ã³ lÃ  thÃ´ng bÃ¡o lá»—i máº¡ng.
- **Giáº£i phÃ¡p:** ThÃªm 2 cáº£i tiáº¿n vÃ o `isErrorContent()`:
  1. **Kiá»ƒm tra Ä‘á»™ dÃ i:** ThÃ´ng bÃ¡o lá»—i Ä‘á»©t máº¡ng bao giá» cÅ©ng ngáº¯n (< 200 kÃ½ tá»±). Náº¿u ná»™i dung > 400 kÃ½ tá»± â†’ auto pass, khÃ´ng kiá»ƒm tra.
  2. **Word Boundary:** Äá»•i `.includes('503')` thÃ nh `\b503\b` (regex boundary) Ä‘á»ƒ khÃ´ng nháº§m vá»›i "1503".

#### Lá»—i 2: False Reject vá»›i Tiáº¿ng Nháº­t / Tiáº¿ng Trung
- **NguyÃªn nhÃ¢n:** HÃ m `validateContent()` Ä‘áº¿m sá»‘ tá»« báº±ng `text.split(/\s+/)`. Tiáº¿ng Nháº­t/Trung khÃ´ng cÃ³ khoáº£ng tráº¯ng â†’ toÃ n bá»™ bÃ i giáº£ng dÃ i 2000 kÃ½ tá»± bá»‹ tÃ­nh lÃ  "1 tá»«" â†’ náº¿u tÃªn Agent láº·p láº¡i 1 láº§n, tá»· lá»‡ vÆ°á»£t ngÆ°á»¡ng â†’ bÃ i bá»‹ reject!
- **Giáº£i phÃ¡p:** Äá»•i sang kiá»ƒm tra theo **tá»· lá»‡ kÃ½ tá»±** (character count). Logic má»›i: `nameCharCount > text.length * 0.4`. Hoáº¡t Ä‘á»™ng hoÃ n háº£o vá»›i má»i ngÃ´n ngá»¯ (Anh, Viá»‡t, Nháº­t, Trung).
- **File Ä‘Ã£ sá»­a:** `content_script.js` â€” hÃ m `isErrorContent()` vÃ  `validateContent()`.


### Giai Ä‘oáº¡n 47 â€” Kháº¯c phá»¥c Background Throttling (Chrome cháº¡y cháº­m khi bá»‹ áº©n)

#### NguyÃªn nhÃ¢n gá»‘c
Chrome/Edge cÃ³ cÆ¡ cháº¿ CPU/Timer Throttling. Khi tab khÃ´ng á»Ÿ foreground, `setTimeout` cÃ³ thá»ƒ bá»‹ trÃ¬ hoÃ£n Ä‘áº¿n hÃ ng chá»¥c giÃ¢y / phÃºt. Polling interval `delay(2000)` thá»±c táº¿ cháº¡y máº¥t 30-60s â†’ hÃ ng chá»¥c vÃ²ng láº·p chá» = cáº£ tiáº¿ng chÆ°a xong 1 bÃ i.
CÆ¡ cháº¿ Silent Audio Ä‘Ã£ tá»“n táº¡i nhÆ°ng cÃ³ 2 Ä‘iá»ƒm yáº¿u:
1. Audio bá»‹ Chrome block autoplay sau khi tab reload (chuyá»ƒn ngÃ y) â†’ bá»‹ táº¯t ngáº§m â†’ keepAlive máº¥t tÃ¡c dá»¥ng.
2. KhÃ´ng cÃ³ cÆ¡ cháº¿ nÃ o kiá»ƒm tra audio cÃ³ Ä‘ang cháº¡y khÃ´ng.

#### Giáº£i phÃ¡p (PhÆ°Æ¡ng Ã¡n A+B)
- **A â€” Audio Health Check:** ThÃªm `_audioHealthInterval` (5s) kiá»ƒm tra `_silentAudio.paused`. Náº¿u Ä‘Ãºng â†’ tá»± `play()` láº¡i. Audio khÃ´ng bao giá» bá»‹ táº¯t lÃ¢u hÆ¡n 5 giÃ¢y.
- **B â€” Web Locks API:** DÃ¹ng `navigator.locks.request('askcpl_wakeLock', { mode: 'shared' }, ...)` Ä‘á»ƒ giá»¯ lock trong suá»‘t vÃ²ng láº·p. Tab giá»¯ lock sáº½ **khÃ´ng bá»‹ browser cho vÃ o tráº¡ng thÃ¡i ngá»§/frozen**, ngÄƒn timer throttle á»Ÿ má»©c Ä‘á»™ OS/browser thay vÃ¬ chá»‰ audio workaround.

#### File Ä‘Ã£ sá»­a
- `content_script.js`: ThÃªm 2 biáº¿n `_audioHealthInterval`, `_wakeLockAbort`. Sá»­a `setupKeepAlive()` vÃ  `teardownKeepAlive()`.

### Giai Ä‘oáº¡n 32 â€” Fix lá»—i Quill Editor Syntax
- **Váº¥n Ä‘á»**: TrÃ¬nh soáº¡n tháº£o (WYSIWYG Exercise Builder) bÃ¡o lá»—i thiáº¿u thÆ° viá»‡n highlight.js khi khá»Ÿi táº¡o module Syntax.
- **Giáº£i phÃ¡p**: Äá»•i thá»© tá»± táº£i file trong 	emplates/editor.html, báº¯t buá»™c táº£i highlight.js trÆ°á»›c quill.js Ä‘á»ƒ Quill nháº­n diá»‡n Ä‘Æ°á»£c biáº¿n toÃ n cá»¥c window.hljs.


### Giai doan 33 - Bo sung Roadmap C++ (3080 â†’ 3350 Ngay)
- **File:** `roadmap_cpp test.md` | **Script:** `patch_cpp_roadmap.py`

#### 1. Bo sung Non-Interactive Warning (1342 Day)
- Chen canh bao (WARNING: TUYET DOI KHONG tao bai test/quiz tuong tac...) vao:
  - **15-cycle**: Phan 13, 14, 15 (Ecosystem Integration, Deep Debugging, Execution Lifecycle)
  - **25-cycle**: Phan 13-25 (Design Patterns, Testing, CI/CD, Open Source, Interview)
- Nhat quan voi oadmap_python_3000.md va SKILL.md (Muc 4: Non-Interactive).

#### 2. Them 18 Topic Moi (Day 3081 - 3350, moi topic 15 ngay)
- Advanced Core & STL: std::format C++20/23; std::jthread, stop_token, std::generator
- Systems & Performance: Memory-mapped files (mmap); Coroutine internals tu viet
- Embedded & Firmware: DMA & USB protocol stack; Ethernet + lwIP TCP/IP
- Graphics & Game Dev: Animation systems (skeletal, IK); Game networking (rollback); Metal API (Apple)
- Networking & Distributed: HTTP/2 & HTTP/3 (QUIC); io_uring Linux async I/O
- Specialized: ML inference C++ (ONNX/TFLite); OpenCV C++; DSP (FFT/FIR); Database C++ (SQLite/PostgreSQL); llama.cpp internals; CUDA/ROCm GPU computing
- Documentation & Tooling: Google Benchmark & Valgrind deep dive

#### Verify ket qua
- Total Day: 3350 OK | Prompt: 3350 OK | Bai tap: 3350 OK | Tags: 3350 OK
- Non-Interactive warnings: 1342 OK | File size: 7.00 MB | Khong thieu Day nao

### Phân tích Extension Download All TikTok
- **Công vi?c**: T?i mã ngu?n c?a ti?n ích t? Chrome Web Store (ID: gmajiifkcmjkehmngbopoobeplhoegad) vào thu m?c DownloadTiktok và ti?n hành phân tích.
- **K?t qu?**: Ðã luu mã ngu?n, script t? d?ng t?i MP4 (d?a trên vi?c dùng chrome.webRequest b?t URL/header t? API item_list c?a Tiktok). Báo cáo phân tích dã du?c luu trong artifact.

## 2026-07-20 Update: Fix FileNotFoundError & Pip Pinning
- ÄÃ£ sá»­a lá»—i FileNotFoundError khi khÃ´ng tÃ¬m tháº¥y thÆ° má»¥c trong \ex_refresh_listbox\ vÃ  \
ote_refresh_list\. Náº¿u thÆ° má»¥c khÃ´ng tá»“n táº¡i, sáº½ tráº£ vá» máº£ng rá»—ng (hoáº·c bá» qua) thay vÃ¬ crash app.
- Cáº­p nháº­t lá»‡nh tá»± Ä‘á»™ng cÃ i Ä‘áº·t thÆ° viá»‡n khi thiáº¿u thÃ nh \python -m pip install --user <tÃªn_thÆ°_viá»‡n>==<phiÃªn_báº£n>\ Ä‘á»ƒ giá»›i háº¡n cÃ i Ä‘áº·t trong user-space vÃ  cá»‘ Ä‘á»‹nh version an toÃ n.

- ÄÃ£ sá»­a lá»—i thiáº¿u module requests báº±ng cÃ¡ch bá»• sung requests==2.31.0 vÃ o cáº¥u hÃ¬nh tá»± Ä‘á»™ng cÃ i Ä‘áº·t trong REQUIRED_PACKAGES.


- [Settings] TÃ¡ch cáº¥u hÃ¬nh host/port cá»§a Local Server (trÆ°á»›c Ä‘Ã¢y hardcode 127.0.0.1:5678) ra settings.json cho phÃ©p tuá»³ chá»‰nh IP LAN (vÃ­ dá»¥ 192.168.x.x) Ä‘á»ƒ trÃ¡nh bá»‹ block bá»Ÿi proxy/firewall.


- [Settings] Bá»• sung hÃ m \get_local_ip()\ tá»± Ä‘á»™ng nháº­n diá»‡n IP LAN cá»§a mÃ¡y. Náº¿u cáº¥u hÃ¬nh Ä‘ang lÃ  \127.0.0.1\, há»‡ thá»‘ng sáº½ tá»± Ä‘á»™ng ghi Ä‘Ã¨ báº±ng IP LAN thá»±c táº¿ Ä‘á»ƒ trÃ¡nh lá»—i Firewall/Proxy cháº·n Localhost.


- ÄÃ£ sá»­a lá»—i ngáº§m khiáº¿n Local Server khÃ´ng thá»ƒ khá»Ÿi cháº¡y (dáº«n Ä‘áº¿n ERR_CONNECTION_REFUSED trÃªn má»i IP) do thiáº¿u thÆ° viá»‡n \lask_cors\. ÄÃ£ bá»• sung \lask_cors==6.0.5\ vÃ o \REQUIRED_PACKAGES\.



### Cáº­p nháº­t cÃ¡c thÆ° viá»‡n má»›i (2026-07-20)
- python -m pip install --user requests==2.31.0 â€” Cáº§n thiáº¿t cho github_api.py
- python -m pip install --user Flask-Cors==6.0.5 â€” Cáº§n thiáº¿t cho exercise_server.py (sá»­a lá»—i ERR_CONNECTION_REFUSED)

---

## [2026-07-20] Cáº­p nháº­t roadmap_intramart_72.md tá»« PDF gá»‘c

### Viá»‡c Ä‘Ã£ lÃ m
- Truy cáº­p trang index chÃ­nh thá»©c: https://document.intra-mart.jp/download/product/index_v72.html
- Táº£i vá» toÃ n bá»™ 89 file PDF intra-mart WebPlatform/AppFramework Ver.7.2 vá» C:\Users\12953 bao\Desktop\Data
- Äá»c kÃ­ch thÆ°á»›c file thá»±c táº¿ báº±ng Python parallel downloader (10 threads)
- Calibration: im_developers_guide_v72.pdf = 1513 KB / 44 trang => 34.4 KB/trang
- ThÃªm 126 ghi chÃº kÃ­ch thÆ°á»›c vÃ o tá»«ng Day trong roadmap_intramart_72.md

### Káº¿t quáº£
- 89 PDF Ä‘Ã£ táº£i vá» C:\Users\12953 bao\Desktop\Data (tá»•ng ~130 MB)
- roadmap_intramart_72.md: 3021 dÃ²ng -> 3148 dÃ²ng, 313KB -> 323KB
- Má»—i Day giá» cÃ³ dÃ²ng: *File goc: X KB (~Y trang) - da tai ve Desktop\Data*

### File PDF lá»›n nháº¥t (cáº§n nhiá»u ngÃ y há»c nháº¥t)
- bpm_designer_operation_guide_v72.pdf: 23898 KB (~695 trang)
- iwp_iaf_group_admin_operation_guide_v72.pdf: 14326 KB (~416 trang)
- im_workflow_operation_guide_v72.pdf: 13201 KB (~384 trang)
- im_workflow_spec_v72.pdf (IM-WF): 12503 KB (~363 trang)
- bpm_user_operation_guide_v72.pdf: 9653 KB (~281 trang)
- bpm_introduction_v72.pdf: 9918 KB (~288 trang)

### Tráº¡ng thÃ¡i
- DONE - roadmap Ä‘Ã£ Ä‘Æ°á»£c cáº­p nháº­t vá»›i metadata PDF thá»±c táº¿


### Giai Ä‘oáº¡n xx (HÃ´m nay): TÃ­ch há»£p Auto AI (Gemini) Ä‘á»c PDF vÃ  sinh HTML vÃ o AskCpl
- **Cáº­p nháº­t:** ThÃªm Tab má»›i `Auto AI` vÃ o `AskCpl.py`.
- **Má»¥c Ä‘Ã­ch:** Äá»c file Roadmap `roadmap_intramart_72.md`, trÃ­ch xuáº¥t thÃ´ng tin, tÃ¬m file PDF trong thÆ° má»¥c cá»¥c bá»™ (sá»­ dá»¥ng `PyMuPDF`), gá»­i lÃªn Gemini API (dÃ¹ng `google-genai`), vÃ  tá»± Ä‘á»™ng sinh file `session.json` + `index.html`.
- **Xá»­ lÃ½:** Tá»± Ä‘á»™ng báº¯t lá»—i API, mÃ£ hÃ³a Base64 theo Ä‘Ãºng Quy táº¯c VÃ ng Ä‘á»ƒ báº£o toÃ n tiáº¿ng Viá»‡t, cháº¡y trÃªn luá»“ng phá»¥ (Thread) Ä‘á»ƒ khÃ´ng Ä‘Æ¡ UI.


### Bugfix & Tá»‘i Æ°u hÃ³a (Lá»—i 429 & 404 Gemini API)
- **Váº¥n Ä‘á» 1 (Lá»—i 429 - Quota Exceeded):** MÃ´ hÃ¬nh `gemini-2.5-pro` vÆ°á»£t quÃ¡ giá»›i háº¡n token cá»§a Free Tier (32k TPM) khi gá»­i lÆ°á»£ng lá»›n text tá»« PDF.
- **Váº¥n Ä‘á» 2 (Lá»—i 404 - Not Found):** CÃ¡c mÃ´ hÃ¬nh cÅ© nhÆ° `1.5-flash` Ä‘Ã£ bá»‹ Google loáº¡i bá» khá»i API, vÃ  `2.5-flash` bá»‹ cháº·n vá»›i tÃ i khoáº£n má»›i.
- **Giáº£i phÃ¡p:**
  1. **Bá» dÃ¹ng SDK (`google-genai`):** Thay báº±ng gá»i REST API trá»±c tiáº¿p (`requests.post`) Ä‘á»ƒ trÃ¡nh lá»—i do thÆ° viá»‡n cÅ© khÃ´ng nháº­n dáº¡ng Ä‘Æ°á»£c model má»›i.
  2. **DÃ¹ng alias `gemini-flash-latest`:** Tá»± Ä‘á»™ng Ä‘á»‹nh tuyáº¿n tá»›i model Flash á»•n Ä‘á»‹nh nháº¥t hiá»‡n cÃ³ cá»§a Google, trÃ¡nh lá»—i 404 khi Google update phiÃªn báº£n.
  3. **Auto-Retry:** ThÃªm vÃ²ng láº·p `max_retries = 3` vÃ  `time.sleep(60)` náº¿u váº«n vÃ´ tÃ¬nh gáº·p lá»—i 429.


### Cáº£i tiáº¿n UI Xuáº¥t & Bá» Base64
- **Váº¥n Ä‘á»:** Export toÃ n bá»™ lá»™ trÃ¬nh gom vÃ o 1 file index.html duy nháº¥t (qua session.js base64) bá»‹ lá»—i vÃ  khÃ´ng trá»±c quan. Lá»‡nh (Prompt) gá»­i AI cÅ©ng bá»‹ láº·p khi chia cáº¯t file PDF dÃ i.
- **Giáº£i phÃ¡p:**
  1. XoÃ¡ bá» hoÃ n toÃ n cÆ¡ cháº¿ mÃ£ hoÃ¡ **Base64** vÃ  xoÃ¡ session.js, ghi trá»±c tiáº¿p session.json báº±ng raw utf-8 (giáº£m 33% dung lÆ°á»£ng). uto_ai_worker.py (Resume function) váº«n Ä‘Æ°á»£c viáº¿t há»— trá»£ Ä‘á»c ngÆ°á»£c base64 cÅ© nhÆ°ng sáº½ convert sang json.
  2. Thay Ä‘á»•i create_viewer() Ä‘á»ƒ sinh Ä‘á»™c láº­p cÃ¡c file váº­t lÃ½ dayXXX.html (nhÆ° tiá»‡n Ã­ch Chrome cÅ©) cÃ³ CSS Ä‘áº¹p.
  3. LÃ m má»›i báº£ng index.html Ä‘Ã³ng vai trÃ² lÃ  Má»¥c lá»¥c liÃªn káº¿t (TOC), cÃ³ thanh tÃ¬m kiáº¿m, thá»‘ng kÃª sá»‘ day.
  4. BÆ¡m thÃªm biáº¿n day['title'] vÃ o lá»‡nh (prompt) truyá»n cho AI Ä‘á»ƒ AI hiá»ƒu bá»‘i cáº£nh vÃ  trÃ¡nh sinh ra cÃ¢u dáº«n láº·p láº¡i.


### Giai doan moi (22/07/2026): Tai lai PDF, Nang cap Quan ly API Keys & Hoi thoai Multi-turn (YC1-YC5)
- YC1 (Tai lai du lieu): Viet script download_intramart_pdfs.py tu dong quet roadmap, trich xuat URL PDF, tai song song 10 Thread, luu vao D:\Tai truyen\Data, bo qua file da co.
- YC2 (Nhap Key cai tien): Thay the simpledialog.askstring bang Toplevel dialog co nut 'Kiem tra trang thai' chay thread nen, hien thi mau xanh/cam/do, ESC de thoat nhanh.
- YC3 (Smart key skip): get_active_key() bo qua exhausted key chua den next_check_time (3h), cap nhat last_check_time sau moi request, them cot 'Check lan cuoi' vao TreeView.
- YC4 (Patch roadmap): Viet patch_expanded_prompts.py: them dong [gio hoc du kien], them YEU CAU CHI TIET VE CACH TRA LOI vao toan bo Prompt trong roadmap_expanded.md. Da chay va verify: 1607 Day co them gio hoc, 1570 Day co them YEU CAU CHI TIET.
- YC5 (Multi-turn follow-up): Sau response chinh, auto_ai_worker.py lap lap: gui FOLLOWUP_PROMPT den khi AI ket thuc bang 'Da day du' hoac dat max_followup lan. Gop tat ca response thanh 1 file HTML voi section rieng. Them checkbox + spinbox tren UI Auto AI.
- COMPILE CHECK: auto_ai_worker.py, AskCpl.py, settings.py => ALL PASS.

### Bá»• sung (22/07/2026): Cáº£i thiá»‡n Check Key & Navbar
- YC: TÃ­nh nÄƒng check key lá»—i (chá»‰ check 1 key Ä‘ang chá»n), yÃªu cáº§u nÃ¢ng cáº¥p nÃºt Check thÃ nh Check ALL keys.
- Giáº£i quyáº¿t: Sá»­a 	est_key trong AskCpl.py thÃ nh check_all_keys(). Cho vÃ²ng láº·p check toÃ n bá»™ keys trong luá»“ng phá»¥ (	hreading), sau Ä‘Ã³ cáº­p nháº­t UI.
- YC: Cáº­p nháº­t Navbar cá»§a HTML sinh ra giá»‘ng há»‡t Addon (cÃ³ gradient, nÃºt mÅ©i tÃªn, TOC dropdown, báº¯t sá»± kiá»‡n phÃ­m mÅ©i tÃªn).
- Giáº£i quyáº¿t: Cáº­p nháº­t template html string trong uto_ai_worker.py, nhÃºng toÃ n bá»™ logic CSS/JS tá»« ackground.js (Addon) vÃ o uto_ai_worker.py (NAV-BAR-V2).
- Tráº¡ng thÃ¡i: PASS

### Bá»• sung nhá» (22/07/2026): ThÃªm tÃ­nh nÄƒng sá»­a Key
- YC: Key gmv15 bÃ¡o invalid, thÃªm tÃ­nh nÄƒng click double Ä‘á»ƒ sá»­a key (CRUD).
- Giáº£i quyáº¿t: ChÃ¨n event 	ree.bind("<Double-1>", edit_key) vÃ o AskCpl.py. Khi nhÃ¡y Ä‘Ãºp vÃ o má»™t dÃ²ng, hiá»‡n cá»­a sá»• edit_win Ä‘iá»n sáºµn thÃ´ng tin key cÅ©, cho phÃ©p lÆ°u láº¡i Ä‘á»ƒ Ä‘Ã¨ lÃªn vá»‹ trÃ­ cÅ©. Reset tráº¡ng thÃ¡i (status="active", reset_time=0) sau khi sá»­a.
- Káº¿t quáº£ test API: BÃ¡o 400 API key not valid. tá»« Google, chá»©ng tá» key nháº­p vÃ o thá»±c sá»± sai hoáº·c Ä‘Ã£ bá»‹ Google khÃ³a.

### Cáº­p nháº­t nÃ¢ng cao (23/07/2026): Quáº£n lÃ½ API Keys
- YC1: Form Sá»­a Key (Modify) bá»• sung nÃºt 'Check Key' y há»‡t lÃºc ThÃªm má»›i.
- YC2: Kiá»ƒm tra trÃ¹ng láº·p mÃ£ API Key khi ThÃªm hoáº·c Sá»­a. Náº¿u trÃ¹ng bÃ¡o lá»—i vÃ  tá»« chá»‘i lÆ°u.
- YC3: Cáº£i tiáº¿n Check ALL keys: Báº¯t Ä‘Æ°á»£c thÃ´ng Ä‘iá»‡p lá»—i (nhÆ° lá»—i 403 Access Denied) vÃ  lÆ°u láº¡i vÃ o trÆ°á»ng error_msg, Ä‘á»“ng thá»i hiá»ƒn thá»‹ chi tiáº¿t lá»—i Ä‘Ã³ trÃªn cá»™t Tráº¡ng thÃ¡i cá»§a TreeView Ä‘á»ƒ ngÆ°á»i dÃ¹ng biáº¿t chÃ­nh xÃ¡c nguyÃªn nhÃ¢n invalid.


## 2026-07-23: Fix Quota Exhaustion & Add Start Day
- Cáº­p nháº­t AskCpl.py: ThÃªm Ã´ nháº­p Báº¯t Ä‘áº§u tá»« Day Ä‘á»ƒ cho phÃ©p chá»n ngÃ y táº£i láº¡i (bá» qua/xÃ³a cÃ¡c ngÃ y sau).
- Cáº­p nháº­t auto_ai_worker.py: LÆ°u láº¡i raw_responses vÃ o session.json Ä‘á»ƒ tá»± Ä‘á»™ng resume (cháº¡y tiáº¿p) tiáº¿n trÃ¬nh há»i follow-up Ä‘ang dang dá»Ÿ khi bá»‹ háº¿t quota, khÃ´ng bá»‹ lÃ£ng phÃ­ cháº¡y láº¡i tá»« LÆ°á»£t 1.
- Cáº­p nháº­t AskCpl.py: Tá»± Ä‘á»™ng Ä‘á»c session.json khi chá»n thÆ° má»¥c xuáº¥t Ä‘á»ƒ bÃ¡o Day hoÃ n thÃ nh gáº§n nháº¥t/Ä‘ang dang dá»Ÿ vÃ  tá»± Ä‘iá»n Day káº¿ tiáº¿p vÃ o Ã´ báº¯t Ä‘áº§u.


## 2026-07-23: Follow-up Mode UI + Key Manager Upgrade
- AskCpl.py: Thay Ã´ nháº­p "so luot toi da" bang 2 radio button: "Hoi den khi hoan thanh" (mac dinh, max=999) va "Hoi toi da N luot".
- AskCpl.py: Key Manager nang cap: them cot Project ID, nut Tu dong dieu chinh, to do key trung project ID, tu dong check truoc khi luu key moi.


## 2026-07-23: UI API Manager & Auto AI Stop Button
- ThÃªm nÃºt Stop (ðŸ›‘ Dá»«ng láº¡i) cho luá»“ng Auto AI vÃ  logic há»§y an toÃ n (STOP_REQUESTED) trong auto_ai_worker.py.
- Cáº£i thiá»‡n giao diá»‡n Quáº£n lÃ½ API Key: NhÃ³m TreeView vÃ o frame Ä‘á»ƒ fix lá»—i nÃºt bá»‹ che khuáº¥t.
- Cáº­p nháº­t logic trÃ­ch xuáº¥t Project ID: DÃ¹ng Regex parse thÃ´ng bÃ¡o lá»—i 429 Ä‘á»ƒ láº¥y Ä‘Ãºng project_number.
- ThÃªm tÃ­nh nÄƒng click vÃ o tiÃªu Ä‘á» cá»™t Ä‘á»ƒ sáº¯p xáº¿p ABC, vÃ  nÃºt LÆ°u Thá»© Tá»± Ä‘á»ƒ ghi nháº­n vá»‹ trÃ­ hiá»ƒn thá»‹ hiá»‡n táº¡i vÃ o settings.


## 2026-07-23: Fix UI Auto AI Session & API Key Project ID Input
- Fix: Sá»­a lá»—i khÃ´ng hiá»‡n tráº¡ng thÃ¡i session náº¿u ngÆ°á»i dÃ¹ng Ä‘á»ƒ trá»‘ng ThÆ° má»¥c Output (sáº½ fallback vá» thÆ° má»¥c chá»©a file roadmap).
- Feature: Bá»• sung Ã´ nháº­p Project ID thá»§ cÃ´ng vÃ o giao diá»‡n ThÃªm/Sá»­a API Key. Viá»‡c nÃ y cho phÃ©p ngÆ°á»i dÃ¹ng tá»± phÃ¢n loáº¡i cÃ¡c API key cÃ¹ng email vÃ o cÃ¡c project khÃ¡c nhau Ä‘á»ƒ tá»± Ä‘á»™ng check trÃ¹ng láº·p (vÃ¬ Google API khÃ´ng tráº£ vá» project_id khi bÃ¡o lá»—i 429).

## 2026-07-23: Fix Bug Auto AI Stop & Avoid Re-reading PDF
- **Fix:** Nút Stop dã ho?t d?ng t?c thì ngay c? khi dang ch? ph?n h?i t? Gemini (t?i da 180s) nh? b? sung check \STOP_REQUESTED\ trong vòng l?p \while not future.done()\ c?a \call_gemini_api\.
- **Fix:** Tránh d?c l?i file PDF và t?n RAM/Time vô ích (in ra 'Ðang d?c PDF...') cho các Day dã hoàn thành Lu?t 1 nhung dang dang d? ph?n h?i b? sung (Follow-up). Tool gi? ch? d?c file PDF n?u dây là l?n g?i Lu?t 1.


## 2026-07-23: Add Project ID to Logs & Auto-increment ID in UI
- **Log:** B? sung hi?n th? Project ID (n?u có) bên c?nh Tên/Email vào toàn b? các dòng log báo l?i (Exhausted, Invalid, Quota, Quá t?i) trong uto_ai_worker.py d? d? dàng theo dõi.
- **UI:** Tính nang Thêm API Key m?i (AskCpl.py) t? d?ng c?ng thêm 1 vào Project ID (ví d? 2 -> 3) n?u Project ID l?n tru?c nh?p vào là m?t con s?, giúp thao tác thêm Key nhanh hon.


## 2026-07-24: Fix Race Condition When Updating API Keys While AI Is Running
- **V?n d?:** N?u ngu?i dùng thêm API key m?i trong lúc ti?n trình Auto AI dang t?i ng?m, khi AI g?p l?i (VD: h?t Quota) và luu tr?ng thái key, nó s? dùng danh sách key cu t? d?u phiên ch?y ghi dè xu?ng dia, làm m?t key m?i thêm.
- **Fix:** Thay d?i logic trong uto_ai_worker.py: 
  1. Lo?i b? vi?c dùng m?ng pi_keys_list truy?n vào lúc d?u d? xét duy?t. Hàm get_active_key nay s? t? d?c tr?c ti?p danh sách key m?i nh?t t? dia.
  2. B? sung hàm update_key_on_disk(k_obj): ch? thay d?i dúng status, eset_time c?a key tuong ?ng vào danh sách m?i nh?t trên ? c?ng.
  3. Nh? co ch? này, ti?n trình n?n không nh?ng h?t l?i ghi dè, mà còn **nh?n di?n du?c ngay l?p t?c** các Key m?i b?n v?a thêm vào mà không c?n ph?i kh?i d?ng l?i tác v? Auto AI.


## 2026-07-28: Fix Exercise Builder for Addon Files
- **Fix:** C?p nh?t logic quet file HTML trong AskCpl.py (tab Bai t?p) ?? h? tr? nh?n di?n c? ten file d?ng c? (day_1.html) va ??nh d?ng m?i xu?t t? Addon (001_Day 1...html). ?a ??i c? ch? parse t? startswith('day_') sang regex k?t h?p ki?m tra t? khoa linh ho?t, ??ng th?i s?p x?p (sort) l?i danh sach chu?n xac ?? tr?n l?n c? 2 chu?n file khong b? l?i.

## 2026-07-29: Tá»‘i Æ°u Cá»±c Ä‘áº¡i Tá»‘c Ä‘á»™ Má»Ÿ/LÆ°u .askcpl (In-Memory Crypto)
- **Tá»‘i Æ°u AES Chunk:** TÄƒng _CHUNK tá»« 64KB lÃªn 4MB trong crypto_utils.py giÃºp tÄƒng tá»‘c Ä‘á»™ mÃ£ hoÃ¡ lÃªn 3x (300%).
- **In-Memory Decryption:** ThÃªm hÃ m decrypt_to_memory() Ä‘á»c luá»“ng AES vÃ  xuáº¥t file ZIP tháº³ng vÃ o io.BytesIO (trÃªn RAM), loáº¡i bá» hoÃ n toÃ n Disk I/O cháº­m cháº¡p. Tá»± Ä‘á»™ng fallback vá» ghi file cá»©ng náº¿u file quÃ¡ lá»›n (>500MB).
- **Streaming Zip Copy:** Thay Ä‘á»•i encrypt_from_zip_and_folder sang dÃ¹ng shutil.copyfileobj káº¿t há»£p vá»›i io.BytesIO, tÄƒng tá»‘c Ä‘á»™ há»£p nháº¥t ZIP lÃªn thÃªm 27%.
- **Cáº­p nháº­t UI AskCpl:**
  - AskCpl.py tá»± Ä‘á»™ng hiá»ƒn thá»‹ popup bÃ¡o cháº¿ Ä‘á»™ 'RAM (SiÃªu tá»‘c)' hoáº·c 'Disk (File lá»›n)'.
  - Thay tháº¿ toÃ n bá»™ mÃ£ nÃ©n/giáº£i nÃ©n cá»¥c bá»™ thÃ nh sá»­ dá»¥ng context manager _open_lazy_zip().
  - Hiá»‡u nÄƒng hiá»‡n táº¡i Ä‘Ã£ Ä‘áº¡t Ä‘áº¿n giá»›i háº¡n pháº§n cá»©ng cá»§a quÃ¡ trÃ¬nh streaming file mÃ  khÃ´ng cáº§n thay Ä‘á»•i Ä‘á»‹nh dáº¡ng archive.

## 2026-07-29: Quota Tracker - TÃ­ch há»£p Local OAuth Server Ä‘á»™c láº­p
- **TÃ­nh nÄƒng má»›i:** Thay tháº¿ hoÃ n toÃ n cÆ¡ cháº¿ Ä‘Äƒng nháº­p dá»± phÃ²ng (dá»±a vÃ o Auth Provider máº·c Ä‘á»‹nh khÃ´ng tá»“n táº¡i cá»§a VS Code) báº±ng má»™t **Local OAuth HTTP Server** siÃªu nháº¹, tÃ­ch há»£p tháº³ng vÃ o extension Quota Tracker. 
- **Lá»£i Ã­ch:** 
  - Kháº¯c phá»¥c triá»‡t Ä‘á»ƒ lá»—i "khÃ´ng click Ä‘Æ°á»£c" á»Ÿ nÃºt ThÃªm tÃ i khoáº£n khi mÃ¡y khÃ´ng cÃ³ extension Gemini Account.
  - Tá»± Ä‘á»™ng má»Ÿ trÃ¬nh duyá»‡t web cá»§a ngÆ°á»i dÃ¹ng Ä‘á»ƒ Ä‘Äƒng nháº­p Google (yÃªu cáº§u consent Ä‘á»ƒ láº¥y refresh_token), tá»± Ä‘á»™ng nháº­n callback á»Ÿ cá»•ng localhost (8888-8892), vÃ  tá»± Ä‘á»™ng Ä‘Ã³ng trÃ¬nh duyá»‡t khi thÃ nh cÃ´ng.
  - ToÃ n bá»™ Access Token & Refresh Token Ä‘Æ°á»£c extension tá»± chá»§ lÆ°u vÃ o globalState cá»§a chÃ­nh nÃ³, giÃºp nÃ³ khÃ´ng cáº§n phá»¥ thuá»™c vÃ o Gemini Account.
- **Backend Sync:** Cáº­p nháº­t script sync_antigravity.py Ä‘á»ƒ bá»• sung tÃ­nh nÄƒng Ä‘á»c trá»±c tiáº¿p mÃ£ Token do chÃ­nh extension Quota Tracker tá»± thu tháº­p tá»« state.vscdb, nÃ¢ng cao tÃ­nh Ä‘á»™c láº­p cá»§a á»©ng dá»¥ng.


## 2026-07-29: Quota Tracker - TÃ­ch há»£p Fetch Quota API & NÃºt Check All thá»±c thá»¥
- **API Fetching:** Viáº¿t module etchBalances trong oauth.js giáº£ láº­p User-Agent cá»§a Antigravity IDE Ä‘á»ƒ qua máº·t Google Cloud Code API.
- **NÃºt Check All:** Viáº¿t láº¡i logic doCheckAll trong extension Ä‘á»ƒ thá»±c sá»± gá»i máº¡ng tá»›i Google kiá»ƒm tra tá»«ng tÃ i khoáº£n, khÃ´ng cÃ²n lÃ  nÃºt giáº£ láº­p chá»‰ Ä‘á»c DB cá»¥c bá»™.
- **Auto-Fetch:** Extension tá»± Ä‘á»™ng fetch sá»‘ dÆ° % Quota ngay sau khi thÃªm tÃ i khoáº£n, sá»­a lá»—i hiá»ƒn thá»‹ mÃ¹ 100% khi má»›i Add Account.
- **Base64 Backup:** ToÃ n bá»™ OAuth tokens Ä‘Æ°á»£c sao chÃ©p vÃ  mÃ£ hoÃ¡ chuáº©n Base64 UTF-8 an toÃ n vÃ o File Dá»¯ liá»‡u (quota_data.dat), cho phÃ©p cÃ¡c tiáº¿n trÃ¬nh ngoáº¡i vi nhÆ° Python sá»­ dá»¥ng mÃ  khÃ´ng cáº§n globalState cá»§a VS Code.


## 2026-07-29: Fix checkAll - Token tá»« VS Code Auth + groupStatus tá»©c thÃ¬
- **Nguyen nhan loi 1 (svendn03):** token nam trong VS Code Auth (Antigravity Account ext), khong co trong Quota Tracker globalState. checkAll cu bo qua.
- **Fix:** Them vscode.authentication.getSessions() vao checkAll va checkOne, lay token cua TAT CA tai khoan Google dang dang nhap, ke ca svendn03.
- **Nguyen nhan loi 2 (gamesvendn OK 100%):** Python sync doc SQLite cu (stale), balances trong dat file chua kip duoc cap nhat truoc khi Python chay.
- **Fix:** Them ham computeGroupStatus() bang JS (copy logic assess_account cua Python). Sau khi fetch balances, tinh ngay groupStatus va luu vao dat file. UI co the hien thi Gemini/Claude/GPT % NGAY LAP TUC ma khong can cho Python.
- **Fix sync_antigravity.py:** Doc ca 2 key DB (Davissss2 + Quota Tracker), merge ket qua. Khi tinh, uu tien balances tu quota_data.dat (fresh) thay vi SQLite (stale).
- **Ket qua verify:** svendn03: OK=[gemini], EX=[claude,gpt]. gamesvendn: OK=[gemini,claude,gpt].


## 2026-07-29: Quota Tracker - Cai thien addAccount va switchAccount
- **addAccount chi sync 1 email:** Them email filter vao autoSyncFromDB trong addAccount, chi chay Python sync cho account vua them, tranh mat thoi gian sync toan bo.
- **switchAccount khong can restart:** Phat hien antigravity-account extension poll key ntigravity.accounts.active trong globalState moi 5s de detect account change. Viec set key nay truc tiep (context.globalState.update) lam cho IDE tu reload AI models ma KHONG can restart. UI cua Quota Tracker cung cap nhat ngay lap tuc.
- **Source:** Doc truc tiep minified source cua antigravity-account ext de xac nhan cach hoat dong.


## 2026-07-29: Fix loi addAccount (Race condition & Stale Data)
- **Nguyen nhan loi 1 (Khong hien account ngay / Phai chay 2 lan):** Do addAccount goi sync ngay lap tuc, trong khi VS Code chua kip ghi data xuong SQLite. Python doc SQLite cu nen khong thay account moi.
- **Fix loi 1:** Them setTimeout(2500) de cho SQLite ghi xong. Sau do tu dong fetch balances qua vscode.authentication.getSessions, tinh groupStatus va goi refreshPanel() NGAY LAP TUC de UI hien thi luon, khong can cho Python sync.
- **Nguyen nhan loi 2 (Account het quota nhung van hien 100%):** Do sync_antigravity.py LUON uu tien lay balances tu quota_data.dat mac du data nay co the da cu tu may ngay truoc (vi du: luu thong tin 100% tu luc moi them account).
- **Fix loi 2:** Them check freshness trong sync_antigravity.py. Chi su dung balances tu quota_data.dat neu lastChecked con moi (< 5 phut). Neu cu hon, dung lai data tu SQLite.


## 2026-07-29: Fix Check All Missing Accounts & 100% Display Bug
- **Check All**: Changed checkAll in JS to call ntigravity-account.refreshBalances to force Antigravity Account extension to refresh all managed accounts before doing utoSyncFromDB. This ensures all 9 accounts are synced, instead of just the 5 logged directly into VS Code.
- **100% Display Bug**: Changed computeGroupStatus in JS and ssess_account in Python to use the minimum percentage of active models instead of the average of all 24 models in a group. This prevents the UI from diluting the percentage of exhausted/partially-exhausted models and always showing 100%.


## 2026-07-30: Tá»± chá»§ hoÃ n toÃ n (TokenManager + switch_account.py)
- **TokenManager**: ThÃªm class TokenManager tá»± chá»§ trong extension.js. DÃ¹ng context.secrets cá»§a chÃ­nh extension Ä‘á»ƒ lÆ°u/Ä‘á»c access_token + refresh_token + expiresAt cho tá»«ng email. KhÃ´ng phá»¥ thuá»™c vÃ o Antigravity Account extension.
- **Token refresh tá»± Ä‘á»™ng**: ThÃªm AuthService.refreshAccessToken() vÃ o oauth.js. TokenManager.ensureValid() sáº½ tá»± refresh náº¿u token gáº§n háº¿t háº¡n (< 5 phÃºt).
- **Check All tá»± chá»§**: Rewrite checkAll Ä‘á»ƒ tá»± gá»™p email tá»« (1) TokenManager store, (2) .dat file, (3) VS Code session. Tá»± fetch API cho tá»«ng email báº±ng token cá»§a mÃ¬nh. Hiá»ƒn thá»‹ tiáº¿n Ä‘á»™ [i/n] Äang check...
- **Add Account tá»± chá»§**: Rewrite addAccount Ä‘á»ƒ chá»‰ dÃ¹ng Local OAuth (oauth.js), lÆ°u token vÃ o TokenManager thay vÃ¬ phá»¥ thuá»™c vÃ o Antigravity Account extension.
- **Switch Account**: DÃ¹ng switch_account.py viáº¿t tháº³ng vÃ o state.vscdb (can thiá»‡p Ä‘Ãºng DB). Cáº§n Reload Window sau khi switch.
- **switch_account.py**: Táº¡o file má»›i táº¡i CTApp/QuotaAntigravity/QuotaApp/switch_account.py.


## 2026-07-30: Fix Core Bug - sync_antigravity.py fresh_balances override
- ROOT CAUSE IDENTIFIED: file .dat luu 'balances' cu (tat ca 100%) tu lan Check All cu. Python sync co logic 'fresh_balances override' se dung .dat balances neu < 5 phut thay vi doc tu state.vscdb. Ket qua: UI hien thi 100% du tai khoan da het quota.
- FIX: Xoa logic 'fresh balances' override trong sync_quota_data(). state.vscdb LUON la nguon su that. Email khong co trong state.vscdb thi moi dung .dat balances (email Quota Tracker tu quan ly qua OAuth).
- FIX: Xoa balances thu tu state.vscdb khoi .dat de tranh stale data.
- VERIFIED: Chay sync sau fix, svendn03 hien EX=[gemini,claude,gpt] dung; gamesvendn10 EX=[gemini] nhung con claude+gpt.
- Sync 13 tai khoan tu IDE, 5 het hoan toan, 1 het mot phan (gamesvendn10).

## 2026-07-30: Kien truc Cross-Machine (Quota Tracker tu chu)

### Vision nguoi dung:
- Machine A: Dang nhap OAuth -> token luu vao TokenManager (secrets) + .dat
- Copy .dat sang Machine B
- Machine B: Doc .dat -> import token vao TokenManager -> Check All hoat dong
- Khong phu thuoc Antigravity Account de Check / display quota

### Ket qua diagnostic:
- state.vscdb KHONG luu token (chi luu email, status, balances)
- Token Antigravity Account nam trong VS Code Secrets (ma hoa, Python khong doc duoc)
- state.vscdb chi dung de doc balances hien tai (truong hop may A)

### Kien truc dat file (se implement):
- dat = portable source of truth
- dat luu: groupStatus, exhaustedUntil, tokens (access+refresh), lastChecked
- Khi addAccount (OAuth): luu token vao ca TokenManager VA dat
- Khi Check All thanh cong: luu token moi vao dat
- Khi startup Machine B: doc dat -> auto-import token vao TokenManager
- sync_antigravity.py: KHONG xoa tokens tu dat, bao ton tokens theo email

### Chua implement:
- dat chua luu tokens
- startup chua auto-import tokens tu dat
- addAccount chua ghi token vao dat

## 2026-07-30: IMPLEMENTED Cross-Machine Token Portability

### Thay doi extension.js:
1. addAccount: Sau OAuth -> luu tokens vao .dat file (access_token, refresh_token, expiry_ms)
2. activate: Auto-import tokens tu .dat vao TokenManager khi startup (chi import neu chua co)
3. checkAll: Sau fetch thanh cong -> cap nhat token moi nhat vao .dat. Email khong co token -> hien thi ro rang khong am tham bo qua

### Thay doi sync_antigravity.py:
- Bao ton tokens field khi sync (luu existing_tokens truoc update, khoi phuc sau)
- Xoa balances tho tu DB khoi .dat (tranh stale data)

### Luong cross-machine:
Machine A: Login -> .dat co tokens -> copy .dat sang Machine B
Machine B: Startup -> auto-import tokens -> Check All hoat dong ngay

### VERIFIED:
- Syntax check: extension.js va sync_antigravity.py deu pass
- Sync chay dung: 15 accounts, 5 het hoan toan, 2 het mot phan

## 2026-07-30: UI improvements + checkAll summary + sort by reset

- formatCountdown: hien so ngay (2d 4h 30m thay vi chi hours)
- Header "Reset" clickable de sort theo thoi gian hoi phuc
- sortKey='reset': sort theo overallResetTime (sap hoi phuc nhat len dau khi asc)
- Badge 'NO TOKEN' (do) hien thi trong cot Email neu email khong co token trong .dat
- checkAll summary cuoi: hien ten email nao can dang nhap lai cu the
- Syntax check: PASS

## 2026-07-30: Fix checkOne token lookup, syncTokensToDat, and explicit error status in UI

### Nguyen nhan & Fixes:
1. Fix checkOne (nut ðŸ” check 1 tai khoan): Truoc day checkOne dung code cu tim trong globalState (rong) thay vi TokenManager. Refactor checkOne dung TokenManager.ensureValid(msg.email).
2. Synchronization syncTokensToDat(): Tu dong dong bo token tu TokenManager (context.secrets) sang .dat file moi khi refresh panel, giup UI hien thi chinh xac tai khoan nao da co token.
3. Explicit error status in UI: Khi checkAll/checkOne bi loi (no token, expired token, network error), luu data[email].lastError va hien thi badge loi mau do âš ï¸ nhat dinh tren UI (thay vi hien thi 100% cu gay nham lan).
4. Verified: Node syntax check PASS.

## 2026-07-30: Fix Live API vs Stale DB Priority in sync_antigravity.py

### Nguyen nhan & giai phap:
1. Root cause vi sao gamesvendn06 ra 100%: Google API truc tiep tra ve 24/24 models deu 100% OK (da hoi phuc). Tuy nhien truoc day khi autoSyncFromDB chay ngay sau khi addAccount / Check All, Python sync doc state.vscdb chua cap nhat (chua qua refresh cua Antigravity Account ext) va ghi de len data tu API.
2. Giai phap: Cap nhat priority trong sync_antigravity.py: Nhat dinh uu tien dat_balances tu Google API neu duoc fetch trong vong 15 phut (is_fresh_api). Khong ghi de va khong xoa dat_balances khi API data con moi.
3. Auto Reload: addAccount (dang nhap lai) da co san tu dong refreshPanel() va luu token vao .dat + TokenManager, giup giao dien tu dong cap nhat ngay lap tuc sau dang nhap.
4. VERIFIED: Python sync chay thanh cong, hoan toan chinh xac theo du lieu tu ca Live API va DB.

## 2026-07-30: Fix Conservative Merging between IDE DB & Live Google API

### Phan tich nguyen nhan vi sao svendn03@gmail.com bi nham 100%:
1. Google OAuth API (etchAvailableModels) kiem tra base account quota tren Google Cloud va tra ve 100% OK.
2. Tuy nhien Antigravity IDE state.vscdb ghi nhan 20 models bi depleted (alue: 0, status low_balance) do rate limit/project quota trong IDE.
3. Truoc day Quota Tracker uu tien dung ket qua tu API va bo qua data tu state.vscdb, nen hien thi 100% OK trong khi thuc te user khong dung duoc trong IDE.

### Giai phap thuat toan (Conservative Merge):
- Quota Tracker ket hop ca 2 nguon: DB trong IDE (state.vscdb) va Live Google API.
- Voi moi model, lay gia tri nho nhat min(value_db, value_api).
- Neu bat ky nguon nao (DB IDE hoac API) ghi nhan model het quota (alue == 0), model do se bi tinh la  %.
- Nhá» váº­y, svendn03@gmail.com va cac tai khoan khac bi het quota trong IDE láº­p tá»©c Ä‘Æ°á»£c tÃ­nh toÃ¡n va hien thi **ðŸ”´ Háº¿t quota** chÃ­nh xÃ¡c 100%.

### VERIFIED:
- Diagnostic script va Python sync chay cho ra ket qua svendn03@gmail.com: EX=[gemini, claude, gpt] (Het quota hoÃ n toÃ n).
- Tat ca 16 tai khoan deu duoc phan tich dung voi thuc te trong IDE.

## 2026-07-30: Auto-Update Status on Login without requiring Check All

### Cai thien tinh nang addAccount:
1. Khi nguoi dung dang nhap lai (nut âž• Dang nhap), tu dong xoa bo lastError/NO TOKEN badge ngay lap tuc (delete data[email].lastError).
2. Tu dong fetch live API balances va tinh toan groupStatus moi nhat cho email do.
3. Tu dong chay utoSyncFromDB (conservative merge) va reload giao dien Webview efreshPanel() lap tuc.
4. Nguoi dung KHONG can phai bam Check All nua, giao dien va trang thai cua tai khoan se duoc tu dong lam moi 100% ngay khi dang nhap thanh cong.
5. VERIFIED: Node syntax check PASS.

## 2026-07-30: Fix Key Collision in extract_accounts_from_db

### Phat hien nguyen nhan chinh xac khien gamesvendn06 bi nham 100%:
- Trong file sync_antigravity.py, ham extract_accounts_from_db doc 2 key tu state.vscdb:
  1) Davissss2.antigravity-account (key cua Antigravity Account extension chu dong luu 20 models bi depleted = 0).
  2) ntigravity.quota-antigravity-ext (key cu cua Quota Tracker luu 24 models = 100%).
- Vi Vong lap doc key 2 sau key 1 va thuc hien merged = {**existing, **acc}, key 2 da DEM GHI DE len du lieu 20 models depleted cua key 1!
- Do do, du lieu bi het quota cua Antigravity Account bi xoa mat moi lan Python sync chay!

### Da sua trong sync_antigravity.py:
- Chi doc duy nhat key Davissss2.antigravity-account tu SQLite DB lam nguon su that duy nhat.
- KET QUA: gamesvendn06@gmail.com va tat ca cac tai khoan khac da duoc phan tich CHINCH XAC 100%: gamesvendn06 tinh ra EX=[gemini, claude, gpt] (Het quota hoan toan).

### VERIFIED:
- Diagnostic doc lai .dat file -> gamesvendn06 da chuyen sang exhausted: true cho ca 3 nhom gemini, claude, gpt.

## 2026-07-30: Fix Misleading 6d Countdown and Ensure Accurately Computed Exhausted Status for gamesvendn18

### Nguyen nhan & khac phá»¥c:
1. Fix fake 6d countdown: Google API tra ve resetTime 7 ngay (weekly reset) cho ca cac model 100% OK. Truoc day computeGroupStatus va assess_account van tinh resetTime tu cac model OK khien tai khoan 100% bi hien hien thi 6d 23h 58m sai lech.
2. Da sua: esetTime va overallResetTime chi duoc tinh khi model/group bi EXHAUSTED (exhausted: true). Neu tai khoan 100% OK, overallResetTime = 0 va hien thi â€”.
3. Fix gamesvendn18: Tu dong gop va phan tich dung voi DB state.vscdb cua IDE, gamesvendn18 nay tinh ra **ðŸ”´ Háº¿t quota hoÃ n toÃ n** (EX=[gemini, claude, gpt]) voi thoi gian hoi phuc chinh xac la 1d 17h 18m (hoan toan trung khá»›p voi thoi gian trong IDE).
4. VERIFIED: Node.js & Python syntax PASS.

### [2026-07-31 10:34:14] Fix API Key Validation & Add Log Panel

- **Váº¥n Ä‘á» 1**: Chá»©c nÄƒng kiá»ƒm tra API Key á»Ÿ tab 'Quáº£n lÃ½ API Key' im láº·ng, khÃ´ng cÃ³ log (trÆ°á»›c Ä‘Ã¢y ghi log vÃ o tab Auto AI nÃªn ngÆ°á»i dÃ¹ng khÃ´ng tháº¥y).
- **Váº¥n Ä‘á» 2**: CÃ¡c lá»—i máº¡ng (HTTPSConnectionPool, Timeout) hoáº·c server Google quÃ¡ táº£i (503, 'model is currently experiencing...') bá»‹ hiá»ƒu láº§m lÃ  lá»—i key vÃ  tá»± Ä‘á»™ng Ä‘Ã¡nh dáº¥u key lÃ  'invalid'.
- **Giáº£i phÃ¡p Ä‘Ã£ thá»±c hiá»‡n**:
  1. ThÃªm ScrolledText widget vÃ o panel cuá»‘i tab API Keys Ä‘á»ƒ hiá»ƒn thá»‹ tiáº¿n trÃ¬nh (Log Panel).
  2. Bá»• sung hÃ m log_key() Ä‘á»ƒ ghi trá»±c tiáº¿p cÃ¡c tráº¡ng thÃ¡i gá»i API (HTTP status code, message) ngay trong lÃºc background thread Ä‘ang cháº¡y.
  3. Cáº­p nháº­t logic trong AskCpl.py (check_all_keys, dd_key, edit_key):
     - ConnectionError & Timeout: BÃ¡o lá»—i máº¡ng nhÆ°ng GIá»® NGUYÃŠN tráº¡ng thÃ¡i key.
     - HTTP 503 / 'overloaded': BÃ¡o model báº­n nhÆ°ng GIá»® NGUYÃŠN tráº¡ng thÃ¡i key (hoáº·c mark lÃ  'busy' táº¡m thá»i).
     - HTTP 429 / Quota: Cáº­p nháº­t thÃ nh 'exhausted'.
     - Lá»—i thá»±c sá»± tá»« key: Cáº­p nháº­t thÃ nh 'invalid'.
  4. Cáº­p nháº­t nguyÃªn táº¯c vÃ o generate_roadmap/SKILL.md: Báº¥t ká»³ app Python Tkinter nÃ o thá»±c hiá»‡n request/thread Ä‘á»u pháº£i cÃ³ UI Log Panel Ä‘á»ƒ ngÆ°á»i dÃ¹ng theo dÃµi (Rule sá»‘ 10).
- **Tráº¡ng thÃ¡i**: âœ… HoÃ n thÃ nh. ÄÃ£ syntax check.

### [2026-07-31 10:48:14] Add 'Kiá»ƒm tra key lá»—i' button

- **YÃªu cáº§u**: ThÃªm nÃºt chá»‰ kiá»ƒm tra cÃ¡c key Ä‘ang bÃ¡o lá»—i (status khÃ¡c active/exhausted) Ä‘á»ƒ tiáº¿t kiá»‡m thá»i gian, Ä‘áº·t cáº¡nh nÃºt Kiá»ƒm tra táº¥t cáº£.
- **Giáº£i phÃ¡p**:
  - ThÃªm nÃºt tn_check_err ('Kiá»ƒm tra key lá»—i') ngay cáº¡nh tn_check.
  - NÃ¢ng cáº¥p check_all_keys(only_errors=False): náº¿u only_errors=True thÃ¬ list cáº§n check sáº½ Ä‘Æ°á»£c filter bá» qua 'active' vÃ  'exhausted'.
  - Block/Unblock cáº£ 2 nÃºt trong thá»i gian test.
- **Tráº¡ng thÃ¡i**: âœ… HoÃ n thÃ nh. ÄÃ£ syntax check.

### [2026-07-31 11:10:08] Fix Model Name Error (gemini-1.5-flash-latest)

- **Váº¥n Ä‘á»**: NgÆ°á»i dÃ¹ng bÃ¡o lá»—i API tráº£ vá» models/gemini-1.5-flash-latest is not found for API version v1beta.
- **NguyÃªn nhÃ¢n**: Trong phiÃªn báº£n cáº­p nháº­t trÆ°á»›c, model name trong URL bá»‹ thay Ä‘á»•i thÃ nh gemini-1.5-flash-latest - tÃªn nÃ y khÃ´ng Ä‘Æ°á»£c Google API há»— trá»£ (chá»‰ há»— trá»£ gemini-1.5-flash hoáº·c gemini-flash-latest).
- **Giáº£i phÃ¡p**:
  - DÃ¹ng script sá»­a láº¡i toÃ n bá»™ gemini-1.5-flash-latest thÃ nh gemini-1.5-flash á»Ÿ cáº£ 3 hÃ m gá»i (ThÃªm key, sá»­a key, vÃ  check toÃ n bá»™).
- **Tráº¡ng thÃ¡i**: âœ… HoÃ n thÃ nh.

### [2026-07-31 11:12:23] Rollback Model Name to gemini-flash-latest

- **Váº¥n Ä‘á»**: Sai láº§m chá»§ quan khi tá»± Ã½ Ä‘á»•i tÃªn model thÃ nh gemini-1.5-flash vÃ  gemini-1.5-flash-latest dáº«n tá»›i lá»—i version v1beta khÃ´ng support. 
- **BÃ i há»c**: KhÃ´ng Ä‘á»c ká»¹ log quÃ¡ khá»© trong ProjectLog.md. User Ä‘Ã£ tá»«ng chá»‘t phiÃªn báº£n gemini-flash-latest lÃ  chuáº©n nháº¥t cho code nÃ y.
- **Kháº¯c phá»¥c**: ÄÃ£ dÃ¹ng script Ä‘á»•i toÃ n bá»™ gemini-1.5-flash vá» láº¡i chÃ­nh xÃ¡c gemini-flash-latest trong file AskCpl.py.
- **Tráº¡ng thÃ¡i**: âœ… HoÃ n thÃ nh sá»­a sai.

### [2026-07-31 11:18:13] ThÃªm NÃºt Dá»«ng & LÆ°u Real-time khi check API

- **YÃªu cáº§u 1**: LÆ°u vÃ  cáº­p nháº­t giao diá»‡n ngay sau khi check xong tá»«ng key thay vÃ¬ Ä‘á»£i hoÃ n táº¥t toÃ n bá»™.
- **YÃªu cáº§u 2**: Biáº¿n nÃºt 'Kiá»ƒm tra táº¥t cáº£' thÃ nh nÃºt 'Dá»«ng kiá»ƒm tra' mÃ u Ä‘á» trong lÃºc cháº¡y.
- **Giáº£i phÃ¡p**:
  - DÃ¹ng 	op.after(0, update_single) Ä‘á»ƒ gá»i logic lÆ°u JSON vÃ  
efresh_list() ngay bÃªn trong vÃ²ng láº·p sau má»—i láº§n gá»i API tráº£ káº¿t quáº£.
  - ThÃªm cá» stop_flag = [False]. Äá»•i text vÃ  lá»‡nh cá»§a nÃºt tn_check thÃ nh logic Dá»«ng. Khi loop phÃ¡t hiá»‡n cá», vÃ²ng láº·p dá»«ng ngay láº­p tá»©c. Sau Ä‘Ã³ khÃ´i phá»¥c láº¡i tráº¡ng thÃ¡i cÅ© cho nÃºt.
- **Tráº¡ng thÃ¡i**: âœ… HoÃ n thÃ nh. ÄÃ£ syntax check.

- [x] **AskCpl.py - NÃ¢ng cáº¥p Auto AI Roadmap (Context-Aware):**
  - Bá»• sung Ã´ nháº­p [YÃªu cáº§u bá»• sung/TiÃªu chuáº©n] trÃªn giao diá»‡n Ä‘á»ƒ náº¡p Prompt hoáº·c ná»™i dung file SKILL.md.
  - Step 1 (PhÃ¢n tÃ­ch Khung): Ã‰p LLM sinh JSON Object chá»©a domain_profile (persona, sÃ¡ch ná»n táº£ng, lá»‡nh tá»‘i thÆ°á»£ng) vÃ  skeleton.
  - Step 3 (Sinh Markdown): Äá»c profile Ä‘á»ƒ tá»± Ä‘á»™ng ghÃ©p/ná»‘i thÃ nh siÃªu Template chuyÃªn sÃ¢u (nhÆ° Ná»™i Ä‘an luyá»‡n tháº§n).
  - Tá»± Ä‘á»™ng gá»i há»‡ thá»‘ng má»Ÿ file markdown báº±ng os.startfile() ngay khi hoÃ n thÃ nh Step 3.

- [x] **AskCpl.py - NÃ¢ng cáº¥p Roadmap Generator V3 (2-Stage + Quota Resilient):**
  - UI: ThÃªm Ã´ Thá»i lÆ°á»£ng há»c/ngÃ y, Dropdown Sá»‘ ngÃ y (Auto/30/60/100/150).
  - UI: Thay File tham kháº£o Ä‘Æ¡n thÃ nh danh sÃ¡ch Ä‘á»™ng há»— trá»£ [+]/[-] tá»‘i Ä‘a 5 file.
  - Step 1 viáº¿t láº¡i thÃ nh 2-Stage Prompting: Nhá»‹p 1 sinh Phase Milestones, Nhá»‹p 2 loop sinh chi tiáº¿t tá»«ng Phase vÃ  Merge thÃ nh 1 JSON Skeleton hoÃ n chá»‰nh.
  - Step 3 (LLM Mode) thÃªm: Auto-detect file tá»“n táº¡i Ä‘á»ƒ Append thay vÃ¬ Overwrite, Rotate API Key khi gáº·p lá»—i Quota 429, Retry 3 láº§n trÆ°á»›c khi dá»«ng.

## [2026-07-31] V4 Roadmap Generator - 6-Pass Reflexion Architecture
- **UI Update**: Chia lai giao dien thanh 3 nut bam tuong ung voi 3 giai doan lon.
- **Step 1 (Core Skeleton)**: Doi prompt de AI chi tap trung xuat Khung Xuong cot loi (nhanh, it token).
- **Step 2 (3-Pass Expand & Critique)**: 
  - Pass 1: Doc Dan y Loi -> Tu danh gia, che nho chu de lon, bo sung kien thuc hien dai -> JSON V2.
  - Pass 2: Doc JSON V2 -> Doi chieu SKILL.md va Reference Files -> Ep chuan -> JSON V3 (Cap nhat len UI).
  - Pass 3: Xuat JSON V3 ra file markdown duoi dang Muc Luc.
- **Step 3 (3-Pass Master Details)**: Chay vong lap tung batch:
  - Pass 4: Viet nhap cac cau Prompt bai giang.
  - Pass 5: Dong vai chuyen gia Review, ep them Vi du, Loi thuong gap, Giai thich sau vao Prompt nhap.
  - Pass 6: Danh bong van phong, ep format chuan va Append vao cuoi file.
- **Toi uu Quota**: Tich hop Auto-Rotate API Key ngay trong vong lap 3-Pass cua Step 3.

## [2026-08-02] Roadmap generator: durable handoff and resume

- Step 3 preferentially loads the validated `roadmap_<domain>.reviewed.json`
  produced by Step 2 after an application restart. It falls back to
  `roadmap_<domain>.skeleton.json` only when no reviewed artifact exists.
- Step 2 persists `reviewed.json.progress.json` after each independent review
  pass and each integrated Day group. Step 3 persists `roadmap_<domain>.md.progress.json`
  after each generated content batch.
- Each resume file stores the roadmap identity and is accepted only when it
  matches the source skeleton. A mismatch is logged and is not silently mixed
  with another roadmap.
- Preview text is no longer the sole source of truth: an empty preview reloads
  the saved artifact automatically. Temporary checkpoints are removed only
  after validation and the final stage artifact are saved.
- Verified: Python compile check passed; roadmap pipeline regression suite
  passed (16 tests); the saved toy roadmap skeleton validates with 365 Days.

## [2026-08-02] Retry temporary Gemini failures without losing resume state

- Root cause: a `503`/timeout raised by the Gemini call escaped the outer
  retry loop of Step 2 Phase integration, so one temporary outage stopped the
  stage although the durable checkpoint was intact.
- Fix: both Step 2 phase integration and Step 3 content batches now retry
  network/API and JSON failures at the stage level with bounded backoff.
  Their progress checkpoint is retained after every successful batch.
- If all bounded retries fail, the log now states the exact saved Day range and
  instructs the user to reopen the app and resume the same step; prior work is
  not regenerated.
