# warodai_to_json.py
import re
import json

# Путь к скачанному файлу EDICT2 (например, warodai.edict2)
INPUT_FILE = 'ewarodaiedict.txt'
OUTPUT_FILE = 'warodai_data.js'

def parse_edict2(filename):
    entries = {}
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Разбор строки EDICT2
            # Пример: 日本 [にほん] /(n) Япония/
            parts = re.split(r'\s*\[', line, 1)
            if len(parts) < 2:
                continue
            
            word_part = parts[0]
            rest = '[' + parts[1]
            
            reading_match = re.match(r'\[([^\]]+)\]', rest)
            reading = reading_match.group(1) if reading_match else ''
            
            # Извлекаем переводы, разделённые слешами
            meanings = re.findall(r'/([^/]+)/', rest)
            
            # Очищаем и объединяем
            clean_meanings = []
            for m in meanings:
                # Убираем пометки типа (n), (adj) и т.д.
                m = re.sub(r'\([^)]*\)', '', m).strip()
                if m:
                    clean_meanings.append(m)
            
            if word_part and clean_meanings:
                # Сохраняем по слову и по чтению
                entry = {
                    'word': word_part,
                    'reading': reading,
                    'meanings': clean_meanings
                }
                entries[word_part] = entry
                if reading:
                    entries[reading] = entry
    
    return entries

def main():
    print("Парсинг Warodai...")
    data = parse_edict2(INPUT_FILE)
    print(f"Найдено статей: {len(data)}")
    
    # Генерируем JS-файл
    js_lines = []
    js_lines.append("// Автоматически сгенерировано из Warodai")
    js_lines.append("// Лицензия: CC BY-NC-ND 3.0")
    js_lines.append("const WARODAI_DATA = {")
    
    for key, entry in data.items():
        # Экранируем кавычки
        word = entry['word'].replace('"', '\\"')
        reading = entry['reading'].replace('"', '\\"')
        meanings_str = '; '.join(entry['meanings']).replace('"', '\\"')
        
        js_lines.append(f'  "{word}": {{ r: "{reading}", m: "{meanings_str}" }},')
    
    js_lines.append("};")
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(js_lines))
    
    print(f"Готово! Файл {OUTPUT_FILE} создан.")

if __name__ == '__main__':
    main()