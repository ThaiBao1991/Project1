# Audit toàn bộ — 2026-11-19 20:48:32

Thời gian chạy: **2713s** · FAIL: **0** · WARN: **7**

## 1. Tiến độ media

| Khóa | Ngày local | Còn | % | Uploaded |
|---|---:|---:|---:|---|
| tiếng_nhật | 0/2520 | 2520 | 0.0% | ✅ |
| tiếng_anh | 1429/2520 | 1091 | 56.71% | — |
| tiếng_hàn_quốc | 1156/2520 | 1364 | 45.87% | — |
| tiếng_nga | 600/2520 | 1920 | 23.81% | — |
| tiếng_pháp | 600/2520 | 1920 | 23.81% | — |
| tiếng_tây_ban_nha | 926/2520 | 1594 | 36.75% | — |
| tiếng_đức | 600/2520 | 1920 | 23.81% | — |
| tiếng_trung | 0/2520 | 2520 | 0.0% | ✅ |

## 2. Dung lượng

| Nhóm | GB | File |
|---|---:|---:|
| data/media | 1.64 | 169079 |
| data/audio | 0.07 | 4429 |
| data/ai_courses | 0.86 | 76424 |
| web/data | 0.58 | 20177 |
| web | 0.58 | 20189 |
| publish | 0.00 | 0 |
| media/tiếng_anh | 0.40 | 44542 |
| media/tiếng_hàn_quốc | 0.32 | 36088 |
| media/tiếng_nga | 0.20 | 19828 |
| media/tiếng_pháp | 0.17 | 19007 |
| media/tiếng_tây_ban_nha | 0.20 | 29627 |
| media/tiếng_đức | 0.14 | 19277 |
| media/_cards | 0.01 | 899 |

- MP3: 114994 file, 1.37 GB; bitrate mẫu: {32: 200}
- Tiết kiệm dự kiến khi nén 32 kbps: **0.00 GB**
- File tạm/rác: **0.03 GB**
- Repo GitHub: {'ThaiBao1991/VocabularyData': 2.82, 'ThaiBao1991/Project1': 5.48}

## 3. Nội dung

| Khóa | Ngày | Mẫu câu | Câu thông dụng | Ngữ pháp | Hội thoại | Quiz G/C | Template | Script lỗi |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| tiếng_nhật | 2520 | 4 | 5 | 2 | 1 | 3/3 | 0 | 0 |
| tiếng_anh | 2520 | 4 | 5 | 2 | 1 | 3/3 | 0 | 0 |
| tiếng_hàn_quốc | 2520 | 4 | 5 | 2 | 1 | 3/3 | 0 | 0 |
| tiếng_nga | 2520 | 4 | 5 | 2 | 1 | 3/3 | 0 | 0 |
| tiếng_pháp | 2520 | 4 | 5 | 2 | 1 | 3/3 | 0 | 0 |
| tiếng_tây_ban_nha | 2520 | 4 | 5 | 2 | 1 | 3/3 | 0 | 0 |
| tiếng_đức | 2520 | 4 | 5 | 2 | 1 | 3/3 | 0 | 0 |
| tiếng_trung | 2520 | 4 | 5 | 2 | 1 | 3/3 | 0 | 0 |

## 4. Toàn vẹn media

```
{"manifest_items": 326413, "days_with_map": 8664, "refs": 274632, "missing": 3, "examples": [["tiếng_nhật", 111, "m_3016d013"], ["tiếng_anh", 525, "m_0363158f"], ["tiếng_pháp", 105, "m_a07a3a83"]]}
```

## 5. Online

```
{"verify_rc": 0, "verify_tail": ["→ 9/9 PASS"], "sw": "vocab-v9", "days": {"tiếng_nhật": {"pat": 4, "common": 5, "gram": 4, "turns": 9, "quiz": 16}, "tiếng_anh": {"pat": 4, "common": 5, "gram": 4, "turns": 10, "quiz": 16}, "tiếng_hàn_quốc": {"pat": 4, "common": 5, "gram": 4, "turns": 12, "quiz": 16}, "tiếng_nga": {"pat": 4, "common": 5, "gram": 4, "turns": 12, "quiz": 16}, "tiếng_pháp": {"pat": 4, "common": 5, "gram": 4, "turns": 6, "quiz": 16}, "tiếng_tây_ban_nha": {"pat": 4, "common": 5, "gram": 4, "turns": 9, "quiz": 16}, "tiếng_đức": {"pat": 4, "common": 5, "gram": 4, "turns": 9, "quiz": 16}, "tiếng_trung": {"pat": 4, "common": 5, "gram": 4, "turns": 9, "quiz": 16}}}
```

## 6. Test

```
{"test_web_contract.py": {"rc": 0, "tail": ["✅ TẤT CẢ PASS"]}, "test_content_quality.py": {"rc": 0, "tail": ["✅ TẤT CẢ PASS"]}}
```

## 7. Git

```
{'count': 'count: 1125\nsize: 328.84 MiB\nin-pack: 19655\npacks: 9\nsize-pack: 8.76 GiB\nprune-packable: 0\ngarbage: 0\nsize-garbage: 0 bytes', 'status': '', 'last': '640052c8 ops(vocab): chuyen data lon sang F junction + ha nguong dia\n77cf522f chore(vocab): ha nguong dia chang cuoi + ghi nhan nen audio 615MB\n8b884d07 fix(vocab): supervisor media chay tung khoa den khi du 2520'}
```

## 8. Kết luận

- Không có FAIL.
- WARN: tiếng_anh: mới 1429/2520 ngày media
- WARN: tiếng_hàn_quốc: mới 1156/2520 ngày media
- WARN: tiếng_nga: mới 600/2520 ngày media
- WARN: tiếng_pháp: mới 600/2520 ngày media
- WARN: tiếng_tây_ban_nha: mới 926/2520 ngày media
- WARN: tiếng_đức: mới 600/2520 ngày media
- WARN: media_map: 3 ref mới chưa kịp vào manifest (đang fill)
