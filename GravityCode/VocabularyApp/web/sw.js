// sw.js â€” SERVICE WORKER cho báº£n há»c trÃªn Ä‘iá»‡n thoáº¡i (GitHub Pages).
//
// Má»¤C TIÃŠU: má»Ÿ app khi KHÃ”NG cÃ³ máº¡ng váº«n há»c Ä‘Æ°á»£c nhá»¯ng ngÃ y Ä‘Ã£ xem.
//   â€¢ App shell (html/css/js/icon): cache-first, cáº­p nháº­t ngáº§m.
//   â€¢ data/<khÃ³a>/index.json: network-first (Ä‘á»ƒ biáº¿t khÃ³a má»›i), fallback cache.
//   â€¢ data/<khÃ³a>/day/<n>.json: stale-while-revalidate (má»Ÿ tá»©c thÃ¬, ná»n cáº­p nháº­t).
//   â€¢ GÃ³i media .zip (GitHub API): KHÃ”NG cache á»Ÿ Ä‘Ã¢y â€” script.js tá»± cache
//     trong CacheStorage "vocab-media-v1" (xem _fetchBundleBytes).
//
// Äá»•i VERSION khi sá»­a app shell Ä‘á»ƒ buá»™c cáº­p nháº­t.
const VERSION = "vocab-v9";
const SHELL = [
    "./",
    "./index.html",
    "./style.css",
    "./script.js",
    "./paths.js",
    "./zipreader.js",
    "./data-config.js",
    "./manifest.json",
    "./icons/icon192.png",
    "./icons/icon512.png",
];

self.addEventListener("install", (e) => {
    e.waitUntil((async () => {
        const c = await caches.open(VERSION);
        // ThÃªm tá»«ng file (má»™t file lá»—i khÃ´ng lÃ m há»ng cáº£ install)
        await Promise.all(SHELL.map((u) => c.add(new Request(u, { cache: "reload" })).catch(() => null)));
        self.skipWaiting();
    })());
});

self.addEventListener("activate", (e) => {
    e.waitUntil((async () => {
        const keys = await caches.keys();
        await Promise.all(keys.filter((k) => k !== VERSION && k !== "vocab-media-v1")
            .map((k) => caches.delete(k)));
        await self.clients.claim();
    })());
});

function isDayJson(url) {
    return /\/data\/[^/]+\/day\/\d+\.json$/.test(url.pathname);
}
function isCourseIndex(url) {
    return /\/data\/(index\.json|[^/]+\/index\.json)$/.test(url.pathname);
}

self.addEventListener("fetch", (e) => {
    const req = e.request;
    if (req.method !== "GET") return;
    let url;
    try { url = new URL(req.url); } catch (_) { return; }
    if (url.origin !== self.location.origin) return;   // GitHub API/Release: Ä‘á»ƒ trÃ¬nh duyá»‡t tá»± lo

    // Ná»™i dung ngÃ y: stale-while-revalidate
    if (isDayJson(url)) {
        e.respondWith((async () => {
            const c = await caches.open(VERSION);
            const hit = await c.match(req);
            const net = fetch(req).then((r) => {
                if (r && r.ok) c.put(req, r.clone()).catch(() => {});
                return r;
            }).catch(() => null);
            return hit || (await net) || new Response("{}", { headers: { "Content-Type": "application/json" } });
        })());
        return;
    }

    // index.json: network-first
    if (isCourseIndex(url)) {
        e.respondWith((async () => {
            const c = await caches.open(VERSION);
            try {
                const r = await fetch(req);
                if (r && r.ok) c.put(req, r.clone()).catch(() => {});
                return r;
            } catch (err) {
                const hit = await c.match(req);
                if (hit) return hit;
                throw err;
            }
        })());
        return;
    }

    // App shell + asset tÄ©nh: NETWORK-FIRST (Ä‘á»ƒ báº£n má»›i Ã¡p dá»¥ng ngay),
    // fallback cache khi máº¥t máº¡ng. `cache: "reload"` Ä‘á»ƒ KHÃ”NG dÃ¹ng HTTP cache
    // cÅ© cá»§a trÃ¬nh duyá»‡t (Ä‘o tháº­t: sá»­a data-config.js mÃ  Ä‘iá»‡n thoáº¡i váº«n cháº¡y
    // báº£n cÅ© vÃ¬ HTTP cache + SW cache-first).
    if (url.pathname.endsWith("/") || /\.(html|css|js|json|png|webp|svg|ico)$/.test(url.pathname)) {
        e.respondWith((async () => {
            const c = await caches.open(VERSION);
            try {
                const r = await fetch(req, { cache: "reload" });
                if (r && r.ok) c.put(req, r.clone()).catch(() => {});
                return r;
            } catch (err) {
                const hit = await c.match(req, { ignoreSearch: true });
                if (hit) return hit;
                throw err;
            }
        })());
    }
});
