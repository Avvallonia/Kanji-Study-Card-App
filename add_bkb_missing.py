#!/usr/bin/env python3
"""
add_bkb_missing.py — находит кандзи, которые есть в BKB,
но отсутствуют в kanji_data.js, и добавляет их туда.
"""

import re, pathlib

KANJI_DATA = 'kanji_data.js'
BKB_DATA   = 'bkb_data.js'

# Кандзи-диапазон (иероглифы CJK)
KANJI_RE = re.compile(r'[\u4E00-\u9FFF\u3400-\u4DBF]')

def read_kanji_data():
    """Возвращает (список строк, множество кандзи)."""
    path = pathlib.Path(KANJI_DATA)
    if not path.exists():
        raise SystemExit(f'{KANJI_DATA} не найден')
    content = path.read_text(encoding='utf-8')
    m = re.search(r'const KANJI_DB = `(.*?)`\.trim\(\);', content, re.S)
    if not m:
        raise SystemExit('Не удалось найти KANJI_DB в kanji_data.js')
    body = m.group(1)
    lines = [l for l in body.split('\n') if l.strip()]
    existing = set()
    for l in lines:
        parts = l.split('|')
        if parts:
            existing.add(parts[0].strip())
    return content, body, lines, existing

def read_bkb():
    """Возвращает множество кандзи из BKB."""
    path = pathlib.Path(BKB_DATA)
    if not path.exists():
        raise SystemExit(f'{BKB_DATA} не найден')
    content = path.read_text(encoding='utf-8')
    # Строки вида: "日": { m: "...", ex: [...] },
    return set(re.findall(r'"([\u4E00-\u9FFF\u3400-\u4DBF])"\s*:', content))

def main():
    content, body, lines, existing = read_kanji_data()
    bkb = read_bkb()

    missing = sorted(bkb - existing)
    print(f'В BKB: {len(bkb)}')
    print(f'В kanji_data.js: {len(existing)}')
    print(f'Отсутствуют в JLPT-базе: {len(missing)}')
    print(f'\nСписок: {"".join(missing)}')

    if not missing:
        print('\n✅ Нечего добавлять.')
        return

    # Добавляем строки с уровнем "bkb" (не JLPT)
    new_lines = list(lines)
    for k in missing:
        # kanji|level|значения|онные|кунные|примеры
        # Оставляем значения пустыми — они подтянутся из BKB
        new_lines.append(f'{k}|BKB|—|||')

    new_body = '\n'.join(new_lines)
    new_content = content.replace(body, new_body)

    pathlib.Path(KANJI_DATA).write_text(new_content, encoding='utf-8')
    print(f'\n✅ Добавлено {len(missing)} кандзи в {KANJI_DATA}')
    print('Теперь в приложении будет ~500 кандзи по книге BKB.')

if __name__ == '__main__':
    main()
