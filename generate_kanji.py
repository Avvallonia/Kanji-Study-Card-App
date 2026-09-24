#!/usr/bin/env python3
"""
generate_kanji.py — собирает kanji_data.js из открытых датасетов.
Источники:
  1) AnchorI/jlpt-kanji-dictionary — уровни JLPT + русские переводы слов
  2) davidluzgouveia/kanji-data    — онные/кунные чтения + английские значения
"""

import json, urllib.request, re, pathlib

ANCHOR = "https://raw.githubusercontent.com/AnchorI/jlpt-kanji-dictionary/main/"
DAVID  = "https://raw.githubusercontent.com/davidluzgouveia/kanji-data/master/kanji.json"
KANA_RE = re.compile(r"^[\u3040-\u309F\u30A0-\u30FFー・]+$")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode("utf-8"))


def normalize_list(raw):
    result = {}
    if isinstance(raw, dict):
        for k, v in raw.items():
            if isinstance(v, dict):
                info = dict(v); info.setdefault("kanji", k); result[k] = info
        return result
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict):
                k = item.get("kanji") or item.get("character") or item.get("literal")
                if k: result[k] = item
    return result


def get_level(info):
    for key in ("jlpt", "jlpt_level", "level", "JLPT"):
        v = info.get(key)
        if v:
            v = str(v).upper()
            return v if v.startswith("N") else "N" + v
    return "N5"


def get_readings(info):
    """Главное исправление: ключи называются readings_on / readings_kun."""
    on = info.get("readings_on") or []
    kun = info.get("readings_kun") or []
    if isinstance(on, str): on = [on]
    if isinstance(kun, str): kun = [kun]
    return [str(x) for x in on], [str(x) for x in kun]


def clean_ru(text, max_items=3):
    """Чистит словарные статьи из AnchorI."""
    if not text: return ""
    text = re.sub(r"\{[^}]*\}", "", text)
    text = re.sub(r"\([^)]*\)", "", text)
    text = re.sub(r"（[^）]*）", "", text)
    text = re.sub(r"【[^】]*】", "", text)
    text = re.sub(r"…[^\s,;]*", "", text)
    text = re.sub(r"\b\d+\)", "", text)
    text = re.sub(r"\s+", " ", text).strip(" .,;")
    parts = [p.strip(" .,;") for p in re.split(r"[,;]", text) if p.strip(" .,;")]
    parts = [p for p in parts if len(p) > 1 and not KANA_RE.match(p)]
    # Удаляем дубликаты, сохраняя порядок
    seen, out = set(), []
    for p in parts:
        if p.lower() not in seen:
            seen.add(p.lower()); out.append(p)
    return ", ".join(out[:max_items])


def clean_english(meanings):
    """Чистит английские значения из david: убирает 'Counter For...' и т.п."""
    out = []
    for m in meanings:
        m = m.strip()
        low = m.lower()
        if low.startswith("counter for"): continue
        if "radical" in low: continue
        out.append(m.lower())
    return ", ".join(out[:3])


def pick_examples(kanji, words, limit=3):
    single, start, end, other = [], [], [], []
    seen = set()
    for w in words:
        word = w.get("kanji") or ""
        reading = w.get("reading") or ""
        if not word or not reading or word in seen: continue
        seen.add(word)
        gloss = w.get("glossary_ru") or w.get("glossary_en") or []
        meaning = gloss[0] if isinstance(gloss, list) and gloss else (gloss if isinstance(gloss, str) else "")
        if len(word) > 4: continue
        entry = f"{word}:{reading}:{meaning}"
        if len(word) == 1: single.append(entry)
        elif word.startswith(kanji): start.append(entry)
        elif word.endswith(kanji): end.append(entry)
        else: other.append(entry)
    return (single + start + end + other)[:limit]


# ---------- Загрузка ----------
print("1/4 Кандзи (AnchorI)...")
kanji_list = normalize_list(fetch(ANCHOR + "jlpt-kanji.json"))
print(f"     {len(kanji_list)} кандзи")

print("2/4 Словарь (AnchorI)...")
dictionary = []
for i in range(1, 5):
    dictionary += fetch(ANCHOR + f"dictionary_part_{i}.json")
print(f"     {len(dictionary)} слов")

print("3/4 Чтения и значения (davidluzgouveia)...")
david = normalize_list(fetch(DAVID))
print(f"     {len(david)} записей")

# ---------- Индексы ----------
ru_single = {}
words_by_kanji = {}
for w in dictionary:
    word = w.get("kanji") or ""
    if not word: continue
    gloss_ru = w.get("glossary_ru") or []
    if len(word) == 1 and gloss_ru and word not in ru_single:
        ru_single[word] = gloss_ru
    for ch in word:
        words_by_kanji.setdefault(ch, []).append(w)

# Ручной запасной из index.html
fallback = {}
if pathlib.Path("index.html").exists():
    html = pathlib.Path("index.html").read_text(encoding="utf-8")
    m = re.search(r"const KANJI_RAW = `(.*?)`;", html, re.S)
    if m:
        for line in m.group(1).strip().split("\n"):
            parts = line.split("|")
            if len(parts) >= 4:
                fallback[parts[0].strip()] = parts

# ---------- Генерация ----------
print("4/4 Генерирую kanji_data.js...")
out_lines = []
levels_count = {}
empty_readings = 0
empty_meaning_ru = 0

for kanji, info in sorted(kanji_list.items(), key=lambda x: (get_level(x[1]), x[0])):
    level = get_level(info)
    levels_count[level] = levels_count.get(level, 0) + 1
    d_info = david.get(kanji, {})

    # --- Значение ---
    meanings = ""
    # 1) русский из однобуквенного слова
    if kanji in ru_single:
        meanings = clean_ru("; ".join(ru_single[kanji][:3]))
    # 2) ручной список
    if not meanings and kanji in fallback and len(fallback[kanji]) > 1:
        meanings = fallback[kanji][1]
    # 3) английский из david
    if not meanings:
        eng = d_info.get("meanings", [])
        if eng:
            meanings = clean_english(eng)
    # 4) описание из AnchorI (обрезанное)
    if not meanings:
        desc = info.get("description") or ""
        m2 = re.search(r"means ([^.]+)", desc)
        meanings = (m2.group(1).strip().lower() if m2 else "")
    if not meanings:
        meanings = "—"
        empty_meaning_ru += 1
    meanings = meanings.replace("|", "/").strip()

    # --- Чтения ---
    on_list, kun_list = [], []
    if d_info:
        on_list, kun_list = get_readings(d_info)
    if not on_list and kanji in fallback and len(fallback[kanji]) > 2:
        on_list = [r.strip() for r in fallback[kanji][2].split(",") if r.strip()]
    if not kun_list and kanji in fallback and len(fallback[kanji]) > 3:
        kun_list = [r.strip() for r in fallback[kanji][3].split(",") if r.strip()]
    if not on_list and not kun_list:
        empty_readings += 1

    on_str = ", ".join(dict.fromkeys(on_list))[:80]
    kun_str = ", ".join(dict.fromkeys(kun_list))[:80]

    # --- Примеры ---
    if kanji in fallback and len(fallback[kanji]) > 4 and fallback[kanji][4]:
        examples = [e for e in fallback[kanji][4].split(";") if e.strip()]
    else:
        examples = pick_examples(kanji, words_by_kanji.get(kanji, []), limit=3)
    ex_str = "; ".join(examples[:3]).replace("|", "/")

    out_lines.append(f"{kanji}|{level}|{meanings}|{on_str}|{kun_str}|{ex_str}")

header = (
    "// Автоматически сгенерировано generate_kanji.py\n"
    "// Источники: AnchorI/jlpt-kanji-dictionary, davidluzgouveia/kanji-data\n"
    "const KANJI_DB = `\n"
)
with open("kanji_data.js", "w", encoding="utf-8") as f:
    f.write(header + "\n".join(out_lines) + "\n`.trim();\n")

print(f"\n✅ Кандзи: {len(out_lines)}")
for lv in sorted(levels_count): print(f"   {lv}: {levels_count[lv]}")
print(f"   Без чтений:       {empty_readings}")
print(f"   Без значений:     {empty_meaning_ru}")