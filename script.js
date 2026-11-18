let currentLanguage = "";
let currentView = "list";   // view đang hiện (Gói 10: dùng để nạp lại khóa học khi đổi ngôn ngữ)
let vocabularies = [];
let filteredVocabs = [];
let flashcardIndex = 0;

// Pagination for Lazy Loading
let currentPage = 1;
// paths.js (script load TRƯỚC) đã khai `const VOCAB_SLUG` toàn cục.
// KHÔNG được khai lại cùng tên bằng var/const/function — mọi cách đều ném
// SyntaxError "Identifier 'VOCAB_SLUG' has already been declared" NGAY khi
// instantiate ⇒ toàn bộ script.js chết (mọi hàm undefined). Dùng alias nội bộ.
const slugOf = (typeof VOCAB_SLUG === "function")
    ? VOCAB_SLUG
    : (s) => String(s || "").trim().toLowerCase().replace(/\s+/g, "_");

const ITEMS_PER_PAGE = 30;

const langSelect = document.getElementById("language-select");
const searchInput = document.getElementById("search-input");
const clearSearchBtn = document.getElementById("clear-search");
const filterTopic = document.getElementById("filter-topic");
const filterType = document.getElementById("filter-type");
const filterDate = document.getElementById("filter-date");
const listContainer = document.getElementById("vocab-list");
const loadMoreTrigger = document.getElementById("load-more-trigger");

const btnList = document.getElementById("btn-list");
const btnFlashcard = document.getElementById("btn-flashcard");
const btnCourse = document.getElementById("btn-course");
const viewList = document.getElementById("list-view");
const viewFlashcard = document.getElementById("flashcard-view");
const viewCourse = document.getElementById("course-view");

// ─── Chuyển đổi view 4 chiều (+ Ôn tập SM-2 — Gói 3) ─────────────────────────
const btnReview = document.getElementById("btn-review");
const viewReview = document.getElementById("review-view");

function switchView(name) {
    currentView = name;
    const views = {
        list:      [btnList, viewList],
        flashcard: [btnFlashcard, viewFlashcard],
        course:    [btnCourse, viewCourse],
        review:    [btnReview, viewReview],
    };
    Object.entries(views).forEach(([key, [b, v]]) => {
        if (!b || !v) return;
        b.classList.toggle("active", key === name);
        v.classList.toggle("active", key === name);
        b.setAttribute("aria-selected", key === name ? "true" : "false");
    });
    if (name === "flashcard") renderFlashcard();
    if (name === "course") ensureCourseLoaded();
    if (name === "review") loadSrsQueue();
}

// ─── Helper: escape HTML để an toàn khi dùng innerHTML ───────────────────────
function escapeHtml(str) {
    if (!str) return "";
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

// ─── Markdown mini-renderer (Gói 3 — 2026-11-12) ────────────────────────────────
// TRƯỚC: `marked.parse()` + `DOMPurify.sanitize()` tải từ CDN jsdelivr.
//   ① Mất mạng / CDN bị chặn ⇒ `marked` undefined ở top-level ⇒ script.js CHẾT
//      HOÀN TOÀN ⇒ trang trắng (app local-first lại phụ thuộc mạng ngoài).
//   ② Nếu DOMPurify lỗi nhưng marked tải được ⇒ innerHTML THÔ của nội dung AI
//      (stored XSS trong app local).
// NAY: tự escape trước, rồi áp markdown cơ bản ⇒ không mạng, không XSS.
function formatText(str) {
    if (!str) return "";
    let t = escapeHtml(String(str));
    // code inline
    t = t.replace(/`([^`\n]+)`/g, "<code>$1</code>");
    // **đậm** / *nghiêng*
    t = t.replace(/\*\*([^*\n]+)\*\*/g, "<strong>$1</strong>");
    t = t.replace(/(^|[\s(])\*([^*\n]+)\*(?=[\s).,;:!?]|$)/g, "$1<em>$2</em>");
    // gạch ngang
    t = t.replace(/~~([^~\n]+)~~/g, "<del>$1</del>");
    // link an toàn (chỉ http/https)
    t = t.replace(/\[([^\]\n]+)\]\((https?:\/\/[^)\s]+)\)/g,
                  '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
    // dòng mới → <br>
    t = t.replace(/\r\n/g, "\n").replace(/\n/g, "<br>");
    return t;
}

// Fetch languages list
async function init() {
    try {
        let res = await fetch("data/index.json").catch(() => null);
        if (!res || !res.ok) {
            res = await fetch("../data/index.json").catch(() => null);
        }
        if (!res || !res.ok) throw new Error("Could not load index.json");
        const data = await res.json();
        
        langSelect.innerHTML = "";
        if (data.languages && data.languages.length > 0) {
            // Gói 3: dùng tên hiển thị đẹp nếu server có ("names").
            const names = data.names || {};
            data.languages.forEach(lang => {
                const opt = document.createElement("option");
                opt.value = lang;
                opt.textContent = names[lang] || lang;
                langSelect.appendChild(opt);
            });
            loadLanguage(data.languages[0]);
        } else {
            langSelect.innerHTML = "<option>Chưa có khóa học nào</option>";
        }
    } catch (e) {
        // Dữ liệu (từ vựng/ảnh/audio) nằm LOCAL trong data/ của máy — trang
        // phải qua server nội bộ app (127.0.0.1:5690). KHÔNG cần GitHub.
        langSelect.innerHTML = (location.protocol === "file:")
            ? "<option>⚠ Mở sai cách (file://) — mở app VocabApp rồi vào 127.0.0.1:5690/index</option>"
            : "<option>⚠ Không tải được dữ liệu local — mở qua app VocabApp (127.0.0.1:5690)</option>";
        console.error(e);
    }
}

async function loadLanguage(lang) {
    currentLanguage = lang;
    const filename = slugOf(lang) + ".json";
    // Reset cache khóa học AI theo ngôn ngữ mới
    courseData = null;
    courseSlug = "";
    try {
        let res = await fetch(`data/${filename}`).catch(() => null);
        if (!res || !res.ok) {
            res = await fetch(`../data/${filename}`).catch(() => null);
        }
        if (!res || !res.ok) throw new Error("Could not load vocab data");
        const data = await res.json();
        vocabularies = data.vocabularies || [];

        populateFilters();
        applyFilters();
        // Gói 10 (17/11): nếu đang ở tab "Khóa học AI" mà ngôn ngữ vừa
        // đổi ⇒ nạp lại khóa học (trước đây bị race: ensureCourseLoaded chạy
        // lúc currentLanguage còn RỖNG ⇒ "Chưa có khóa học AI").
        if (currentView === "course") {
            try { await ensureCourseLoaded(); } catch (e) { }
        }
    } catch (e) {
        console.error(e);
        listContainer.innerHTML = (location.protocol === "file:")
            ? "<p>⚠ Mở sai cách (file://) — dữ liệu đọc từ máy qua app VocabApp: vào <b>http://127.0.0.1:5690/index</b></p>"
            : "<p>⚠ Không tải được dữ liệu local — mở app VocabApp rồi vào <b>http://127.0.0.1:5690/index</b></p>";
    }
}

function populateFilters() {
    const topics = new Set();
    const types = new Set();
    const dates = new Set();
    
    vocabularies.forEach(v => {
        if(v.topic) topics.add(v.topic);
        if(v.word_type) types.add(v.word_type);
        if(v.date_tag) dates.add(v.date_tag);
    });
    
    filterTopic.innerHTML = '<option value="">All Topics</option>' + Array.from(topics).map(t => `<option value="${escapeHtml(t)}">${escapeHtml(t)}</option>`).join("");
    filterType.innerHTML  = '<option value="">All Types</option>'  + Array.from(types).map(t => `<option value="${escapeHtml(t)}">${escapeHtml(t)}</option>`).join("");
    filterDate.innerHTML  = '<option value="">All Dates</option>'  + Array.from(dates).map(t => `<option value="${escapeHtml(t)}">${escapeHtml(t)}</option>`).join("");
}

function applyFilters() {
    const q = searchInput.value.toLowerCase();
    const tTopic = filterTopic.value;
    const tType = filterType.value;
    const tDate = filterDate.value;
    
    // Toggle Clear button visibility
    // Gói 3: <button> dùng thuộc tính `hidden` (đúng ngữ nghĩa) thay vì display.
    clearSearchBtn.hidden = !(q.length > 0);
    
    filteredVocabs = vocabularies.filter(v => {
        if (tTopic && v.topic !== tTopic) return false;
        if (tType && v.word_type !== tType) return false;
        if (tDate && v.date_tag !== tDate) return false;
        if (q) {
            const haystack = `${v.word} ${v.meaning} ${v.pronunciation} ${v.example} ${v.example_meaning} ${v.note}`.toLowerCase();
            if (!haystack.includes(q)) return false;
        }
        return true;
    });
    
    renderList(true); // reset list
    flashcardIndex = 0;
    renderFlashcard();
}

function renderList(reset = true) {
    if (reset) {
        listContainer.innerHTML = "";
        currentPage = 1;
    }
    
    if (filteredVocabs.length === 0) {
        listContainer.innerHTML = "<p style='color:var(--text-muted);padding:20px;text-align:center;'>Không tìm thấy từ vựng nào phù hợp.</p>";
        loadMoreTrigger.textContent = "";
        return;
    }
    
    const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
    const endIndex = Math.min(startIndex + ITEMS_PER_PAGE, filteredVocabs.length);
    const itemsToRender = filteredVocabs.slice(startIndex, endIndex);
    
    if (itemsToRender.length === 0) return;
    
    itemsToRender.forEach((v, relativeIdx) => {
        const item = document.createElement("div");
        item.className = "vocab-item";
        const idx = startIndex + relativeIdx;

        const hasExample = v.example && v.example.trim() !== "";

        item.innerHTML = `
            <div class="vocab-header">
                <div>
                    <div class="vocab-word">${escapeHtml(v.word)}</div>
                    ${v.pronunciation ? `<div class="vocab-pronunciation">/${escapeHtml(v.pronunciation)}/</div>` : ""}
                </div>
                ${v.word_type ? `<span class="badge">${escapeHtml(v.word_type)}</span>` : ""}
            </div>
            <div class="vocab-meaning">${formatText(v.meaning)}</div>
            ${hasExample ? `
            <button class="toggle-example-btn" data-idx="${idx}" data-open="false">📖 Xem ví dụ</button>
            <div class="vocab-example" id="example-block-${idx}">
                <div class="vocab-example-content">
                    ${formatText(v.example)}
                    ${v.example_meaning ? `<div class="vocab-example-meaning">${formatText(v.example_meaning)}</div>` : ""}
                </div>
            </div>` : ""}
        `;
        listContainer.appendChild(item);
    });

    // Handle Example Toggle with Smooth Accordion
    const toggleBtns = listContainer.querySelectorAll(".toggle-example-btn");
    // Only bind events to newly added buttons
    for (let i = toggleBtns.length - itemsToRender.length; i < toggleBtns.length; i++) {
        if (i < 0) continue;
        const btn = toggleBtns[i];
        btn.addEventListener("click", function() {
            const block = document.getElementById(`example-block-${this.dataset.idx}`);
            const isOpen = this.dataset.open === "true";
            if (isOpen) {
                block.classList.remove("expanded");
                this.textContent = "📖 Xem ví dụ";
                this.dataset.open = "false";
            } else {
                block.classList.add("expanded");
                this.textContent = "🔼 Ẩn ví dụ";
                this.dataset.open = "true";
            }
        });
    }
    
    if (endIndex >= filteredVocabs.length) {
        loadMoreTrigger.textContent = "Hết danh sách";
    } else {
        loadMoreTrigger.textContent = "Đang tải thêm...";
    }
}

// Intersection Observer for Lazy Loading
const listObserver = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting && filteredVocabs.length > currentPage * ITEMS_PER_PAGE) {
        currentPage++;
        renderList(false);
    }
}, { rootMargin: "100px" });
if (loadMoreTrigger) listObserver.observe(loadMoreTrigger);

// ─── Flashcard logic ──────────────────────────────────────────────────────────
const fcCard    = document.getElementById("flashcard");
const fcWord    = document.getElementById("fc-word");
const fcPron    = document.getElementById("fc-pronunciation");
const fcType    = document.getElementById("fc-type");
const fcMean    = document.getElementById("fc-meaning");
const fcEx      = document.getElementById("fc-example");
const fcExMean  = document.getElementById("fc-example-meaning");
const fcCounter = document.getElementById("fc-counter");
const fcAudioBox = document.getElementById("fc-audio-box");
const fcAudio   = document.getElementById("fc-audio");
const btnPlayAudio = document.getElementById("btn-play-audio");

function renderFlashcard() {
    fcCard.classList.remove("is-flipped");
    if (filteredVocabs.length === 0) {
        fcWord.textContent = "Không có thẻ";
        fcPron.textContent = "";
        fcType.textContent = "";
        fcMean.innerHTML = "Hãy thử thay đổi bộ lọc";
        fcEx.innerHTML   = "";
        fcExMean.innerHTML = "";
        fcCounter.textContent = "0 / 0";
        fcAudioBox.style.display = "none";
        return;
    }
    
    const v = filteredVocabs[flashcardIndex];

    // Mặt trước
    fcWord.textContent = v.word;
    fcPron.textContent = v.pronunciation ? `/${v.pronunciation}/` : "";
    fcType.textContent = v.word_type || "";

    // Mặt sau — dùng innerHTML để hiện \n thành xuống dòng
    fcMean.innerHTML   = formatText(v.meaning) || "<em style='color:var(--text-muted)'>Chưa có nghĩa</em>";
    fcEx.innerHTML     = formatText(v.example) || "<em style='color:var(--text-muted)'>Chưa có ví dụ</em>";
    fcExMean.innerHTML = formatText(v.example_meaning) || "";

    fcCounter.textContent = `${flashcardIndex + 1} / ${filteredVocabs.length}`;

    // ── Audio: MP3 nếu có, fallback Web Speech API ──
    fcAudioBox.style.display = "block"; // luôn hiện nút phát
    if (v.mp3_gdrive_id) {
        fcAudio.src = `https://docs.google.com/uc?export=download&id=${v.mp3_gdrive_id}`;
        btnPlayAudio.title = "Phát MP3 gốc";
        btnPlayAudio.dataset.ttsMode = "mp3";
    } else {
        fcAudio.src = "";
        btnPlayAudio.title = "Đọc bằng TTS (Text-to-Speech)";
        btnPlayAudio.dataset.ttsMode = "tts";
        btnPlayAudio.dataset.ttsWord = v.word;
    }
}

document.getElementById("btn-flip").addEventListener("click", () => {
    fcCard.classList.toggle("is-flipped");
});

fcCard.addEventListener("click", () => {
    fcCard.classList.toggle("is-flipped");
});

document.getElementById("btn-prev").addEventListener("click", () => {
    if (filteredVocabs.length === 0) return;
    flashcardIndex = (flashcardIndex - 1 + filteredVocabs.length) % filteredVocabs.length;
    renderFlashcard();
});

document.getElementById("btn-next").addEventListener("click", () => {
    if (filteredVocabs.length === 0) return;
    flashcardIndex = (flashcardIndex + 1) % filteredVocabs.length;
    renderFlashcard();
});

// ─── Keyboard shortcuts cho Flashcard (Space = lật, ←/→ = chuyển thẻ) ────────
document.addEventListener("keydown", (e) => {
    // Bỏ qua nếu đang gõ trong input/select/textarea hoặc modal luyện viết mở
    const tag = (document.activeElement && document.activeElement.tagName) || "";
    if (/^(INPUT|SELECT|TEXTAREA)$/.test(tag)) return;
    if (writingModal.style.display === "flex") return;
    if (!viewFlashcard.classList.contains("active")) return;

    if (e.code === "Space") {
        e.preventDefault();
        fcCard.classList.toggle("is-flipped");
    } else if (e.key === "ArrowLeft") {
        document.getElementById("btn-prev").click();
    } else if (e.key === "ArrowRight") {
        document.getElementById("btn-next").click();
    }
});

// ─── Language → SpeechSynthesis locale mapping ────────────────────────────
function getLangCode(langName) {
    const name = (langName || "").toLowerCase();
    if (name.includes("anh") || name.includes("english"))   return "en-US";
    if (name.includes("nh\u1eadt") || name.includes("japan")) return "ja-JP";
    if (name.includes("trung") || name.includes("chin"))    return "zh-CN";
    if (name.includes("vi\u1ec7t") || name.includes("viet"))  return "vi-VN";
    if (name.includes("h\u00e0n") || name.includes("korea"))  return "ko-KR";
    if (name.includes("ph\u00e1p") || name.includes("french")) return "fr-FR";
    if (name.includes("\u0111\u1ee9c") || name.includes("german")) return "de-DE";
    return "en-US"; // fallback
}

// ─── Web Speech API TTS ────────────────────────────────────────────────────
function speakWord(word, langCode) {
    if (!window.speechSynthesis) {
        alert("Trình duyệt của bạn không hỗ trợ Text-to-Speech.");
        return;
    }
    window.speechSynthesis.cancel(); // dừng nếu đang đọc
    const utter = new SpeechSynthesisUtterance(word);
    utter.lang = langCode;
    utter.rate = 0.9;  // tốc độ hơi chậm, dễ nghe
    utter.pitch = 1.0;

    // Thử chọn giọng native tốt nhất cho ngôn ngữ đó
    const voices = window.speechSynthesis.getVoices();
    const matched = voices.find(v => v.lang === langCode && !v.name.includes("Google"));
    const googleVoice = voices.find(v => v.lang === langCode);
    utter.voice = matched || googleVoice || null;

    window.speechSynthesis.speak(utter);
}

btnPlayAudio.addEventListener("click", (e) => {
    e.stopPropagation();
    if (btnPlayAudio.dataset.ttsMode === "tts") {
        const word     = btnPlayAudio.dataset.ttsWord || "";
        const langName = langSelect ? langSelect.value : "";
        speakWord(word, getLangCode(langName));
    } else {
        fcAudio.play();
    }
});

// ─── Debounce helper ──────────────────────────────────────────────────────────
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

// ─── Event Listeners ──────────────────────────────────────────────────────────
langSelect.addEventListener("change", (e) => loadLanguage(e.target.value));

// Use debounce for search input
searchInput.addEventListener("input", debounce(applyFilters, 300));
clearSearchBtn.addEventListener("click", () => {
    searchInput.value = "";
    applyFilters();
    searchInput.focus();
});
filterTopic.addEventListener("change", applyFilters);
filterType.addEventListener("change", applyFilters);
filterDate.addEventListener("change", applyFilters);

btnList.addEventListener("click", () => switchView("list"));

btnFlashcard.addEventListener("click", () => switchView("flashcard"));

btnCourse.addEventListener("click", () => switchView("course"));

btnReview.addEventListener("click", () => switchView("review"));

// ─── Khóa học AI (lưu database kiểu AskCpl: data/ai_courses/<lang>/course.json) ─
const daySelect = document.getElementById("course-day-select");
const courseContent = document.getElementById("course-content");
const progressBadge = document.getElementById("course-progress-badge");

let courseData = null;
let courseSlug = "";

// FIX: dropdown chọn ngày trước đây KHÔNG có listener → đổi ngày nội dung
// vẫn kẹt ở ngày đầu (renderCourseDay chỉ chạy 1 lần trong renderCourseShell).
daySelect.addEventListener("change", (e) => {
    const n = Number(e.target.value);
    if (n && courseData) renderCourseDay(n);
});

function courseProgressKey() {
    return `vocabapp_ai_progress_${courseSlug}`;
}

function getCourseProgress() {
    try {
        return JSON.parse(localStorage.getItem(courseProgressKey()) || "{}");
    } catch (e) { return {}; }
}

function saveCourseProgress(p) {
    localStorage.setItem(courseProgressKey(), JSON.stringify(p));
}

// ─── Khóa học: tải THEO NGÀY thay vì cả file (Gói 3) ──────────────────────────
// Trước: web tải TOÀN BỘ course.json (khóa Nhật 47 MB) + manifest media
// 38 MB ⇒ mở tab nặng, đổi ngày không nhẹ. Nay: API index (danh sách ngày)
// + API day/<n> (1 ngày ~40 KB), có fallback về course.json cũ.
let courseIndex = null;      // [{day,title,phase,topic}]
let courseDayCache = {};     // day → lesson

// ─── BẢN ONLINE (Gói 10): nguồn dữ liệu tĩnh + gói media .zip ───────────────
const VOCAB_DATA_CFG = (typeof window !== "undefined" && window.VOCAB_DATA) || null;
let staticCourseMeta = null;              // index.json của khóa (chế độ static)
let staticMediaMap = {};                  // ref → rel_path (của ngày đang xem)
let currentLessonDay = 1;                 // ngày đang xem (để tìm gói media)
let mediaBundles = {};                    // "slug|m01" → { "d0010/x.webp": BlobURL }
let mediaBundlePromise = {};              // chống tải trùng gói

function _cfgMode() {
    return (VOCAB_DATA_CFG && VOCAB_DATA_CFG.mode) || "local";
}

/** Đường dẫn gói .zip của 1 (khóa, nhóm 30 ngày) trên GitHub Releases. */
function _bundleUrl(slug, monthKey) {
    if (!VOCAB_DATA_CFG || !VOCAB_DATA_CFG.releases) return "";
    const tag = VOCAB_DATA_CFG.releases[slug];
    if (!tag) return "";
    return `https://github.com/${VOCAB_DATA_CFG.repo}/releases/download/${tag}/m${monthKey}.zip`;
}

/** index.json của repo dữ liệu: { "<slug>": {dir, months} } (cache localStorage). */
let mediaIndexCfg = null;
async function _mediaIndex() {
    if (mediaIndexCfg) return mediaIndexCfg;
    const ck = "vocab_media_index_v1";
    try {
        const raw = localStorage.getItem(ck);
        if (raw) {
            const o = JSON.parse(raw);
            // TTL 1 ngày — để khóa mới thêm vào repo dữ liệu sớm được nhận.
            if (o && o.d && (Date.now() - (o.t || 0)) < 24 * 3600 * 1000) {
                mediaIndexCfg = o.d;
                return o.d;
            }
        }
    } catch (e) { }
    const r = await fetch(`${VOCAB_DATA_CFG.mediaRawBase}/index.json`, { cache: "no-cache" });
    if (!r.ok) throw new Error("HTTP " + r.status);
    const d = await r.json();
    mediaIndexCfg = d;
    try { localStorage.setItem(ck, JSON.stringify({ t: Date.now(), d })); } catch (e) { }
    return d;
}

/** Danh sách asset của 1 release (cache RAM + localStorage 7 ngày).
 *  ⚠ GitHub API không token chỉ cho **60 request/giờ/IP** ⇒ phải cache để
 *  mở app nhiều lần không bị 403. */
let releaseCache = {};
async function _releaseAssets(tag) {
    if (releaseCache[tag]) return releaseCache[tag];
    const ck = "vocab_rel_" + tag;
    const readCache = () => {
        try {
            const raw = localStorage.getItem(ck);
            if (!raw) return null;
            const o = JSON.parse(raw);
            return (o && Array.isArray(o.a)) ? o : null;
        } catch (e) { return null; }
    };
    const old = readCache();
    if (old && (Date.now() - (old.t || 0)) < 7 * 24 * 3600 * 1000) {
        releaseCache[tag] = old.a;
        return old.a;
    }
    const r = await fetch(`https://api.github.com/repos/${VOCAB_DATA_CFG.repo}/releases/tags/${encodeURIComponent(tag)}`);
    if (!r.ok) {
        // 403 = hết quota 60/giờ ⇒ dùng cache cũ (nếu có) thay vì bỏ media.
        if (old) { releaseCache[tag] = old.a; return old.a; }
        throw new Error("HTTP " + r.status);
    }
    const j = await r.json();
    const assets = (j.assets || []).map(a => ({ id: a.id, name: a.name, size: a.size }));
    releaseCache[tag] = assets;
    try { localStorage.setItem(ck, JSON.stringify({ t: Date.now(), a: assets })); } catch (e) { }
    return assets;
}

/**
 * Tải 1 gói .zip từ GitHub Releases.
 * ⚠ KHÔNG dùng `github.com/.../releases/download/...` — bị CORS chặn (đo thật:
 *   "blocked by CORS policy: No 'Access-Control-Allow-Origin'"). Phải đi qua
 *   api.github.com (có CORS) với header Accept: application/octet-stream.
 */
async function _fetchBundleBytes(slug, monthKey) {
    const cacheKey = `https://vocab.local/media/${encodeURIComponent(slug)}/m${monthKey}.zip`;
    let cache = null;
    try {
        if (typeof caches !== "undefined") cache = await caches.open("vocab-media-v1");
        if (cache) {
            const hit = await cache.match(cacheKey);
            if (hit) return await hit.arrayBuffer();
        }
    } catch (e) { cache = null; }

    // 1) REPO DỮ LIỆU qua raw.githubusercontent.com — CÓ CORS, không giới hạn
    //    60 request/giờ như api.github.com.
    try {
        const idx = await _mediaIndex();
        const info = idx[slug];
        if (info && info.dir) {
            const url = `${VOCAB_DATA_CFG.mediaRawBase}/${info.dir}/m${monthKey}.zip`;
            const r = await fetch(url);
            if (r.ok) {
                const buf = await r.arrayBuffer();
                if (cache && buf.byteLength > 1024) {
                    try { await cache.put(cacheKey, new Response(buf.slice(0))); } catch (e) { }
                }
                return buf;
            }
            if (r.status === 404) return null;   // tháng chưa có gói
        }
    } catch (e) {
        console.warn("raw media lỗi, thử GitHub API", e);
    }

    // 2) Fallback: GitHub Releases qua API (có thể bị CORS ở bước tải bytes)
    const tag = VOCAB_DATA_CFG.releases && VOCAB_DATA_CFG.releases[slug];
    if (!tag) return null;
    const assets = await _releaseAssets(tag);
    const name = `m${monthKey}.zip`;
    const a = assets.find(x => x.name === name);
    if (!a) return null;
    const r = await fetch(`https://api.github.com/repos/${VOCAB_DATA_CFG.repo}/releases/assets/${a.id}`,
        { headers: { Accept: "application/octet-stream" } });
    if (!r.ok) throw new Error("HTTP " + r.status);
    const buf = await r.arrayBuffer();
    if (cache && buf.byteLength > 1024) {
        try { await cache.put(cacheKey, new Response(buf.slice(0))); } catch (e) { }
    }
    return buf;
}

/** Tải + giải nén 1 gói media (nếu chưa có) → map đường dẫn → object URL. */
async function ensureMediaBundle(slug, monthKey) {
    if (_cfgMode() !== "static") return null;
    const key = `${slug}|m${monthKey}`;
    if (mediaBundles[key]) return mediaBundles[key];
    if (mediaBundlePromise[key]) return mediaBundlePromise[key];
    mediaBundlePromise[key] = (async () => {
        try {
            if (!(window.VOCAB_ZIP && VOCAB_ZIP.supported())) {
                console.warn("Bộ giải nén ZIP không khả dụng (DecompressionStream)");
                return null;
            }
            const buf = await _fetchBundleBytes(slug, monthKey);
            if (!buf) return null;
            const files = await VOCAB_ZIP.read(buf);
            const map = {};
            for (const [name, bytes] of Object.entries(files)) {
                // "d0010/word_00_x.webp" → "media/<slug>/d0010/word_00_x.webp"
                map[`media/${slug}/${name}`] = URL.createObjectURL(
                    new Blob([bytes], { type: _mimeOf(name) }));
            }
            mediaBundles[key] = map;
            return map;
        } catch (e) {
            console.warn("Không tải được gói media", key, e);
            const m = String(e && e.message || e);
            if (m.includes("403")) {
                _notifyMediaLimited("⚠ GitHub tạm giới hạn lượt tải (60 lượt/giờ cho mỗi IP). "
                    + "Nội dung chữ vẫn học bình thường; ảnh/âm thanh sẽ tự có lại sau ít phút. "
                    + "Gói media đã tải trước đó vẫn dùng được.");
            } else if (m.includes("404")) {
                _notifyMediaLimited("⚠ Gói media của tháng này chưa có trên GitHub Releases "
                    + "(media đang được bổ sung dần). Nội dung chữ vẫn học được.");
            }
            return null;
        } finally {
            delete mediaBundlePromise[key];
        }
    })();
    return mediaBundlePromise[key];
}

/** Cảnh báo 1 lần khi GitHub giới hạn lượt tải (60/giờ/IP). */
let _mediaLimitWarned = false;
function _notifyMediaLimited(msg) {
    if (_mediaLimitWarned) return;
    _mediaLimitWarned = true;
    const box = document.getElementById("course-content");
    if (!box) return;
    const div = document.createElement("div");
    div.className = "media-limit-note";
    div.style.cssText = "margin:10px 0;padding:10px 12px;border-radius:10px;"
        + "background:rgba(255,193,7,.12);border:1px solid rgba(255,193,7,.35);"
        + "color:#ffd54f;font-size:.9em;line-height:1.45;";
    div.textContent = msg;
    box.insertBefore(div, box.firstChild);
}

function _mimeOf(name) {
    if (name.endsWith(".webp")) return "image/webp";
    if (name.endsWith(".png")) return "image/png";
    if (name.endsWith(".jpg") || name.endsWith(".jpeg")) return "image/jpeg";
    if (name.endsWith(".mp3")) return "audio/mpeg";
    if (name.endsWith(".wav")) return "audio/wav";
    return "application/octet-stream";
}

/** Ngày thuộc nhóm 30 ngày nào (trùng với tools/publish_online.py). */
function _monthKeyOf(day) {
    // Python: mkey = day // 30 + 1  ⇒ ngày 1-29 → 01, 30-59 → 02, 60-89 → 03
    return String(Math.floor(Number(day) / 30) + 1).padStart(2, "0");
}


async function ensureCourseLoaded() {
    const slug = slugOf(currentLanguage);
    if (!slug) {
        // Gói 10: chưa chọn được ngôn ngữ (đang tải danh sách) ⇒ chờ, đừng
        // báo "Chưa có khóa học AI" (sai lệch thông tin).
        return;
    }
    if (courseData && courseSlug === slug) { renderCourseShell(); return; }
    courseSlug = slug;
    courseData = null;
    courseIndex = null;
    courseDayCache = {};

    // 0) BẢN ONLINE (GitHub Pages) — nội dung tĩnh theo ngày.
    //    data/<slug>/index.json + data/<slug>/day/<n>.json  (~14 KB/ngày)
    if (VOCAB_DATA_CFG && VOCAB_DATA_CFG.mode === "static") {
        try {
            const base = `${VOCAB_DATA_CFG.dataBase}/${encodeURIComponent(slug)}`;
            const ir = await fetch(`${base}/index.json`).catch(() => null);
            if (ir && ir.ok) {
                const idx = await ir.json();
                if (idx && Array.isArray(idx.days) && idx.days.length) {
                    courseIndex = idx.days;
                    staticCourseMeta = idx;
                    courseData = { days: idx.days, level: idx.level || "" };
                    renderCourseShell();
                    return;
                }
            }
        } catch (e) { /* không có dữ liệu tĩnh ⇒ thử API bên dưới */ }
    }

    // 1) API nhẹ: index + tải từng ngày
    try {
        const r = await fetch(`api/vocab/course/${encodeURIComponent(slug)}/index`);
        if (r.ok) {
            const j = await r.json();
            if (j && j.ok && Array.isArray(j.days) && j.days.length) {
                courseIndex = j.days;
                courseData = { days: j.days, level: j.level || "" };
                // Gói 9: KHÔNG nạp manifest ở đây — renderCourseDay sẽ nạp
                // manifest THEO NGÀY (vài KB) để trang mở nhanh.
                renderCourseShell();
                return;
            }
        }
    } catch (e) { /* không có API ⇒ fallback bên dưới */ }

    // 2) fallback: tải course.json (file lớn)
    try {
        let res = await fetch(`data/ai_courses/${slug}/course.json`).catch(() => null);
        if (!res || !res.ok) res = await fetch(`../data/ai_courses/${slug}/course.json`).catch(() => null);
        if (!res || !res.ok) throw new Error("no course");
        courseData = await res.json();
    } catch (e) {
        daySelect.innerHTML = "<option value=''>—</option>";
        progressBadge.textContent = "";
        // Không còn nhắc việc đẩy dữ liệu lên git — dữ liệu nằm NGAY trên máy,
        // trang đọc trực tiếp từ data/ local qua server của app.
        const tip = (location.protocol === "file:")
            ? `⚠ Trang đang mở sai cách (file://).<br>
                Dữ liệu (từ vựng · ảnh · âm thanh) nằm <b>ngay trên máy bạn</b> —<br>
                mở app VocabApp rồi vào <b>http://127.0.0.1:5690/index</b> là thấy ngay, không cần GitHub.`
            : `🤖 Chưa có khóa học AI cho <b>${escapeHtml(currentLanguage || "(chưa chọn khóa)")}</b>.<br><br>
                Mở app desktop → tab 🎓 Học Tập → bấm 🤖 Sinh khóa học AI —<br>
                khóa học lưu ngay trên máy, trang này đọc trực tiếp từ <b>data/</b> local.`;
        courseContent.innerHTML = `
            <p style="color:var(--text-muted);padding:30px 10px;text-align:center;">
                ${tip}
            </p>`;
        return;
    }
    // Gói 9 (17/11): KHÔNG nạp manifest toàn bộ ở đây (103 MB) — renderCourseDay
    // sẽ nạp manifest THEO NGÀY (vài KB) ⇒ trang mở nhanh.
    renderCourseShell();
}

// ─── Manifest media (ảnh minh họa + âm thanh) ───────────────────────────────
let mediaIndex = null;
let mediaIndexPromise = null;
const mediaLoadedDays = new Set();

// Gói 9 (17/11): manifest media đầy đủ = 211.524 entry ≈ 103 MB ⇒ tải file
// mất **82 giây** (đo thật) ⇒ trang học như đứng hình. Nay nạp manifest
// **theo ngày** qua API `/api/media/manifest?slug=..&day=..` ⇒ chỉ vài chục KB.
async function loadMediaIndex(day) {
    const slug = (typeof slugOf === "function" ? slugOf(currentLanguage) : (currentLanguage || ""));
    const key = day ? `${slug}#${day}` : slug;
    if (mediaLoadedDays.has(key)) return mediaIndex;

    // 1) API theo ngày (nhanh)
    try {
        const q = day ? `?slug=${encodeURIComponent(slug)}&day=${encodeURIComponent(day)}`
                      : `?slug=${encodeURIComponent(slug)}`;
        const res = await fetch(`api/media/manifest${q}`).catch(() => null);
        if (res && res.ok) {
            const j = await res.json();
            if (j && j.items) {
                mediaIndex = mediaIndex || { items: {} };
                Object.assign(mediaIndex.items, j.items);
                mediaLoadedDays.add(key);
                return mediaIndex;
            }
        }
    } catch (e) { /* fallback xuống dưới */ }

    // 2) Fallback: tải file manifest đầy đủ (chậm nhưng vẫn hoạt động)
    if (mediaIndexPromise) return mediaIndexPromise;
    mediaIndexPromise = (async () => {
        try {
            let res = await fetch("data/media/index.json").catch(() => null);
            if (!res || !res.ok) res = await fetch("../data/media/index.json").catch(() => null);
            if (!res || !res.ok) { mediaIndex = { items: {} }; return mediaIndex; }
            mediaIndex = await res.json();
            if (!mediaIndex.items) mediaIndex.items = {};
        } catch (e) {
            mediaIndex = { items: {} };
        }
        return mediaIndex;
    })();
    return mediaIndexPromise;
}

function mediaEntry(ref) {
    if (!ref) return null;
    // BẢN ONLINE: ref → đường dẫn file lấy từ `media_map` của ngày (đã tải).
    if (_cfgMode() === "static") {
        const rel = staticMediaMap[ref];
        if (rel) return { rel_path: rel, _static: true };
        // Chưa tải gói media ⇒ thử đường dẫn trực tiếp (nếu bản deploy có
        // kèm media) — nếu không thì trả null ⇒ hiện "chưa có media".
        return null;
    }
    let r = (mediaIndex && mediaIndex.items) ? mediaIndex.items[ref] : null;
    if (r) return r;
    // Parity desktop: ref không phải m_* → chấp nhận rel_path kho data/
    // ("media/<slug>/d0001/x.webp" hoặc "audio/<slug>/.../x.mp3", có thể "data/" prefix).
    if (typeof ref !== "string") return null;
    const safe = String(ref).trim().replace(/\\/g, "/").replace(/^data\//, "");
    if (!safe || safe.includes("..") || safe.startsWith("/")) return null;
    if (!/^(media|audio)\//.test(safe)) return null;
    return { rel_path: safe, _direct: true };
}

function mediaUrl(ref) {
    const e = mediaEntry(ref);
    if (!e) return "";
    if (e.url) return e.url;
    if (!e.rel_path) return "";
    // Bản ONLINE: file nằm trong gói .zip đã giải nén ⇒ dùng object URL.
    if (e._static) {
        const rel = e.rel_path;
        for (const k of Object.keys(mediaBundles)) {
            const b = mediaBundles[k];
            if (b && b[rel]) return b[rel];
        }
        return "";      // chưa có gói media ⇒ không hiện ảnh/audio
    }
    // rel_path = "media/<slug>/d0001/xxx.webp" ; web root chứa "data/"
    return "data/" + e.rel_path;
}

function mediaImgHtml(ref, alt) {
    const e = mediaEntry(ref);
    if (!e) return "";
    const url = mediaUrl(ref);
    if (!url) return "";
    const credit = e.credit ? `<div class="media-credit">📷 ${escapeHtml(e.credit)}${e.license ? " · " + escapeHtml(e.license) : ""}</div>` : "";
    // FIX 2026-11-12 (Gói 3): file hỏng → hiện chip cảnh báo thay vì xoá im
    // lặng (trước: onerror xoá element ⇒ người dùng không biết là "không có
    // ảnh" hay "tải hỏng").
    return `<div class="media-img-wrap">
        <img class="media-img" loading="lazy" src="${escapeHtml(url)}" alt="${escapeHtml(alt || "")}"
             onerror="this.style.display='none';this.parentNode?.querySelector('.media-missing')?.remove();this.parentNode?.insertAdjacentHTML('beforeend','<div class=&quot;media-missing&quot;>⚠ Ảnh không tải được</div>');">
        ${credit}
    </div>`;
}

function mediaAudioHtml(ref, label) {
    const e = mediaEntry(ref);
    if (!e) return "";
    const url = mediaUrl(ref);
    if (!url) return "";
    // FIX 2026-11-12 (Gói 3): lỗi/404 → chip "⚠ Không có audio" (thay vì
    // xoá lặng lẽ ⇒ không phân biệt được "chưa sinh" với "file hỏng").
    return `<span class="media-audio-wrap">
        <audio class="media-audio" controls preload="none" src="${escapeHtml(url)}"
               onerror="this.style.display='none';this.parentNode?.querySelector('.media-missing')?.remove();this.parentNode?.insertAdjacentHTML('beforeend','<span class=&quot;media-missing&quot;>⚠ Không có audio</span>');"></audio>
    </span>`;
}

function renderCourseShell() {
    const days = (courseData.days || []).slice().sort((a, b) => a.day - b.day);
    const prog = getCourseProgress();
    const completed = new Set(prog.completed_days || []);
    const level = (courseData.level || "").trim();
    const levelTag = level ? ` · trình độ: ${escapeHtml(level)}` : "";
    progressBadge.textContent = `Hoàn thành ${completed.size}/${days.length} ngày${levelTag}`;

    daySelect.innerHTML = days.map(d => {
        const topic = (d.topic || d.title || "").trim();
        const short = topic.length > 24 ? topic.slice(0, 24) + "…" : topic;
        return `<option value="${d.day}">Ngày ${d.day}${short ? " · " + escapeHtml(short) : ""}${completed.has(d.day) ? " ✅" : ""}</option>`;
    }).join("");
    const firstPending = days.find(d => !completed.has(d.day));
    const initialDay = (firstPending || days[0]).day;
    daySelect.value = String(initialDay);
    renderCourseDay(initialDay);
}

function flattenQuiz(quizData) {
    if (Array.isArray(quizData)) return quizData;
    if (!quizData || typeof quizData !== "object") return [];
    const catNames = { vocab: "Từ vựng", pattern: "Cách dùng câu",
                       common: "Câu thông dụng", grammar: "Ngữ pháp", mixed: "Tổng hợp" };
    const out = [];
    ["vocab", "pattern", "common", "grammar", "mixed"].forEach(cat => {
        (quizData[cat] || []).forEach(q => {
            if (q && q.question) {
                out.push(Object.assign({}, q, { _category: catNames[cat] || cat }));
            }
        });
    });
    return out;
}

/** Bao bọc render: lỗi dữ liệu không được để màn hình kẹt "Đang tải…". */
async function renderCourseDay(dayNum) {
    try {
        return await _renderCourseDay(dayNum);
    } catch (e) {
        console.error("renderCourseDay lỗi", dayNum, e);
        const box = document.getElementById("course-content");
        if (box) {
            box.innerHTML = `<p style="color:var(--danger);padding:20px;text-align:center;line-height:1.5;">
                ⚠ Không hiển thị được Ngày ${escapeHtml(String(dayNum))}.<br>
                <span style="font-size:.85em;color:var(--text-muted);">${escapeHtml(String(e && e.message || e))}</span>
            </p>`;
        }
    }
}

async function _renderCourseDay(dayNum) {
    let lesson = (courseData.days || []).find(d => Number(d.day) === Number(dayNum));
    // Gói 3: khi dùng API theo ngày, `courseData.days` chỉ là metadata ⇒ phải
    // tải nội dung ngày đó (cache theo ngày).
    if (!lesson || !(lesson.vocab || lesson.quiz || lesson.dialogue)) {
        const cached = courseDayCache[dayNum];
        if (cached) {
            lesson = cached;
        } else if (courseIndex) {
            courseContent.innerHTML =
                `<p style="color:var(--text-muted);padding:20px;text-align:center;">⏳ Đang tải Ngày ${dayNum}…</p>`;
            // Bản ONLINE: nội dung tĩnh theo ngày (data/<slug>/day/<n>.json)
            if (_cfgMode() === "static") {
                try {
                    const base = `${VOCAB_DATA_CFG.dataBase}/${encodeURIComponent(slugOf(currentLanguage))}`;
                    const r = await fetch(`${base}/day/${String(dayNum).padStart(4, "0")}.json`);
                    if (r.ok) {
                        const j = await r.json();
                        if (j && (j.vocab || j.quiz || j.dialogue)) {
                            lesson = j;
                            courseDayCache[dayNum] = lesson;
                            staticMediaMap = j.media_map || staticMediaMap;
                        }
                    }
                } catch (e) { /* không có ⇒ thử API bên dưới */ }
            }
            if (!lesson) {
                try {
                    const r = await fetch(`api/vocab/course/${encodeURIComponent(slugOf(currentLanguage))}/day/${dayNum}`);
                    if (r.ok) {
                        const j = await r.json();
                        if (j && j.ok && j.lesson) {
                            lesson = j.lesson;
                            courseDayCache[dayNum] = lesson;
                        }
                    }
                } catch (e) { /* giữ nguyên nội dung cũ */ }
            }
        }
    }
    if (!lesson) return;
    currentLessonDay = Number(dayNum) || 1;
    // Gói 9 (17/11): nạp manifest media CỦA NGÀY NÀY (vài KB) trước khi vẽ
    // ⇒ không phải tải manifest 103 MB. Nếu API lỗi ⇒ fallback tải file.
    if (_cfgMode() !== "static") {
        try { await loadMediaIndex(dayNum); } catch (e) { /* bỏ qua */ }
    } else if (VOCAB_DATA_CFG.autoFetchMedia) {
        // Bản ONLINE: tải gói .zip của nhóm 30 ngày chứa ngày này (~11 MB)
        try { await ensureMediaBundle(slugOf(currentLanguage), _monthKeyOf(dayNum)); } catch (e) { }
    }
    const prog = getCourseProgress();
    const alreadyDone = new Set(prog.completed_days || []).has(Number(dayNum));

    let html = `<div class="lesson-title">📚 Ngày ${lesson.day} — ${escapeHtml(lesson.title || "")}</div>`;
    const phase = (lesson.phase || "").trim();
    if (phase) {
        html += `<div style="margin:-4px 0 10px;"><span class="phase-badge">🏷️ ${escapeHtml(phase)}</span></div>`;
    }

    // ── Từ vựng ──
    (lesson.vocab || []).forEach((v, i) => {
        const ipa = v.ipa || v.pronunciation || "";
        const showIpa = ipa && ipa !== v.pronunciation;
        const sources = (Array.isArray(v.sources) ? v.sources : []).filter(Boolean);
        const hasEvidence = sources.length > 0 || v.etymology;
        const audioRef = (lesson.media && lesson.media.vocab_audio)
            ? (lesson.media.vocab_audio[v.word] || v.audio_ref) : v.audio_ref;
        html += `
        <div class="vocab-item">
            <div class="vocab-header">
                <div>
                    <div class="vocab-word">${i + 1}. ${escapeHtml(v.word)}</div>
                    ${v.pronunciation ? `<div class="vocab-pronunciation">/${escapeHtml(v.pronunciation)}/</div>` : ""}
                    ${showIpa ? `<div class="vocab-ipa" title="Phiên âm quốc tế">🔊 ${escapeHtml(ipa)}</div>` : ""}
                    ${v.ipa_ev && v.ipa_ev !== ipa ? `<div class="vocab-ipa" title="IPA chuẩn theo Wiktionary">📖 ${escapeHtml(v.ipa_ev)}</div>` : ""}
                    ${v.pos ? `<span class="pos-badge">${escapeHtml(v.pos)}</span>` : ""}
                </div>
                ${v.part_of_speech ? `<span class="badge">${escapeHtml(v.part_of_speech)}</span>` : ""}
            </div>
            ${mediaImgHtml(v.image_ref, v.meaning_vi || v.word)}
            <div class="vocab-meaning">${escapeHtml(v.meaning_vi || "")}</div>
            ${v.phonetic_note ? `<div class="phonetic-note">👄 ${escapeHtml(v.phonetic_note)}</div>` : ""}
            ${v.explanation ? `<div class="lesson-explanation">💡 ${formatText(v.explanation)}</div>` : ""}
            ${v.example_sentence ? `
            <div class="vocab-example expanded">
                <div class="vocab-example-content">
                    ${formatText(v.example_sentence)}
                    ${v.example_meaning_vi ? `<div class="vocab-example-meaning">${formatText(v.example_meaning_vi)}</div>` : ""}
                </div>
            </div>` : ""}
            ${audioRef ? `<div class="media-audio-row">${mediaAudioHtml(audioRef, v.word)}</div>` : ""}
            ${v.meaning_audio_ref ? `<div class="media-audio-row"><span class="media-audio-label">🔈 Nghĩa (tiếng Việt)</span>${mediaAudioHtml(v.meaning_audio_ref, v.meaning_vi)}</div>` : ""}
            ${hasEvidence ? `
            <div class="evidence-box">
                ${sources.map(s => {
                    const linkText = s.title || s.kind || "nguồn";
                    return `<div class="evidence-source">
                    ${s.url ? `<a href="${escapeHtml(s.url)}" target="_blank" rel="noopener noreferrer">📚 ${escapeHtml(linkText)}</a>` : `<span>📚 ${escapeHtml(linkText)}</span>`}
                    ${s.license ? `<span class="evidence-license"> — ${escapeHtml(s.license)}</span>` : ""}
                    ${s.quote ? `<div class="evidence-quote">“${escapeHtml(String(s.quote).slice(0, 160))}”</div>` : ""}
                </div>`;
                }).join("")}
                ${v.etymology ? `<div class="evidence-etymology">🏛️ Từ nguyên: ${escapeHtml(String(v.etymology).slice(0, 200))}</div>` : ""}
            </div>` : ""}
        </div>`;
    });

    // ── Cách dùng câu ──
    const patterns = lesson.sentence_patterns || [];
    if (patterns.length) {
        html += `<div class="section-title">📝 Cách dùng câu / Mẫu câu</div>`;
        patterns.forEach((p, i) => {
            html += `<div class="pattern-item">
                <b>${i + 1}. ${escapeHtml(p.pattern || "")}</b> — ${escapeHtml(p.meaning_vi || "")}
                ${p.structure_note ? `<div class="pattern-note">${escapeHtml(p.structure_note)}</div>` : ""}
                ${p.example_sentence ? `<div class="pattern-example">💬 ${formatText(p.example_sentence)}${p.example_meaning_vi ? `<div class="vocab-example-meaning">${formatText(p.example_meaning_vi)}</div>` : ""}</div>` : ""}
            </div>`;
        });
    }

    // ── Câu thông dụng ──
    const common = lesson.common_sentences || [];
    if (common.length) {
        html += `<div class="section-title">💬 Câu thông dụng giao tiếp</div>`;
        common.forEach((s, i) => {
            html += `<div class="common-item">
                <b>${i + 1}.</b> ${escapeHtml(s.sentence || "")} — ${escapeHtml(s.meaning_vi || "")}
                ${s.situation ? `<div class="common-situation">📌 ${escapeHtml(s.situation)}</div>` : ""}
            </div>`;
        });
    }

    // ── Ngữ pháp (list hoặc dict cũ) ──
    let grammarItems = lesson.grammar || [];
    if (!Array.isArray(grammarItems)) grammarItems = grammarItems.title ? [grammarItems] : [];
    if (grammarItems.length) {
        html += `<div class="section-title">📐 Ngữ pháp</div>`;
        grammarItems.forEach((g, gi) => {
            // FIX 2026-11-19: `common_mistakes` trong dữ liệu có thể là CHUỖI
            // (69.964 mục ở cả 8 khóa) chứ không phải mảng. Trước đây gọi
            // `.map()` lên chuỗi ⇒ TypeError ⇒ màn hình kẹt "Đang tải…".
            const mistakes = Array.isArray(g.common_mistakes)
                ? g.common_mistakes
                : (g.common_mistakes ? [g.common_mistakes] : []);
            html += `<div class="grammar-box">
                <h4>Bài ${gi + 1}: ${escapeHtml(g.title || "")}</h4>
                <div>${formatText(g.explanation || "")}</div>
                ${(Array.isArray(g.examples) ? g.examples : []).map(ex => `
                    <div style="margin-top:8px;">💬 ${formatText(ex.sentence || "")}
                        ${ex.meaning_vi ? `<div class="vocab-example-meaning">${formatText(ex.meaning_vi)}</div>` : ""}
                    </div>`).join("")}
                ${g.pronunciation_focus ? `<div class="phonetic-note">👄 ${escapeHtml(g.pronunciation_focus)}</div>` : ""}
                ${mistakes.map(m => {
                    if (typeof m === "string") {
                        return `<div class="mistake-box"><div class="mistake-note">⚠️ ${escapeHtml(m)}</div></div>`;
                    }
                    if (!m || typeof m !== "object") return "";
                    return `<div class="mistake-box">
                        <div class="mistake-wrong">❌ ${escapeHtml(m.wrong || "")}</div>
                        <div class="mistake-right">✅ ${escapeHtml(m.right || "")}</div>
                        ${m.why_vi ? `<div class="vocab-example-meaning">${escapeHtml(m.why_vi)}</div>` : ""}
                    </div>`;
                }).join("")}
            </div>`;
        });
    }

    // ── HộI THOẠI (roleplay) ──
    const dialogues = lesson.dialogue || [];
    if (dialogues.length) {
        html += `<div class="section-title">💬 Hội thoại (Roleplay)</div>`;
        dialogues.forEach((dlg, di) => {
            const dAudio = (lesson.media && lesson.media.dialogue_audio)
                ? (lesson.media.dialogue_audio[String(di)] || dlg.audio_ref) : dlg.audio_ref;
            html += `<div class="dialogue-box">
                <div class="dialogue-head">
                    <b>${escapeHtml(dlg.title || `Kịch bản ${di + 1}`)}</b>
                    ${dlg.level_tag ? `<span class="phase-badge">${escapeHtml(dlg.level_tag)}</span>` : ""}
                </div>
                ${dlg.situation ? `<div class="dialogue-situation">📌 ${escapeHtml(dlg.situation)}</div>` : ""}
                ${dAudio ? `<div class="media-audio-row">${mediaAudioHtml(dAudio, dlg.title || "")}</div>` : ""}
                ${(dlg.turns || []).map(t => `
                    <div class="dialogue-turn">
                        <span class="dialogue-speaker">${escapeHtml(t.speaker || "A")}</span>
                        <div class="dialogue-line">
                            <div class="dialogue-target">${formatText(t.line_target || "")}</div>
                            ${t.line_vi ? `<div class="vocab-example-meaning">${formatText(t.line_vi)}</div>` : ""}
                            ${t.tone || t.emotion ? `<div class="dialogue-tone">🎭 ${escapeHtml([t.emotion, t.tone].filter(Boolean).join(" · "))}</div>` : ""}
                        </div>
                    </div>`).join("")}
                ${dlg.cultural_note ? `<div class="dialogue-culture">🌏 ${escapeHtml(dlg.cultural_note)}</div>` : ""}
            </div>`;
        });
    }

    // ── Trắc nghiệm ──
    const quiz = flattenQuiz(lesson.quiz);
    if (quiz.length) {
        const catCounts = {};
        quiz.forEach(q => { const c = q._category || ""; catCounts[c] = (catCounts[c] || 0) + 1; });
        const summary = Object.entries(catCounts).map(([c, n]) => `${c} (${n})`).join(" · ");
        html += `<h3 style="margin-top:18px;">📝 Trắc nghiệm Ngày ${lesson.day} — ${summary}</h3>`;
        quiz.forEach((q, qi) => {
            const catBadge = q._category ? `<span class="quiz-cat-badge">${escapeHtml(q._category)}</span>` : "";
            html += `<div class="quiz-q" data-qi="${qi}">
                <b>${qi + 1}. ${catBadge} ${formatText(q.question)}</b>
                ${(q.options || []).map((opt, oi) =>
                    `<button class="quiz-opt" data-oi="${oi}">${String.fromCharCode(65 + oi)}. ${escapeHtml(opt)}</button>`
                ).join("")}
                <div class="quiz-exp"></div>
            </div>`;
        });
        html += `<button id="btn-submit-quiz" class="submit-btn">✅ Nộp bài</button>
                 <div id="quiz-result"></div>`;
        if (alreadyDone && prog.quiz_scores && prog.quiz_scores[String(dayNum)] != null) {
            html += `<p style="text-align:center;color:var(--success);margin-top:8px;">
                        ✅ Bạn đã hoàn thành ngày này — điểm cao nhất: ${prog.quiz_scores[String(dayNum)].score}% (có thể làm lại)
                     </p>`;
        }
    }

    courseContent.innerHTML = html;
    window.scrollTo({ top: 0 });

    if (quiz.length) bindQuiz(lesson, quiz);
}

function bindQuiz(lesson, quiz) {
    const answers = {};
    document.querySelectorAll(".quiz-q").forEach(qEl => {
        qEl.querySelectorAll(".quiz-opt").forEach(btnEl => {
            btnEl.addEventListener("click", () => {
                qEl.querySelectorAll(".quiz-opt").forEach(b => b.classList.remove("selected"));
                btnEl.classList.add("selected");
                answers[qEl.dataset.qi] = parseInt(btnEl.dataset.oi, 10);
            });
        });
    });

    document.getElementById("btn-submit-quiz").addEventListener("click", () => {
        let correct = 0;
        quiz.forEach((q, qi) => {
            const qEl = document.querySelector(`.quiz-q[data-qi="${qi}"]`);
            const chosen = answers[qi];
            qEl.querySelectorAll(".quiz-opt").forEach(b => {
                b.disabled = true;
                const oi = parseInt(b.dataset.oi, 10);
                if (oi === q.answer_index) b.classList.add("correct");
                else if (oi === chosen) b.classList.add("wrong");
            });
            const exp = qEl.querySelector(".quiz-exp");
            exp.style.display = "block";
            if (chosen === q.answer_index) correct++;
            exp.textContent = (chosen === q.answer_index ? "✅ Đúng! " : "❌ Sai. ")
                + "💡 " + (q.explanation || "");
        });
        const score = Math.round(correct / quiz.length * 100);
        document.getElementById("quiz-result").innerHTML =
            `<div class="quiz-score-banner">🏆 Kết quả: ${correct}/${quiz.length} đúng — ${score}%</div>`;

        // Lưu tiến độ vào localStorage (database phía người dùng)
        const prog = getCourseProgress();
        prog.completed_days = prog.completed_days || [];
        if (!prog.completed_days.includes(lesson.day)) prog.completed_days.push(lesson.day);
        prog.quiz_scores = prog.quiz_scores || {};
        const old = prog.quiz_scores[String(lesson.day)];
        if (!old || score > old.score) {
            prog.quiz_scores[String(lesson.day)] = { score: score, at: new Date().toISOString() };
        }
        saveCourseProgress(prog);

        const badge = parseInt(progressBadge.textContent.replace(/\D/g, "").split(/\D+/)[1] || "0", 10);
        const totalDays = (courseData.days || []).length;
        progressBadge.textContent = `Hoàn thành ${prog.completed_days.length}/${totalDays} ngày`;
        void badge;
        daySelect.querySelectorAll("option").forEach(op => {
            if (parseInt(op.value, 10) === lesson.day && !op.textContent.includes("✅")) {
                op.textContent += " ✅";
            }
        });
    });
}

// Init
init();

// ─── Writing Practice — Pixel Similarity Scoring ─────────────────────────────
const btnPracticeWrite = document.getElementById("btn-practice-write");
const writingModal    = document.getElementById("writing-modal");
const closeWritingBtn = document.getElementById("close-writing-modal");
const modeSelection   = document.getElementById("writing-mode-selection");
const practiceCont    = document.getElementById("canvas-practice-container");

const btnModeHanzi  = document.getElementById("btn-mode-hanzi");   // Có chấm điểm
const btnModeCanvas = document.getElementById("btn-mode-canvas");   // Bảng nháp

const refCanvas  = document.getElementById("ref-canvas");
const bgCanvas   = document.getElementById("bg-canvas");
const drawCanvas = document.getElementById("draw-canvas");

const refCtx  = refCanvas.getContext("2d", { willReadFrequently: true });
const bgCtx   = bgCanvas.getContext("2d");
const drawCtx = drawCanvas.getContext("2d", { willReadFrequently: true });

const PW = 280, PH = 280;  // practice canvas size

let practiceChars  = [];
let practiceIndex  = 0;
let practiceMode   = "scored";   // "scored" | "free"
let isPracticing   = false;
let pLastX = 0, pLastY = 0;

// ── Open modal ──────────────────────────────────────────────────────────────
if (btnPracticeWrite) {
    btnPracticeWrite.addEventListener("click", (e) => {
        e.stopPropagation();
        if (filteredVocabs.length === 0) return;
        writingModal.style.display = "flex";
        modeSelection.style.display = "flex";
        practiceCont.style.display  = "none";
    });
}

closeWritingBtn.addEventListener("click", () => {
    writingModal.style.display = "none";
});

// ── Start practice ──────────────────────────────────────────────────────────
btnModeHanzi.addEventListener("click",  () => startPractice("scored"));
btnModeCanvas.addEventListener("click", () => startPractice("free"));

function startPractice(mode) {
    practiceMode  = mode;
    const word    = fcWord.textContent;
    practiceChars = word.replace(/\s+/g, "").split("").filter(c => c.trim() !== "");
    practiceIndex = 0;
    if (practiceChars.length === 0) return;

    modeSelection.style.display  = "none";
    practiceCont.style.display   = "block";

    document.getElementById("btn-score-check").style.display =
        mode === "scored" ? "inline-block" : "none";

    document.getElementById("practice-hint").textContent =
        mode === "scored"
            ? "Vẽ đè lên chữ mờ → nhấn ⭐ Chấm điểm khi xong."
            : "Bảng nháp tự do — vẽ theo chữ mờ phía dưới.";

    document.getElementById("score-display").style.display = "none";
    renderPracticeChar();
}

// ── Render a character ──────────────────────────────────────────────────────
function renderPracticeChar() {
    const char = practiceChars[practiceIndex];
    document.getElementById("char-indicator").textContent =
        `${practiceIndex + 1} / ${practiceChars.length}`;
    document.getElementById("score-display").style.display = "none";

    // 1. Draw crisp black char on offscreen ref-canvas (with shadow for tolerance)
    refCtx.clearRect(0, 0, PW, PH);
    refCtx.fillStyle = "white";
    refCtx.fillRect(0, 0, PW, PH);
    refCtx.save();
    refCtx.fillStyle   = "black";
    refCtx.shadowColor = "black";
    refCtx.shadowBlur  = 6;          // Creates wider "hit zone" for scoring
    const fontSize = Math.floor(PW * 0.72);
    refCtx.font          = `normal ${fontSize}px "Noto Sans", "MS Gothic", "Meiryo", "Arial Unicode MS", sans-serif`;
    refCtx.textAlign     = "center";
    refCtx.textBaseline  = "middle";
    refCtx.fillText(char, PW / 2, PH / 2);
    refCtx.restore();

    // 2. Draw faint char on bg-canvas (user sees this as a guide)
    bgCtx.clearRect(0, 0, PW, PH);
    bgCtx.fillStyle = "white";
    bgCtx.fillRect(0, 0, PW, PH);
    bgCtx.globalAlpha = 0.10;
    bgCtx.drawImage(refCanvas, 0, 0);
    bgCtx.globalAlpha = 1.0;

    // 3. Clear draw-canvas
    drawCtx.clearRect(0, 0, PW, PH);
}

// ── Score calculation (F1 = 2·precision·recall / (precision+recall)) ────────
function calcScore() {
    const refData  = refCtx.getImageData(0, 0, PW, PH).data;
    const drawData = drawCtx.getImageData(0, 0, PW, PH).data;

    let refPx = 0, userPx = 0, overlap = 0;

    for (let i = 0; i < PW * PH; i++) {
        const idx = i * 4;
        // Reference: pixel is "dark" (char stroke)
        const isRef  = (refData[idx] + refData[idx+1] + refData[idx+2]) < 450;
        // User: any drawn pixel (non-transparent)
        const isUser = drawData[idx + 3] > 30;

        if (isRef)           refPx++;
        if (isUser)          userPx++;
        if (isRef && isUser) overlap++;
    }

    if (refPx === 0 || userPx === 0) return 0;

    const recall    = overlap / refPx;
    const precision = overlap / userPx;
    if (recall + precision === 0) return 0;

    return Math.round((2 * recall * precision) / (recall + precision) * 100);
}

document.getElementById("btn-score-check").addEventListener("click", () => {
    const score = calcScore();
    const scoreDisplay = document.getElementById("score-display");
    document.getElementById("score-value").textContent = score + "%";

    let msg   = "", color = "";
    if      (score >= 85) { msg = "🌟 Xuất sắc! Chữ rất chuẩn!";          color = "#03dac6"; }
    else if (score >= 70) { msg = "✅ Tốt! Cần luyện thêm một chút.";       color = "#bb86fc"; }
    else if (score >= 50) { msg = "👍 Khá ổn! Hãy thử lại lần nữa.";       color = "#ffb300"; }
    else                  { msg = "💪 Cần luyện tập thêm! Thử lại nhé.";    color = "#cf6679"; }

    document.getElementById("score-msg").textContent = msg;
    document.querySelector(".score-ring").style.borderColor = color;
    document.getElementById("score-value").style.color      = color;
    scoreDisplay.style.display = "block";
});

// ── Navigation ───────────────────────────────────────────────────────────────
document.getElementById("btn-char-prev").addEventListener("click", () => {
    if (practiceIndex > 0) { practiceIndex--; renderPracticeChar(); }
});
document.getElementById("btn-char-next").addEventListener("click", () => {
    if (practiceIndex < practiceChars.length - 1) { practiceIndex++; renderPracticeChar(); }
});
document.getElementById("btn-clear-draw").addEventListener("click", () => {
    drawCtx.clearRect(0, 0, PW, PH);
    document.getElementById("score-display").style.display = "none";
});

// ── Drawing input ────────────────────────────────────────────────────────────
function getPracticePos(e) {
    const rect   = drawCanvas.getBoundingClientRect();
    const scaleX = PW / rect.width;
    const scaleY = PH / rect.height;
    const src    = e.touches ? e.touches[0] : e;
    return {
        x: (src.clientX - rect.left) * scaleX,
        y: (src.clientY - rect.top)  * scaleY
    };
}

function practiceStroke(x, y) {
    drawCtx.beginPath();
    drawCtx.moveTo(pLastX, pLastY);
    drawCtx.lineTo(x, y);
    drawCtx.strokeStyle = "#1a1a2e";
    drawCtx.lineWidth   = 20;
    drawCtx.lineCap     = "round";
    drawCtx.lineJoin    = "round";
    drawCtx.stroke();
    pLastX = x; pLastY = y;
}

drawCanvas.addEventListener("mousedown", (e) => {
    isPracticing = true;
    const p = getPracticePos(e); pLastX = p.x; pLastY = p.y;
});
drawCanvas.addEventListener("mousemove", (e) => {
    if (!isPracticing) return;
    const p = getPracticePos(e); practiceStroke(p.x, p.y);
});
drawCanvas.addEventListener("mouseup",  () => { isPracticing = false; });
drawCanvas.addEventListener("mouseout", () => { isPracticing = false; });

drawCanvas.addEventListener("touchstart", (e) => {
    e.preventDefault(); isPracticing = true;
    const p = getPracticePos(e); pLastX = p.x; pLastY = p.y;
}, { passive: false });
drawCanvas.addEventListener("touchmove", (e) => {
    e.preventDefault(); if (!isPracticing) return;
    const p = getPracticePos(e); practiceStroke(p.x, p.y);
}, { passive: false });
drawCanvas.addEventListener("touchend", () => { isPracticing = false; });

// ════════════════════════════════════════════════════════════════════════════
// ÔN TẬP SM-2 (Gói 3 — 2026-11-12)
// Trước đây web KHÔNG có bất kỳ API ghi tiến độ học nào ⇒ "học từ online"
// không đóng được vòng lặp (tiến độ chỉ nằm trong localStorage của trình
// duyệt, app desktop không thấy). Nay dùng chung engine SM-2 sẵn có
// (ai/srs.py + database/review_store.py) qua API, và GHI CHUNG file
// data/reviews/<slug>.json với app desktop.
// ════════════════════════════════════════════════════════════════════════════
const srsState = { items: [], idx: 0, revealed: false, stats: null };

// ════════════════════════════════════════════════════════════════════════════
// SRS CỤC BỘ cho bản ONLINE (Gói 10): tiến độ nằm trong localStorage.
// Thuật toán SM-2 rút gọn: again 10 phút · hard ×1.2 · good ×2.5 · easy ×3.2
// ════════════════════════════════════════════════════════════════════════════
function _srsKey(slug) { return "vocab_srs_v1_" + slug; }

function _srsLoad(slug) {
    try {
        const raw = localStorage.getItem(_srsKey(slug));
        const d = raw ? JSON.parse(raw) : null;
        if (d && typeof d === "object") {
            d.cards = d.cards || {};
            d.days = d.days || {};
            return d;
        }
    } catch (e) { }
    return { cards: {}, days: {} };
}

function _srsSave(slug, data) {
    try { localStorage.setItem(_srsKey(slug), JSON.stringify(data)); } catch (e) { }
}

function _todayKey() {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function _dayOfVocab(v) {
    const m = /(\d+)/.exec(String(v.date_tag || ""));
    return m ? Number(m[1]) : 0;
}

function _srsItemFromVocab(v) {
    return {
        word: v.word || "",
        pronunciation: v.reading || "",
        meaning_vi: v.meaning || "",
        example_sentence: v.example || "",
        example_meaning_vi: "",
        image_ref: v.image_ref || "",
        audio_ref: v.audio_ref || "",
        meaning_audio_ref: "",
        day: _dayOfVocab(v),
    };
}

/** Hàng đợi ôn tập cục bộ: thẻ đến hạn trước, sau đó thẻ mới. */
function localSrsQueue(slug, limit = 20) {
    const data = _srsLoad(slug);
    const now = Date.now();
    const due = [];
    const fresh = [];
    for (const v of (vocabularies || [])) {
        if (!v || !v.word) continue;
        const c = data.cards[v.word];
        if (!c) { fresh.push(v); continue; }
        if ((c.due || 0) <= now) due.push(v);
    }
    due.sort((a, b) => (data.cards[a.word].due || 0) - (data.cards[b.word].due || 0));
    const items = due.concat(fresh).slice(0, limit).map(_srsItemFromVocab);
    return { items, stats: localSrsStats(slug) };
}

function localSrsStats(slug) {
    const data = _srsLoad(slug);
    const now = Date.now();
    const cards = Object.values(data.cards || {});
    const due = cards.filter(c => (c.due || 0) <= now).length;
    const mastered = cards.filter(c => (c.interval || 0) >= 21).length;
    // streak: số ngày liên tiếp có ôn (tính từ hôm nay/lùi về)
    let streak = 0;
    const d = new Date();
    for (;;) {
        const k = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
        if (data.days[k]) { streak += 1; d.setDate(d.getDate() - 1); }
        else break;
    }
    return { total: cards.length, mastered, due, streak };
}

/** Chấm điểm 1 thẻ (localStorage) → { next_review_in_days }. */
function localSrsGrade(slug, word, grade) {
    const data = _srsLoad(slug);
    const now = Date.now();
    const c = data.cards[word] || { ef: 2.5, interval: 0, reps: 0, lapses: 0, due: now };
    const g = String(grade || "good");
    if (g === "again") {
        c.ef = Math.max(1.3, (c.ef || 2.5) - 0.2);
        c.interval = 10 / (24 * 60);      // 10 phút
        c.lapses = (c.lapses || 0) + 1;
    } else if (g === "hard") {
        c.interval = Math.max(1, (c.interval || 0) * 1.2);
    } else if (g === "easy") {
        c.interval = Math.max(3, (c.interval || 0) * 3.2);
    } else {
        c.interval = (c.interval || 0) < 1 ? 1 : c.interval * 2.5;
    }
    c.reps = (c.reps || 0) + 1;
    c.due = now + c.interval * 24 * 60 * 60 * 1000;
    c.last = now;
    data.cards[word] = c;
    const tk = _todayKey();
    data.days[tk] = (data.days[tk] || 0) + 1;
    _srsSave(slug, data);
    return { next_review_in_days: c.interval };
}

/** Nạp media_map + gói media của 1 ngày (dùng cho thẻ ôn tập ở bản online). */
async function _staticPreloadSrsMedia(it) {
    if (_cfgMode() !== "static" || !it || !it.day) return false;
    const slug = slugOf(currentLanguage);
    const day = Number(it.day);
    if (!slug || !day) return false;
    if (!courseDayCache[day]) {
        try {
            const base = `${VOCAB_DATA_CFG.dataBase}/${encodeURIComponent(slug)}`;
            const r = await fetch(`${base}/day/${String(day).padStart(4, "0")}.json`);
            if (r.ok) courseDayCache[day] = await r.json();
        } catch (e) { }
    }
    const j = courseDayCache[day];
    if (j && j.media_map) Object.assign(staticMediaMap, j.media_map);
    try { await ensureMediaBundle(slug, _monthKeyOf(day)); } catch (e) { }
    return true;
}

async function loadSrsQueue() {
    const slug = slugOf(currentLanguage);
    const card = document.getElementById("srs-card");
    const actions = document.getElementById("srs-actions");
    const fb = document.getElementById("srs-feedback");
    if (!slug) {
        card.innerHTML = '<p class="srs-hint">Chọn khóa học trước khi ôn tập.</p>';
        actions.hidden = true;
        return;
    }
    card.innerHTML = '<p class="srs-hint">⏳ Đang tải hàng đợi ôn tập…</p>';
    // BẢN ONLINE: hàng đợi + tiến độ nằm trong localStorage (không cần server)
    if (_cfgMode() === "static") {
        try {
            const q = localSrsQueue(slug, 20);
            srsState.items = q.items;
            srsState.stats = q.stats;
            srsState.idx = 0;
            srsState.revealed = false;
            renderSrsStats();
            renderSrsCard();
            if (q.items[0]) {
                _staticPreloadSrsMedia(q.items[0]).then((ok) => { if (ok) renderSrsCard(); });
            }
        } catch (e) {
            card.innerHTML = '<p class="srs-hint">⚠ Không đọc được tiến độ ôn tập trên máy.</p>';
        }
        return;
    }
    try {
        const r = await fetch(`api/vocab/srs/queue?lang=${encodeURIComponent(slug)}&limit=20`);
        if (!r.ok) throw new Error("HTTP " + r.status);
        const j = await r.json();
        srsState.items = j.items || [];
        srsState.stats = j.stats || null;
        srsState.idx = 0;
        srsState.revealed = false;
        renderSrsStats();
        renderSrsCard();
    } catch (e) {
        card.innerHTML = '<p class="srs-hint">⚠ Không tải được hàng đợi ôn tập. '
            + 'Cần khóa học AI có sẵn trên máy (mở app VocabApp → sinh khóa học).</p>';
        actions.hidden = true;
        if (fb) fb.textContent = "";
    }
}

function renderSrsStats() {
    const box = document.getElementById("srs-stats");
    if (!box) return;
    const s = srsState.stats || {};
    const total = s.total ?? 0;
    const mastered = s.mastered ?? 0;
    const due = s.due ?? s.due_today ?? 0;
    const streak = s.streak ?? 0;
    box.innerHTML = `
        <span class="srs-stat"><b>${escapeHtml(String(due))}</b> đến hạn</span>
        <span class="srs-stat"><b>${escapeHtml(String(mastered))}</b>/${escapeHtml(String(total))} đã thuộc</span>
        <span class="srs-stat">🔥 ${escapeHtml(String(streak))} ngày liền</span>`;
}

function renderSrsCard() {
    const card = document.getElementById("srs-card");
    const actions = document.getElementById("srs-actions");
    const fb = document.getElementById("srs-feedback");
    if (!card) return;
    const it = srsState.items[srsState.idx];
    if (!it) {
        card.innerHTML = '<p class="srs-hint">🎉 Hết hàng đợi! Hôm nay đã ôn xong.</p>';
        if (actions) actions.hidden = true;
        if (fb) fb.textContent = "";
        return;
    }
    if (actions) actions.hidden = false;
    const audio = mediaAudioHtml(it.audio_ref);
    if (!srsState.revealed) {
        card.innerHTML = `
            <div class="srs-word">${escapeHtml(it.word)}</div>
            <div class="srs-pron">${it.pronunciation ? "/" + escapeHtml(it.pronunciation) + "/" : ""}</div>
            ${audio}
            <button class="srs-reveal" id="srs-reveal">👀 Xem nghĩa</button>`;
        const rv = document.getElementById("srs-reveal");
        if (rv) rv.addEventListener("click", () => {
            srsState.revealed = true;
            renderSrsCard();
        });
        // KHÔNG xoá feedback ở đây (Gói 3 fix): sau khi chấm điểm, thông báo
        // "ôn lại sau N ngày" phải còn lại cho tới lần chấm kế tiếp.
    } else {
        const meanAudio = it.meaning_audio_ref ? mediaAudioHtml(it.meaning_audio_ref) : "";
        card.innerHTML = `
            <div class="srs-word">${escapeHtml(it.word)}</div>
            <div class="srs-pron">${it.pronunciation ? "/" + escapeHtml(it.pronunciation) + "/" : ""}</div>
            <div class="srs-meaning">${escapeHtml(it.meaning_vi || "")}</div>
            ${it.example_sentence ? `<div class="srs-example">${formatText(it.example_sentence)}
                <div class="muted">${escapeHtml(it.example_meaning_vi || "")}</div></div>` : ""}
            ${mediaImgHtml(it.image_ref, it.word)}
            ${audio}${meanAudio}
            <div class="srs-day">📚 Ngày ${escapeHtml(String(it.day ?? ""))}</div>`;
    }
}

async function srsGrade(grade) {
    const it = srsState.items[srsState.idx];
    const fb = document.getElementById("srs-feedback");
    if (!it) return;
    // BẢN ONLINE: lưu vào localStorage, không gọi server.
    if (_cfgMode() === "static") {
        try {
            const info = localSrsGrade(slugOf(currentLanguage), it.word, grade);
            const d = info.next_review_in_days;
            const when = (d == null) ? "?" :
                (d < 1 ? Math.round(d * 24 * 60) + " phút" : Math.round(d) + " ngày");
            if (fb) fb.textContent = `✅ Đã lưu — ôn lại sau ${when}.`;
        } catch (e) {
            if (fb) fb.textContent = "⚠ Không lưu được kết quả ôn tập.";
        }
        srsState.idx += 1;
        srsState.revealed = false;
        srsState.stats = localSrsStats(slugOf(currentLanguage));
        renderSrsStats();
        renderSrsCard();
        const nx = srsState.items[srsState.idx];
        if (nx) _staticPreloadSrsMedia(nx).then((ok) => { if (ok) renderSrsCard(); });
        return;
    }
    try {
        const r = await fetch("api/vocab/srs/review", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                lang: slugOf(currentLanguage),
                word: it.word,
                grade: grade,
                correct: grade !== "again",
            }),
        });
        const j = await r.json().catch(() => ({}));
        if (j && j.ok && j.info) {
            const d = j.info.next_review_in_days;
            const when = (d == null) ? "?" :
                (d < 1 ? Math.round(d * 24 * 60) + " phút" : Math.round(d) + " ngày");
            if (fb) fb.textContent = `✅ Đã lưu — ôn lại sau ${when}.`;
        } else {
            if (fb) fb.textContent = "⚠ Không lưu được kết quả ôn tập.";
        }
    } catch (e) {
        if (fb) fb.textContent = "⚠ Lỗi mạng khi lưu kết quả ôn tập.";
    }
    srsState.idx += 1;
    srsState.revealed = false;
    try {
        const r2 = await fetch(`api/vocab/srs/stats?lang=${encodeURIComponent(slugOf(currentLanguage))}`);
        const j2 = await r2.json();
        if (j2 && j2.stats) srsState.stats = j2.stats;
    } catch (e) { /* giữ stats cũ */ }
    renderSrsStats();
    renderSrsCard();
}

document.querySelectorAll(".srs-btn").forEach(b => {
    b.addEventListener("click", () => srsGrade(b.dataset.grade));
});

// Phím tắt 1-4 để chấm điểm nhanh (chỉ khi đang ở tab Ôn tập)
document.addEventListener("keydown", (e) => {
    if (!viewReview || !viewReview.classList.contains("active")) return;
    if (e.target && ["INPUT", "TEXTAREA", "SELECT"].includes(e.target.tagName)) return;
    const map = { "1": "again", "2": "hard", "3": "good", "4": "easy" };
    const g = map[e.key];
    if (!g) return;
    if (!srsState.revealed && e.key !== "1") return;   // lộ nghĩa trước
    srsGrade(g);
});
