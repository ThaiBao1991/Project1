// paths.js — SINH TỰ ĐỘNG bởi `python -m ai.paths --export-js`.
// Nguồn sự thật duy nhất: ai/paths.py. KHÔNG sửa tay.
const VOCAB_SLUG = (s) => String(s || '').trim().toLowerCase().replace(/\s+/g, '_');
const VOCAB_LANGS = [{"slug": "nhật", "display": "Nhật"}, {"slug": "tiếng_anh", "display": "Tiếng Anh"}, {"slug": "tiếng_hàn_quốc", "display": "Tiếng Hàn Quốc"}, {"slug": "tiếng_nga", "display": "Tiếng Nga"}, {"slug": "tiếng_pháp", "display": "Tiếng Pháp"}, {"slug": "tiếng_trung", "display": "Tiếng Trung"}, {"slug": "tiếng_tây_ban_nha", "display": "Tiếng Tây Ban Nha"}, {"slug": "tiếng_đức", "display": "Tiếng Đức"}];
