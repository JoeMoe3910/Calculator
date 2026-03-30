"""Создаёт icon.ico из icon.png с правильными размерами для Windows EXE."""
from PIL import Image
import sys

src = "icon.png"
dst = "icon.ico"

try:
    img = Image.open(src).convert("RGBA")
    print(f"Исходник: {img.size}")

    # Сохраняем ICO, Pillow сам создаст нужные размеры из оригинала
    icon_sizes = [(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)]
    img.save(dst, format="ICO", sizes=icon_sizes)

    import os
    size = os.path.getsize(dst)
    print(f"ICO создан: {dst} ({size} байт)")
    assert size > 10_000, "Файл слишком маленький!"
    print("Готово!")
except Exception as e:
    print(f"ОШИБКА: {e}")
    sys.exit(1)
