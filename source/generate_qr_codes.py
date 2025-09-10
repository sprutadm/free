#!/usr/bin/env python3
"""
Скрипт для генерации QR-кодов с ссылками на конфигурации VPN
"""

import os
import qrcode
from PIL import Image

# Создаем папку для QR-кодов в корневой директории, если её нет
# Получаем путь к корневой директории проекта
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
qr_codes_dir = os.path.join(project_root, "qr-codes")

if not os.path.exists(qr_codes_dir):
    os.mkdir(qr_codes_dir)
else:
    # Очищаем папку от старых QR-кодов
    print("🧹 Очищаем папку от старых QR-кодов...")
    for filename in os.listdir(qr_codes_dir):
        if filename.endswith('.png'):
            file_path = os.path.join(qr_codes_dir, filename)
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
    
    # Сохраняем изображение в корневой директории
    filename = os.path.join(qr_codes_dir, f"mariya-{i}.png")
    img.save(filename)
    
    print(f"✅ Создан QR-код: {filename} -> {config_url}")

print("\n🎉 Все QR-коды успешно сгенерированы!")
print("📁 Файлы сохранены в папке: qr-codes/")
