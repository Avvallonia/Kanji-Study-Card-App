#!/usr/bin/env python3
"""
warodai_mini.py — компактный словарь только для слов из kanji_data.js.
Читает JS-формат: "слово;слово2": { r: "чтение", m: "перевод" },
"""

import re, pathlib

INPUT_WARODAI = 'warodai_data.js'   # фактически это наш warodai_data.js
INPUT_KANJI   = 'kanji_data.js'
OUTPUT        = 'warodai_mini.js'

# Регулярка для строки "浮子;網端": { r: "あば", m: "поплавок [рыбачьей] сети" },
LINE_RE = re.compile(
    r'^\s*"((?:[^"\\]|\\.)*)"\s*:\s*\{\s*'
    r'r\s*:\s*"((?:[^"\\]|\\.)*)"\s*,\s*'
    r'm\s*:\s*"((?:[^"\\]|\\.)*)"\s*\}'
)


def unescape(s):
    return s.replace('\\"', '"').replace('\\\\', '\\')


# ---------- 1. Парсим Warodai ----------
print("1/3 Парсим Warodai...")
warodai = {}
total_lines = 0
parsed_lines = 0
samples = []

with open(INPUT_WARODAI, 'r', encoding='utf-8') as f:
    for line in f:
        total_lines += 1
        m = LINE_RE.match(line)
        if not m:
            continue
        parsed_lines += 1
        words_raw, reading, meaning = m.group(1), m.group(2), m.group(3)
        words_raw = unescape(words_raw)
        reading   = unescape(reading)
        meaning   = unescape(meaning)

        if len(samples) < 5:
            samples.append((words_raw, reading, meaning))

        for w in words_raw.split(';'):
            w = w.strip()
            if not w:
                continue
            key = f"{w}:{reading}"
            warodai.setdefault(key, meaning)
            warodai.setdefault(f"{w}:", meaning)

print(f"   Всего строк: {total_lines}")
print(f"   Распарсено:  {parsed_lines}")
print(f"   Индексов:    {len(warodai)}")
print("\n   Примеры:")
for w, r, m in samples:
    print(f"   • {w} [{r}] → {m[:60]}")

if parsed_lines == 0:
    print("\n⚠️  Ничего не распарсилось. Проверь формат файла.")
    raise SystemExit(1)

# ---------- 2. Нужные слова из kanji_data.js ----------
print("\n2/3 Читаю kanji_data.js...")
needed = set()
with open(INPUT_KANJI, 'r', encoding='utf-8') as f:
    for line in f:
        parts = line.split('|')
        if len(parts) < 6:
            continue
        for ex in parts[5].split(';'):
            segs = ex.split(':')
            if len(segs) >= 2:
                word = segs[0].strip()
                reading = segs[1].strip()
                if word:
                    needed.add(f"{word}:{reading}")
                    needed.add(f"{word}:")
print(f"   Нужно слов: {len(needed)}")

# ---------- 3. Фильтр и запись ----------
print("3/3 Генерирую warodai_mini.js...")
found = {k: v for k, v in warodai.items() if k in needed}

with open(OUTPUT, 'w', encoding='utf-8') as f:
    f.write("// Автоматически сгенерировано warodai_mini.py\n")
    f.write("// Источник: Warodai (CC BY-NC-ND 3.0) — www.warodai.ru\n")
    f.write("const WARODAI = {\n")
    for k in sorted(found):
        kk = k.replace('\\', '\\\\').replace('"', '\\"')
        mm = found[k].replace('\\', '\\\\').replace('"', '\\"')
        f.write(f'  "{kk}": "{mm}",\n')
    f.write("};\n")

size = pathlib.Path(OUTPUT).stat().st_size
print(f"\n✅ Готово! {OUTPUT} — {size // 1024} КБ, {len(found)} переводов")