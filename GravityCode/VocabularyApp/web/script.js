let currentLanguage = "";
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

async function ensureCourseLoaded() {
    const slug = slugOf(currentLanguage);
    if (courseData && courseSlug === slug) { renderCourseShell(); return; }
    courseSlug = slug;
    courseData = null;
    courseIndex = null;
    courseDayCache = {};

    // 1) API nhẹ: index + tải từng ngày
    try {
        const r = await fetch(`api/vocab/course/${encodeURIComponent(slug)}/index`);
        if (r.ok) {
            const j = await r.json();
            if (j && j.ok && Array.isArray(j.days) && j.days.length) {
                courseIndex = j.days;
                courseData = { days: j.days, level: j.level || "" };
                await loadMediaIndex();
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
    // Nạp manifest media (ảnh + audio) — LAZY, chỉ khi khóa học có dữ liệu v4
    await loadMediaIndex();
    renderCourseShell();
}

// ─── Manifest media (ảnh minh họa + âm thanh) ───────────────────────────────
let mediaIndex = null;
let mediaIndexPromise = null;

async function loadMediaIndex() {
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

async function renderCourseDay(dayNum) {
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
    if (!lesson) return;
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
            html += `<div class="grammar-box">
                <h4>Bài ${gi + 1}: ${escapeHtml(g.title || "")}</h4>
                <div>${formatText(g.explanation || "")}</div>
                ${(g.examples || []).map(ex => `
                    <div style="margin-top:8px;">💬 ${formatText(ex.sentence || "")}
                        ${ex.meaning_vi ? `<div class="vocab-example-meaning">${formatText(ex.meaning_vi)}</div>` : ""}
                    </div>`).join("")}
                ${g.pronunciation_focus ? `<div class="phonetic-note">👄 ${escapeHtml(g.pronunciation_focus)}</div>` : ""}
                ${(g.common_mistakes || []).map(m => `
                    <div class="mistake-box">
                        <div class="mistake-wrong">❌ ${escapeHtml(m.wrong || "")}</div>
                        <div class="mistake-right">✅ ${escapeHtml(m.right || "")}</div>
                        ${m.why_vi ? `<div class="vocab-example-meaning">${escapeHtml(m.why_vi)}</div>` : ""}
                    </div>`).join("")}
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
                ${q.options.map((opt, oi) =>
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
