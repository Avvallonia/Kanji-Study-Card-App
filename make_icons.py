#!/usr/bin/env python3
"""Генерирует PNG-иконки из icon.svg. Требует: pip install cairosvg"""
import cairosvg

sizes = {
    "icon-192.png": 192,
    "icon-512.png": 512,
    "icon-maskable-512.png": 512,
    "apple-touch-icon.png": 180,   # для iOS
}

for name, size in sizes.items():
    cairosvg.svg2png(
        url="icon.svg",
        write_to=name,
        output_width=size,
        output_height=size,
    )
    print(f"  ✓ {name} ({size}×{size})")

print("\nГотово! Положи PNG-файлы рядом с icon.svg.")
