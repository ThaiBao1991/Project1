# tts_selfbuilt.py — Hệ thống TTS tự-built (edge-tts) với concurrent processing
# Sinh audio cho toàn bộ 12,600 từ vựng tiếng Nhật

import asyncio
import json
import hashlib
import sys
from pathlib import Path

try:
    import edge_tts
except ImportError:
    print("edge-tts chua cai dat")
    sys.exit(1)

BASE = Path(r'C:\Users\games\Desktop\Project\Python\Python MyWork\Project1\GravityCode\VocabularyApp')
COURSE_PATH = BASE / 'data' / 'ai_courses' / 'tiếng_nhật' / 'course.json'
AUDIO_DIR = BASE / 'data' / 'audio' / 'tiếng_nhật'

VOICE_JA = 'ja-JP-NanamiNeural'
RATE = '+0%'
VOLUME = '+0%'
MAX_CONCURRENT = 8  # So luong request song song

AUDIO_DIR.mkdir(parents=True, exist_ok=True)


def hash_filename(text, day, kind, index):
    h = hashlib.md5(f"{day}_{kind}_{index}_{text}".encode('utf-8')).hexdigest()[:8]
    safe = ''.join(c if c.isalnum() else '_' for c in str(text))[:25]
    return f'd{day:04d}_{kind}_{index:03d}_{safe}_{h}.mp3'


async def synthesize_one(semaphore, text, output_path, voice=VOICE_JA, rate=RATE, volume=VOLUME):
    """Sinh 1 file MP3 voi giao han concurrency."""
    if not text or not text.strip():
        return False, text
    async with semaphore:
        try:
            communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume)
            await communicate.save(str(output_path))
            return output_path.exists(), text
        except Exception as e:
            return False, f'{text} (error: {e})'


async def main():
    with open(COURSE_PATH, 'r', encoding='utf-8') as f:
        course = json.load(f)

    days = course.get('days', [])
    print(f'Co {len(days)} ngay, bat dau sinh audio (concurrent={MAX_CONCURRENT})...')

    # Collect all tasks that need audio
    tasks = []
    vocab_info = []  # Store (day, day_num, index, word, vocab_dict) for updating later

    for d in days:
        day_num = d.get('day', 0)
        day_dir = AUDIO_DIR / f'd{day_num:04d}'
        day_dir.mkdir(parents=True, exist_ok=True)

        if 'audio' not in d:
            d['audio'] = {}

        vocab_list = d.get('vocab', [])
        for i, v in enumerate(vocab_list):
            word = v.get('word', '')
            if not word:
                continue

            # Skip if already has audio_ref and file exists
            existing_ref = v.get('audio_ref')
            if existing_ref:
                ref_path = BASE / existing_ref
                if ref_path.exists():
                    continue

            filename = hash_filename(word, day_num, 'vocab', i)
            filepath = day_dir / filename

            tasks.append(synthesize_one(asyncio.Semaphore(MAX_CONCURRENT), word, filepath))
            vocab_info.append((d, day_num, i, word, filepath, v))

    print(f'Tong so can sinh: {len(tasks)}')

    # Process in batches to avoid memory issues
    BATCH_SIZE = 200
    total_done = 0
    total_success = 0
    total_failed = 0

    for batch_start in range(0, len(tasks), BATCH_SIZE):
        batch = tasks[batch_start:batch_start + BATCH_SIZE]
        batch_info = vocab_info[batch_start:batch_start + BATCH_SIZE]

        results = await asyncio.gather(*batch, return_exceptions=True)

        for result, info in zip(results, batch_info):
            if isinstance(result, Exception):
                total_failed += 1
                continue

            success, text_or_error = result
            d, day_num, index, word, filepath, v = info

            if success:
                rel_path = f'audio/tieng_nhat/d{day_num:04d}/{filepath.name}'
                v['audio_ref'] = rel_path
                if 'media' not in d:
                    d['media'] = {}
                if 'vocab_audio' not in d['media']:
                    d['media']['vocab_audio'] = {}
                d['media']['vocab_audio'][word] = rel_path
                total_success += 1
            else:
                total_failed += 1

            total_done += 1

        # Save progress after each batch
        with open(COURSE_PATH, 'w', encoding='utf-8') as f:
            json.dump(course, f, ensure_ascii=False, indent=2)

        if total_done % 200 == 0 or total_done == len(tasks):
            print(f'  Da xu ly {total_done}/{len(tasks)}, thanh cong: {total_success}, that bai: {total_failed}')

    # Final save
    with open(COURSE_PATH, 'w', encoding='utf-8') as f:
        json.dump(course, f, ensure_ascii=False, indent=2)

    print(f'\nHOAN TAT TTS')
    print(f'Tong can sinh: {len(tasks)}')
    print(f'Thanh cong: {total_success}')
    print(f'That bai: {total_failed}')
    print(f'Luu tai: data/audio/tieng_nhat')


if __name__ == '__main__':
    asyncio.run(main())
