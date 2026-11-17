// zipreader.js — ĐỌC FILE .ZIP TRONG TRÌNH DUYỆT (không cần thư viện ngoài).
//
// VÌ SAO CẦN: bản deploy online đóng gói media theo "gói 30 ngày" (.zip)
// để điện thoại chỉ tải phần đang học (~11 MB/gói) thay vì 2,6 GB.
//
// CÀI ĐẶT:
//   • Dùng `DecompressionStream('deflate-raw')` (Chrome 103+, Safari 16.4+,
//     Firefox 113+) ⇒ giải nén deflate native, KHÔNG cần thư viện.
//   • Tự đọc cấu trúc ZIP (EOCD → Central Directory → Local Header).
//
// API:
//   VOCAB_ZIP.supported()          -> boolean
//   VOCAB_ZIP.read(arrayBuffer)     -> Promise<{ "d0010/x.webp": Uint8Array, ... }>
(function (global) {
    "use strict";

    const EOCD_SIG = 0x06054b50;
    const CEN_SIG = 0x02014b50;
    const LOC_SIG = 0x04034b50;

    function supported() {
        return typeof DecompressionStream === "function";
    }

    async function inflateRaw(bytes) {
        const ds = new DecompressionStream("deflate-raw");
        const stream = new Blob([bytes]).stream().pipeThrough(ds);
        const buf = await new Response(stream).arrayBuffer();
        return new Uint8Array(buf);
    }

    async function read(arrayBuffer) {
        if (!supported()) throw new Error("Trình duyệt không hỗ trợ DecompressionStream");
        const u8 = new Uint8Array(arrayBuffer);
        const dv = new DataView(arrayBuffer);

        // 1) Tìm EOCD (End of Central Directory) — quét từ cuối về.
        let eocd = -1;
        for (let i = u8.length - 22; i >= Math.max(0, u8.length - 66000); i--) {
            if (dv.getUint32(i, true) === EOCD_SIG) { eocd = i; break; }
        }
        if (eocd < 0) throw new Error("Không tìm thấy EOCD — file zip hỏng?");

        const count = dv.getUint16(eocd + 10, true);
        let ptr = dv.getUint32(eocd + 16, true);

        const out = {};
        for (let i = 0; i < count; i++) {
            if (dv.getUint32(ptr, true) !== CEN_SIG) break;
            const method = dv.getUint16(ptr + 10, true);
            const compSize = dv.getUint32(ptr + 20, true);
            const nameLen = dv.getUint16(ptr + 28, true);
            const extraLen = dv.getUint16(ptr + 30, true);
            const commentLen = dv.getUint16(ptr + 32, true);
            const locOff = dv.getUint32(ptr + 42, true);
            const name = new TextDecoder().decode(
                u8.subarray(ptr + 46, ptr + 46 + nameLen));

            // 2) Đọc Local File Header để lấy độ dài tên/extra thực tế
            if (dv.getUint32(locOff, true) !== LOC_SIG) { ptr += 46 + nameLen + extraLen + commentLen; continue; }
            const locNameLen = dv.getUint16(locOff + 26, true);
            const locExtraLen = dv.getUint16(locOff + 28, true);
            const dataStart = locOff + 30 + locNameLen + locExtraLen;
            const raw = u8.subarray(dataStart, dataStart + compSize);

            if (method === 0) {
                out[name] = raw.slice();
            } else if (method === 8) {
                out[name] = await inflateRaw(raw);
            }
            ptr += 46 + nameLen + extraLen + commentLen;
        }
        return out;
    }

    global.VOCAB_ZIP = { supported, read };
})(typeof window !== "undefined" ? window : this);
