#!/usr/bin/env python3
"""Генерирует PNG-иконки для PWA. Требует: pip install Pillow"""

from PIL import Image, ImageDraw, ImageFont
import os

# Размеры: имя_файла -> (размер, режим)
ICONS = {
    "icon-192.png":          (192, "normal"),
    "icon-512.png":          (512, "normal"),
    "icon-maskable-512.png": (512, "maskable"),
    "apple-touch-icon.png":  (180, "normal"),
}

BG      = (15, 17, 21, 255)     # #0f1115
CIRCLE  = (108, 158, 255, 25)   # акцент с прозрачностью
ACCENT  = (108, 158, 255, 255)  # #6c9eff
TEXT    = "漢"

# Где искать японский шрифт
FONT_CANDIDATES = [
    # Windows
    "C:/Windows/Fonts/YuMincho.ttc",
    "C:/Windows/Fonts/yumin.ttf",
    "C:/Windows/Fonts/yuminl.ttf",
    "C:/Windows/Fonts/msgothic.ttc",
    "C:/Windows/Fonts/msmincho.ttc",
    "C:/Windows/Fonts/meiryo.ttc",
    "C:/Windows/Fonts/BIZ-UDMinchoM.ttc",
    # macOS
    "/System/Library/Fonts/ヒラギノ明朝 ProN.ttc",
    "/System/Library/Fonts/Hiragino Mincho ProN.ttc",
    "/Library/Fonts/Osaka.ttf",
    # Linux
    "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
    "/usr/share/fonts/truetype/fonts-japanese-mincho.ttf",
    "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
]

def find_font():
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            return p
    return None

def make_icon(size, mode, out_path):
    """mode: 'normal' — скруглённый квадрат с фоном;
             'maskable' — сплошной фон с запасом по краям."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    if mode == "normal":
        # Скруглённый квадрат
        radius = int(size * 0.22)
        bg = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(bg)
        d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=BG)
        img = Image.alpha_composite(img, bg)
    else:
        # Сплошной фон (для maskable)
        bg = Image.new("RGBA", (size, size), BG)
        img = Image.alpha_composite(img, bg)

    draw = ImageDraw.Draw(img)

    # Полупрозрачный круг в центре
    margin = int(size * 0.12)
    draw.ellipse([margin, margin, size - margin, size - margin], fill=CIRCLE)

    # Кандзи
    font_path = find_font()
    if not font_path:
        raise SystemExit(
            "Не найден японский шрифт.\n"
            "Windows: проверь C:/Windows/Fonts/ — там должны быть YuMincho.ttc, msgothic.ttc или meiryo.ttc.\n"
            "Если их нет — установи японский языковой пакет Windows."
        )

    # Для maskable-safe-area кандзи чуть меньше
    font_ratio = 0.50 if mode == "maskable" else 0.62
    font_size = int(size * font_ratio)
    font = ImageFont.truetype(font_path, font_size)

    bbox = draw.textbbox((0, 0), TEXT, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (size - tw) / 2 - bbox[0]
    y = (size - th) / 2 - bbox[1]

    draw.text((x, y), TEXT, font=font, fill=ACCENT)

    img.save(out_path)
    print(f"  ✓ {out_path} ({size}×{size}) [{mode}]")

print("Генерирую иконки...")
for name, (size, mode) in ICONS.items():
    make_icon(size, mode, name)
print("\nГотово! Все PNG лежат рядом со скриптом.")