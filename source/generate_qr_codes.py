#!/usr/bin/env python3
"""
Скрипт для генерации QR-кодов с ссылками на конфигурации VPN
"""

import os
import qrcode
from PIL import Image

# Создаем папки для QR-кодов в корневой директории и в docs, если их нет
# Получаем путь к корневой директории проекта
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
qr_codes_root = os.path.join(project_root, "qr-codes")
qr_codes_docs = os.path.join(project_root, "docs", "qr-codes")

# Создаем папки, если их нет
for qr_dir in [qr_codes_root, qr_codes_docs]:
    if not os.path.exists(qr_dir):
        os.makedirs(qr_dir)
        print(f"📁 Создана папка: {qr_dir}")
    else:
        # Очищаем папку от старых QR-кодов
        print(f"🧹 Очищаем папку от старых QR-кодов: {qr_dir}")
        for filename in os.listdir(qr_dir):
            if filename.endswith('.png'):
                file_path = os.path.join(qr_dir, filename)
                os.remove(file_path)
                print(f"🗑️  Удален: {filename}")

# Базовый URL для вашего репозитория
BASE_URL = "https://github.com/sprutadm/free/raw/refs/heads/main/githubmirror"

# Генерируем QR-коды для всех 25 конфигураций
for i in range(1, 26):
    # URL конфигурации
    config_url = f"{BASE_URL}/mariya-{i}.txt"
    
    # Создаем QR-код с минимальными отступами
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=12,  # Размер ячейки для получения ~400px
        border=1,     # Минимальный отступ
    )
    qr.add_data(config_url)
    qr.make(fit=True)
    
    # Создаем изображение
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Обрезаем лишние отступы
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
    
    # Сохраняем изображение в обе папки
    filename_root = os.path.join(qr_codes_root, f"mariya-{i}.png")
    filename_docs = os.path.join(qr_codes_docs, f"mariya-{i}.png")
    
    img.save(filename_root)
    img.save(filename_docs)
    
    print(f"✅ Создан QR-код: mariya-{i}.png -> {config_url}")

print("\n🎉 Все QR-коды успешно сгенерированы!")
print("📁 Файлы сохранены в папках:")
print(f"   - {qr_codes_root}")
print(f"   - {qr_codes_docs}")
