// content_script.js — MBC Stamp Fixer (Tiếp cận 4: Scale-to-Template)
console.log("[MBC Intramart Signal] Content script loaded.");

if (window === window.top) {
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initToolbar);
    } else {
        initToolbar();
    }
}

// ─────────────────────────────────────────
// TOOLBAR
// ─────────────────────────────────────────
function initToolbar() {
    if (document.getElementById('mbc-intramart-toolbar')) return;
    const toolbar = document.createElement("div");
    toolbar.id = "mbc-intramart-toolbar";
    toolbar.innerHTML = `
        <div class="mbc-toolbar-header">🛠️ MBC Stamp Fixer</div>
        <p class="mbc-toolbar-sub">Phân tích margin + chỉnh dấu</p>
        <button id="mbc-btn-scale-pdf">📌 Chỉnh dấu theo File Mẫu</button>
    `;
    document.body.appendChild(toolbar);
    document.getElementById("mbc-btn-scale-pdf").addEventListener("click", openScaleModal);
}

// ─────────────────────────────────────────
// HÀM HỖ TRỢ
// ─────────────────────────────────────────
function readFileAsArrayBuffer(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsArrayBuffer(file);
    });
}

function getAllFramesFrom(win) {
    const list = [];
    function collect(w) {
        if (!w) return;
        list.push(w);
        try {
            for (let i = 0; i < w.frames.length; i++) collect(w.frames[i]);
        } catch(e) {}
    }
    collect(win);
    return list;
}

// Tìm file input và cửa sổ chứa nó (có thể nằm ở opener nếu đây là popup)
function getFileInput() {
    let input = document.getElementById("edtDocFileId");
    if (input) return { input, win: window };
    if (window.opener) {
        try {
            input = window.opener.document.getElementById("edtDocFileId");
            if (input) return { input, win: window.opener };
            for (let f of getAllFramesFrom(window.opener)) {
                try {
                    input = f.document.getElementById("edtDocFileId");
                    if (input) return { input, win: f };
                } catch(e) {}
            }
        } catch(e) {}
    }
    return null;
}

// Thử tìm URL tải file mẫu từ trang hiện tại
function detectTemplateUrl() {
    // Tìm docCode từ hidden input
    const docCodeInput = document.getElementById("hedtDocCode")
        || document.querySelector('input[name="hedtDocCode"]');
    if (docCodeInput && docCodeInput.value) {
        const docCode = docCodeInput.value;
        return `/imart/EDPServlet?action=5&iDocCode=${encodeURIComponent(docCode)}`;
    }
    // Thử tìm link tải mẫu trực tiếp
    const dlSpan = document.getElementById("spDocDownload");
    if (dlSpan) {
        const link = dlSpan.querySelector("a[href]");
        if (link) return link.href;
        const onclick = dlSpan.getAttribute("onclick") || "";
        const match = onclick.match(/['"]([^'"]+\.pdf[^'"]*)['"]/);
        if (match) return match[1];
    }
    return null;
}

// ─────────────────────────────────────────
// MỞ MODAL
// ─────────────────────────────────────────
function openScaleModal() {
    if (document.getElementById("mbc-scale-modal")) return;

    const modal = document.createElement("div");
    modal.id = "mbc-scale-modal";
    modal.style.cssText = `
        position:fixed;top:0;left:0;width:100%;height:100%;
        background:rgba(0,0,0,0.75);z-index:999999;
        display:flex;align-items:center;justify-content:center;
    `;

    const templateUrl = detectTemplateUrl();
    const autoDetectHtml = templateUrl
        ? `<p class="mbc-hint">✅ Đã tự phát hiện URL file mẫu từ trang.</p>`
        : `<p class="mbc-hint" style="color:#e74c3c">⚠️ Không tự phát hiện được file mẫu. Vui lòng tải về và chọn thủ công bên dưới.</p>`;

    modal.innerHTML = `
        <div class="mbc-modal-box">
            <h3 class="mbc-modal-title">⚖️ Chỉnh Dấu Theo File Mẫu</h3>
            
            <div class="mbc-step">
                <div class="mbc-step-num">1</div>
                <div class="mbc-step-body">
                    <b>File mẫu (Template)</b> — file mà Server đóng dấu đúng chỗ
                    ${autoDetectHtml}
                    <label class="mbc-file-label">
                        Chọn file mẫu (.pdf):
                        <input type="file" id="mbc-input-template" accept=".pdf">
                    </label>
                </div>
            </div>

            <div class="mbc-step">
                <div class="mbc-step-num">2</div>
                <div class="mbc-step-body">
                    <b>File bạn đang làm</b> — đã upload lên ô văn bản chính
                    <div id="mbc-user-file-info" class="mbc-hint">Đang kiểm tra...</div>
                </div>
            </div>

            <div id="mbc-size-preview" style="display:none;" class="mbc-size-box">
                <div id="mbc-size-template"></div>
                <div id="mbc-size-user"></div>
                <div id="mbc-size-diff"></div>
            </div>

            <div id="mbc-excel-guide" style="display:none;" class="mbc-hint" style="background:#e8f8f5; border:1px solid #1abc9c; padding:8px; border-radius:6px; margin-top:8px;">
                <b style="color:#16a085;">📊 Hướng dẫn sửa File Excel gốc (để lần sau xuất PDF chuẩn luôn):</b>
                <ul id="mbc-excel-guide-list" style="margin:4px 0 0 16px; padding:0; color:#2c3e50; font-size:12px;"></ul>
            </div>

            <div id="mbc-scale-status" class="mbc-hint" style="color:#27ae60;margin-top:8px;"></div>

            <div class="mbc-option-row">
                <label style="display:flex;align-items:center;gap:8px;font-size:12px;cursor:pointer;margin-bottom:6px;">
                    <input type="checkbox" id="mbc-chk-remove-header" checked style="width:15px;height:15px;">
                    <span>🧹 Tự động xóa dòng đường dẫn file (Header/Footer Excel)</span>
                </label>
                <label style="display:flex;align-items:center;gap:8px;font-size:12px;margin-bottom:6px;">
                    <span>🔎 Từ khóa căn dấu:</span>
                    <input type="text" id="mbc-input-keywords" value="Phụ trách, Creator, Xác nhận, Manager" style="flex:1; padding:4px; font-size:12px; border:1px solid #ccc; border-radius:4px;">
                </label>
                <div style="font-size:10px; color:#7f8c8d; margin-bottom:8px;">(Addon sẽ tìm chữ này để căn khung chữ ký khớp 100%. Cách nhau bằng dấu phẩy)</div>
                <div style="display:flex; gap:12px; font-size:12px;">
                    <label style="display:flex;align-items:center;gap:4px;">
                        Tinh chỉnh X (pts):
                        <input type="number" id="mbc-input-custom-x" value="0" style="width:60px; padding:4px; border:1px solid #ccc; border-radius:4px;">
                    </label>
                    <label style="display:flex;align-items:center;gap:4px;">
                        Tinh chỉnh Y (pts):
                        <input type="number" id="mbc-input-custom-y" value="0" style="width:60px; padding:4px; border:1px solid #ccc; border-radius:4px;">
                    </label>
                </div>
            </div>

            <div class="mbc-modal-footer">
                <button id="mbc-btn-test-scale" class="mbc-btn-secondary" style="margin-right:8px; border-color:#2980b9; color:#2980b9;" disabled>👀 Xem thử PDF</button>
                <button id="mbc-btn-do-scale" class="mbc-btn-primary" disabled>⚖️ Áp dụng & Upload</button>
                <button id="mbc-btn-cancel-scale" class="mbc-btn-secondary" style="margin-left:auto;">Hủy</button>
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    // Kiểm tra file của user
    const fileInfo = getFileInput();
    const userInfoEl = document.getElementById("mbc-user-file-info");
    if (fileInfo && fileInfo.input.files && fileInfo.input.files.length > 0) {
        const f = fileInfo.input.files[0];
        userInfoEl.innerHTML = `✅ Đã tìm thấy: <b>${f.name}</b> (${(f.size/1024).toFixed(1)} KB)`;
        userInfoEl.style.color = "#27ae60";
    } else {
        userInfoEl.innerHTML = `❌ Chưa có file! Hãy upload file văn bản chính trước.`;
        userInfoEl.style.color = "#e74c3c";
    }

    // Xử lý chọn file mẫu
    document.getElementById("mbc-input-template").addEventListener("change", async (e) => {
        const tplFile = e.target.files[0];
        if (!tplFile) return;
        await previewSizes(tplFile, fileInfo);
    });

    document.getElementById("mbc-btn-test-scale").addEventListener("click", () => doScale(fileInfo, true));
    document.getElementById("mbc-btn-do-scale").addEventListener("click", () => doScale(fileInfo, false));
    document.getElementById("mbc-btn-cancel-scale").addEventListener("click", closeScaleModal);
}

// ─────────────────────────────────────────
// PHÂN TÍCH MARGIN THỰC TẾ BẰNG PIXEL SCAN
// ─────────────────────────────────────────
async function analyzeContentMargins(pdfBytes) {
    if (!window.pdfjsLib.GlobalWorkerOptions.workerSrc) {
        window.pdfjsLib.GlobalWorkerOptions.workerSrc = chrome.runtime.getURL('libs/pdf.worker.min.js');
    }
    const SCAN_SCALE = 1.0;
    // Dùng slice(0) để copy ArrayBuffer, tránh lỗi "detached ArrayBuffer" khi dùng lại
    const loadingTask = window.pdfjsLib.getDocument({ data: pdfBytes.slice(0) });
    const pdf = await loadingTask.promise;
    const page = await pdf.getPage(1);
    const viewport = page.getViewport({ scale: SCAN_SCALE });

    const canvas = document.createElement('canvas');
    canvas.width  = Math.round(viewport.width);
    canvas.height = Math.round(viewport.height);
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = 'white';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    await page.render({ canvasContext: ctx, viewport }).promise;

    const imgData = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
    const W = canvas.width, H = canvas.height;

    // Pixel có "nội dung" nếu tối hơn ngưỡng (không phải trắng)
    const THRESHOLD = 230;
    const hasContent = (x, y) => {
        const i = (y * W + x) * 4;
        return imgData[i] < THRESHOLD || imgData[i+1] < THRESHOLD || imgData[i+2] < THRESHOLD;
    };

    let top = H, bottom = H, left = W, right = W;

    // Quét từ trên xuống → top margin (bỏ qua 5px đầu để tránh artifact render)
    scan_top: for (let y = 5; y < H; y++)
        for (let x = 5; x < W - 5; x++)
            if (hasContent(x, y)) { top = y; break scan_top; }

    // Quét từ dưới lên → bottom margin
    scan_bot: for (let y = H - 6; y >= 0; y--)
        for (let x = 5; x < W - 5; x++)
            if (hasContent(x, y)) { bottom = H - y - 1; break scan_bot; }

    // Quét từ trái → left margin
    scan_left: for (let x = 5; x < W; x++)
        for (let y = 5; y < H - 5; y++)
            if (hasContent(x, y)) { left = x; break scan_left; }

    // Quét từ phải → right margin
    scan_right: for (let x = W - 6; x >= 0; x--)
        for (let y = 5; y < H - 5; y++)
            if (hasContent(x, y)) { right = W - x - 1; break scan_right; }

    // Chuyển từ canvas pixels → PDF points
    const ptsPerPx = 1 / SCAN_SCALE;
    return {
        top:    top    * ptsPerPx,
        bottom: bottom * ptsPerPx,
        left:   left   * ptsPerPx,
        right:  right  * ptsPerPx,
        pageW:  viewport.width  / SCAN_SCALE,
        pageH:  viewport.height / SCAN_SCALE,
    };
}

// ─────────────────────────────────────────
// TÌM TỌA ĐỘ TEXT (ĐỂ CĂN THEO Ô CHỮ KÝ)
// ─────────────────────────────────────────
async function findKeywordCoordinates(pdfBytes, keywords) {
    // Dùng slice(0) để copy ArrayBuffer
    const loadingTask = window.pdfjsLib.getDocument({ data: pdfBytes.slice(0) });
    const pdf = await loadingTask.promise;
    const page = await pdf.getPage(1);
    const textContent = await page.getTextContent();
    
    for (const item of textContent.items) {
        const text = item.str || "";
        for (const kw of keywords) {
            if (text.toLowerCase().includes(kw.toLowerCase())) {
                // item.transform là mảng [scaleX, skewY, skewX, scaleY, tx, ty]
                // tx, ty là tọa độ góc dưới bên trái của text
                return {
                    x: item.transform[4],
                    y: item.transform[5],
                    text: text
                };
            }
        }
    }
    return null;
}

// ─────────────────────────────────────────
// XEM TRƯỚC VÀ PHÂN TÍCH
// ─────────────────────────────────────────
async function previewSizes(templateFile, fileInfo) {
    const statusEl  = document.getElementById("mbc-scale-status");
    const previewEl = document.getElementById("mbc-size-preview");
    statusEl.innerHTML = "⏳ Đang phân tích margin PDF (quét pixel)...";
    statusEl.style.color = "#2980b9";

    try {
        const tplBytes  = await readFileAsArrayBuffer(templateFile);
        const tplMargin = await analyzeContentMargins(tplBytes);

        document.getElementById("mbc-size-template").innerHTML =
            `📄 File mẫu — margin: ` +
            `Trên <b>${tplMargin.top.toFixed(1)}</b> | ` +
            `Trái <b>${tplMargin.left.toFixed(1)}</b> | ` +
            `Phải <b>${tplMargin.right.toFixed(1)}</b> | ` +
            `Dưới <b>${tplMargin.bottom.toFixed(1)}</b> pts`;

        if (fileInfo && fileInfo.input.files && fileInfo.input.files.length > 0) {
            const userBytes  = await readFileAsArrayBuffer(fileInfo.input.files[0]);
            const userMargin = await analyzeContentMargins(userBytes);

            document.getElementById("mbc-size-user").innerHTML =
                `📄 File của bạn — margin: ` +
                `Trên <b>${userMargin.top.toFixed(1)}</b> | ` +
                `Trái <b>${userMargin.left.toFixed(1)}</b> | ` +
                `Phải <b>${userMargin.right.toFixed(1)}</b> | ` +
                `Dưới <b>${userMargin.bottom.toFixed(1)}</b> pts`;

            // Thử tìm tọa độ text chữ ký
            const rawKw = document.getElementById("mbc-input-keywords")?.value || "Phụ trách, Creator, Xác nhận";
            const signKeywords = rawKw.split(",").map(k => k.trim()).filter(k => k.length > 0);
            
            const tplTextPos = await findKeywordCoordinates(tplBytes, signKeywords);
            const userTextPos = await findKeywordCoordinates(userBytes, signKeywords);

            let deltaTop, deltaLeft, alignMethod;

            if (tplTextPos && userTextPos) {
                // Text alignment (Siêu chuẩn xác)
                // y trong PDF tính từ dưới lên, nếu userTextPos.y < tplTextPos.y 
                // -> ô chữ ký của user đang thấp hơn mẫu -> cần đẩy user lên (+)
                deltaTop  = tplTextPos.y - userTextPos.y; 
                deltaLeft = userTextPos.x - tplTextPos.x;
                alignMethod = `📍 Căn theo chữ ký ("${tplTextPos.text}")`;
            } else {
                // Fallback về Bounding Box Margin
                deltaTop  = userMargin.top  - tplMargin.top;
                deltaLeft = userMargin.left - tplMargin.left;
                alignMethod = `📏 Căn theo lề tổng thể (Bounding Box)`;
            }

            const deltaBot  = userMargin.bottom - tplMargin.bottom;
            const deltaRight = userMargin.right - tplMargin.right;

            const fmt = (v) => (v >= 0 ? `+${v.toFixed(1)}` : v.toFixed(1));
            let diffColor = (Math.abs(deltaLeft) > 1 || Math.abs(deltaTop) > 1) ? "#e67e22" : "#27ae60";

            document.getElementById("mbc-size-diff").innerHTML =
                `<b>${alignMethod}</b><br>` +
                `🔍 Cần dịch chuyển: X = <b>${fmt(-deltaLeft)}</b> pts, Y = <b>${fmt(deltaTop)}</b> pts.<br>` +
                `<span style="font-size:11px;color:#7f8c8d;">(Chi tiết lề - Trái: ${fmt(deltaLeft)}, Phải: ${fmt(deltaRight)}, Trên: ${fmt(deltaTop)}, Dưới: ${fmt(deltaBot)})</span>`;
            document.getElementById("mbc-size-diff").style.color = diffColor;

            previewEl.style.display = "block";
            document.getElementById("mbc-btn-do-scale").disabled = false;
            document.getElementById("mbc-btn-test-scale").disabled = false;
            statusEl.innerHTML = `✅ Phân tích xong! Cần dịch chuyển: X = <b>${fmt(-deltaLeft)}</b> pts, Y = <b>${fmt(deltaTop)}</b> pts.<br>Bấm 'Xem thử' hoặc 'Áp dụng & Upload' để tiến hành.`;
            statusEl.style.color = "#27ae60";

            // ─────────────────────────────────────────
            // GỢI Ý CHỈNH EXCEL
            // ─────────────────────────────────────────
            const guideEl = document.getElementById("mbc-excel-guide");
            const guideList = document.getElementById("mbc-excel-guide-list");
            guideList.innerHTML = "";
            let needsExcelChange = false;

            const ptsToCm = (pts) => (Math.abs(pts) / 72 * 2.54).toFixed(2);
            const ptsToIn = (pts) => (Math.abs(pts) / 72).toFixed(2);

            if (Math.abs(deltaTop) > 2) {
                needsExcelChange = true;
                if (deltaTop > 0) {
                    guideList.innerHTML += `<li><b>Top Margin (Lề trên):</b> Đang bị dư, hãy <span style="color:#e74c3c">GIẢM</span> bớt <b>${ptsToCm(deltaTop)} cm</b> (hoặc ${ptsToIn(deltaTop)} inch) trong Excel.</li>`;
                } else {
                    guideList.innerHTML += `<li><b>Top Margin (Lề trên):</b> Đang bị thiếu, hãy <span style="color:#27ae60">TĂNG</span> thêm <b>${ptsToCm(deltaTop)} cm</b> (hoặc ${ptsToIn(deltaTop)} inch) trong Excel.</li>`;
                }
            }

            if (Math.abs(deltaLeft) > 2) {
                needsExcelChange = true;
                if (deltaLeft > 0) {
                    guideList.innerHTML += `<li><b>Left Margin (Lề trái):</b> Đang bị dư, hãy <span style="color:#e74c3c">GIẢM</span> bớt <b>${ptsToCm(deltaLeft)} cm</b> (hoặc ${ptsToIn(deltaLeft)} inch) trong Excel.</li>`;
                } else {
                    guideList.innerHTML += `<li><b>Left Margin (Lề trái):</b> Đang bị thiếu, hãy <span style="color:#27ae60">TĂNG</span> thêm <b>${ptsToCm(deltaLeft)} cm</b> (hoặc ${ptsToIn(deltaLeft)} inch) trong Excel.</li>`;
                }
            }

            const scaleRatio = (userMargin.pageW / tplMargin.pageW);
            if (Math.abs(scaleRatio - 1) > 0.05) {
                needsExcelChange = true;
                guideList.innerHTML += `<li><b>Scaling (Tỷ lệ thu phóng):</b> Kích thước giấy của bạn đang ${scaleRatio > 1 ? 'lớn' : 'nhỏ'} hơn file mẫu ${(Math.abs(scaleRatio - 1)*100).toFixed(0)}%. Hãy kiểm tra lại cài đặt <b>"Fit to 1 page"</b> trong Excel.</li>`;
            }

            if (needsExcelChange) {
                guideEl.style.display = "block";
            } else {
                guideEl.style.display = "none";
            }

            // Lưu dữ liệu để dùng khi Apply
            window._mbcTplBytes  = tplBytes;
            window._mbcTplSize   = { width: tplMargin.pageW, height: tplMargin.pageH };
            window._mbcDeltaX    = -deltaLeft;  // Shift phải nếu user lùi trái hơn
            window._mbcDeltaY    = deltaTop;     // Shift lên nếu user có top margin lớn hơn
            window._mbcTplTextPos = tplTextPos; // Lưu để vẽ khung mô phỏng lúc Test
        }
    } catch(e) {
        statusEl.innerText = "❌ Lỗi phân tích: " + e.message;
        statusEl.style.color = "#e74c3c";
    }
}

// ─────────────────────────────────────────
// ÁP DỤNG TRANSLATION VÀ UPLOAD
// ─────────────────────────────────────────
async function doScale(fileInfo, isPreview = false) {
    const statusEl = document.getElementById("mbc-scale-status");
    const btnScale = document.getElementById("mbc-btn-do-scale");
    const btnTest  = document.getElementById("mbc-btn-test-scale");
    
    btnScale.disabled = true;
    btnTest.disabled = true;
    statusEl.innerText = isPreview ? "⏳ Đang tạo bản xem thử..." : "⏳ Đang dịch chuyển nội dung PDF...";
    statusEl.style.color = "#2980b9";

    try {
        const { PDFDocument, rgb } = window.PDFLib;
        const tplSize  = window._mbcTplSize;
        
        // Đọc giá trị custom bù trừ (pts)
        const customX = parseFloat(document.getElementById("mbc-input-custom-x")?.value) || 0;
        const customY = parseFloat(document.getElementById("mbc-input-custom-y")?.value) || 0;

        const deltaX   = (window._mbcDeltaX || 0) + customX;   // pts: dịch phải (+) / trái (-)
        const deltaY   = (window._mbcDeltaY || 0) + customY;   // pts: dịch lên (+) / xuống (-)

        const removeHeader = document.getElementById("mbc-chk-remove-header")?.checked ?? true;
        const STRIP = 22; // pts che header/footer

        const userFile  = fileInfo.input.files[0];
        const userBytes = await readFileAsArrayBuffer(userFile);
        const userDoc   = await PDFDocument.load(userBytes);
        const newPdf    = await PDFDocument.create();

        for (let i = 0; i < userDoc.getPageCount(); i++) {
            const srcPage = userDoc.getPage(i);
            const { width: srcW, height: srcH } = srcPage.getSize();

            // Giữ nguyên kích thước trang (không scale)
            // Chỉ dịch chuyển nội dung theo deltaX, deltaY
            const pageW = tplSize ? tplSize.width  : srcW;
            const pageH = tplSize ? tplSize.height : srcH;

            const newPage  = newPdf.addPage([pageW, pageH]);
            const embedded = await newPdf.embedPage(srcPage);

            // deltaX: dương = dịch nội dung sang phải
            // deltaY: dương = dịch nội dung lên trên (PDF Y tăng = lên)
            newPage.drawPage(embedded, {
                x: deltaX,
                y: deltaY,
                width: srcW,
                height: srcH,
            });

            // Che header/footer nếu được chọn
            if (removeHeader) {
                const HEADER_H = 40; // 40 pts an toàn hơn
                const FOOTER_H = 40;
                
                // Che vùng trên của nội dung (dịch theo deltaY)
                newPage.drawRectangle({
                    x: deltaX - 10, 
                    y: pageH - HEADER_H + deltaY,
                    width: srcW + 20, 
                    height: HEADER_H + 20,
                    color: rgb(1, 1, 1), opacity: 1,
                });
                // Che vùng dưới của nội dung (footer chứa đường dẫn file)
                newPage.drawRectangle({
                    x: deltaX - 10, 
                    y: deltaY - 20,
                    width: srcW + 20, 
                    height: FOOTER_H + 20,
                    color: rgb(1, 1, 1), opacity: 1,
                });
                // Che viền trái nếu lộ
                if (deltaX > 0) {
                    newPage.drawRectangle({
                        x: 0, y: 0, width: deltaX, height: pageH,
                        color: rgb(1, 1, 1), opacity: 1,
                    });
                }
                // Che viền phải nếu lộ
                if (deltaX < 0) {
                    newPage.drawRectangle({
                        x: pageW + deltaX, y: 0, width: -deltaX + 2, height: pageH,
                        color: rgb(1, 1, 1), opacity: 1,
                    });
                }
            }

            // [MỚI] VẼ KHUNG ĐỎ MÔ PHỎNG CON DẤU NẾU ĐANG CHẾ ĐỘ PREVIEW
            if (isPreview && window._mbcTplTextPos) {
                const STAMP_W = 56; // Kích thước xấp xỉ con dấu
                const STAMP_H = 56;
                // Vị trí con dấu thường nằm ở dưới ô text (y đi từ dưới lên nên trừ đi)
                // Chỉnh 1 chút x để lùi vào giữa
                const stampX = window._mbcTplTextPos.x - 5;
                const stampY = window._mbcTplTextPos.y - 70; 

                // Vẽ ô vuông nền đỏ mờ
                newPage.drawRectangle({
                    x: stampX, y: stampY, width: STAMP_W, height: STAMP_H,
                    borderColor: rgb(1, 0, 0),
                    borderWidth: 2,
                    color: rgb(1, 0.2, 0.2),
                    opacity: 0.15,
                });
                
                // Vẽ dấu thập (Crosshair) định vị
                newPage.drawLine({
                    start: { x: stampX, y: stampY + STAMP_H/2 },
                    end: { x: stampX + STAMP_W, y: stampY + STAMP_H/2 },
                    thickness: 1, color: rgb(1, 0, 0), opacity: 0.5
                });
                newPage.drawLine({
                    start: { x: stampX + STAMP_W/2, y: stampY },
                    end: { x: stampX + STAMP_W/2, y: stampY + STAMP_H },
                    thickness: 1, color: rgb(1, 0, 0), opacity: 0.5
                });
            }
        }

        const newBytes = await newPdf.save();
        const newBlob  = new Blob([newBytes], { type: "application/pdf" });
        
        if (isPreview) {
            const blobUrl = URL.createObjectURL(newBlob);
            window.open(blobUrl, "_blank");
            statusEl.innerHTML = "✅ Đã mở bản Xem thử ở Tab mới!<br>Hãy kiểm tra lại. Nếu OK, bấm <b>Áp dụng & Upload</b>.";
            statusEl.style.color = "#27ae60";
            btnScale.disabled = false;
            btnTest.disabled = false;
            return;
        }

        let   newName  = userFile.name.replace(/(_fixed)?\.pdf$/i, "_fixed.pdf");

        const dt = new DataTransfer();
        dt.items.add(new File([newBlob], newName, { type: "application/pdf" }));
        fileInfo.input.files = dt.files;

        statusEl.innerText = "✅ Hoàn tất! Đang Upload...";
        closeScaleModal();

        const targetWin = fileInfo.win;
        if (typeof targetWin.performAjaxSubmit === "function") {
            targetWin.performAjaxSubmit(0);
        } else {
            const btn2 = targetWin.document.getElementById("btnDocUpload");
            if (btn2) { btn2.disabled = false; btn2.click(); }
            else alert("Đã xử lý xong! Vui lòng bấm nút Upload thủ công.");
        }

        setTimeout(() => {
            if (window.opener) window.location.reload();
        }, 3500);

    } catch(e) {
        console.error("[MBC] Lỗi:", e);
        statusEl.innerText = "❌ Lỗi: " + e.message;
        statusEl.style.color = "#e74c3c";
        btn.disabled = false;
    }
}

function closeScaleModal() {
    const modal = document.getElementById("mbc-scale-modal");
    if (modal) modal.remove();
    delete window._mbcTplBytes;
    delete window._mbcTplSize;
    delete window._mbcDeltaX;
    delete window._mbcDeltaY;
}

