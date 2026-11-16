// data-config.js — CẤU HÌNH NGUỒN DỮ LIỆU cho bản deploy ONLINE (GitHub Pages).
//
// BẢN CHẠY CỤC BỘ (app desktop / localhost): để mode = "local" ⇒ dùng API
// của bridge_server (http://127.0.0.1:5690) — nhanh, đầy đủ.
//
// BẢN CHẠY TRÊN ĐIỆN THOẠI (GitHub Pages): mode = "static" ⇒
//   • nội dung: data/<slug>/index.json + data/<slug>/day/<n>.json  (GitHub Pages)
//   • media   : gói .zip theo 30 ngày trên GitHub Releases
//               https://github.com/<repo>/releases/download/<tag>/m01.zip
//   • tiến độ: localStorage (không cần server)
//
// SỬA Ở ĐÂY khi đổi repo / release / khóa học.
(function () {
    // Tự nhận diện: chạy trên máy (localhost/127.0.0.1) ⇒ dùng API app
    // desktop (đầy đủ, nhanh); chạy trên GitHub Pages ⇒ dùng dữ liệu tĩnh.
    let host = "";
    try { host = location.hostname || ""; } catch (e) { host = ""; }
    const isLocal = /^(localhost|127\.0\.0\.1|0\.0\.0\.0|::1)$/.test(host)
        || host === "";
    // Ép chế độ bằng query: ?mode=static | ?mode=local (để thử trên máy)
    let forced = "";
    try {
        forced = (new URLSearchParams(location.search).get("mode") || "").toLowerCase();
    } catch (e) { forced = ""; }
    window.VOCAB_DATA = {
        mode: (forced === "static" || forced === "local")
            ? forced : (isLocal ? "local" : "static"),
        repo: "ThaiBao1991/Project1",
        api: "http://127.0.0.1:5690",

        // Nội dung tĩnh (Pages). Bỏ trống ⇒ dùng đường dẫn tương đối.
        dataBase: "data",

        // Media theo gói .zip trên GitHub Releases: slug → tag release
        // (tag ASCII: "tiếng_nhật" → "data-tieng-nhat-v1")
        releases: {
            "tiếng_nhật": "data-tieng-nhat-v1",
            "tiếng_trung": "data-tieng-trung-v1",
            "tiếng_anh": "data-tieng-anh-v1",
            "tiếng_hàn_quốc": "data-tieng-han-quoc-v1",
            "tiếng_nga": "data-tieng-nga-v1",
            "tiếng_pháp": "data-tieng-phap-v1",
            "tiếng_tây_ban_nha": "data-tieng-tay-ban-nha-v1",
            "tiếng_đức": "data-tieng-duc-v1"
        },

        // Tự tải gói media khi mở ngày thuộc gói đó (điện thoại: bật 4G/WiFi)
        autoFetchMedia: true,
        // Bộ nhớ đệm gói media đã giải nén (CacheStorage)
        cacheMedia: true
    };
})();
