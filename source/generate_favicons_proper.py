#!/usr/bin/env python3
"""
Правильный скрипт для создания favicon иконок из insurance.svg
Использует rsvg-convert для качественной конвертации SVG в PNG
"""

import os
import subprocess
import sys

def create_proper_favicons():
    # Получаем путь к корневой директории проекта
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    docs_img_dir = os.path.join(project_root, "docs", "img")
    
    # Путь к исходному SVG файлу
    svg_path = os.path.join(docs_img_dir, "insurance.svg")
    
    if not os.path.exists(svg_path):
        print(f"❌ Файл {svg_path} не найден!")
        return
    
    print(f"📁 Создаем favicon иконки из {svg_path}")
    
    # Размеры для разных иконок
    sizes = {
        "favicon-16x16.png": 16,
        "favicon-32x32.png": 32,
        "apple-touch-icon.png": 180,
        "android-chrome-192x192.png": 192,
        "android-chrome-512x512.png": 512
    }
    
    # Проверяем наличие rsvg-convert
    try:
        subprocess.run(["rsvg-convert", "--version"], 
                      capture_output=True, check=True)
        print("✅ rsvg-convert найден")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ rsvg-convert не найден!")
        print("💡 Установите через Homebrew: brew install librsvg")
        return
    
    # Создаем PNG файлы
    for filename, size in sizes.items():
        output_path = os.path.join(docs_img_dir, filename)
        
        try:
            subprocess.run([
                "rsvg-convert",
                "-w", str(size),
                "-h", str(size),
                svg_path,
                "-o", output_path
            ], check=True)
            print(f"✅ Создан: {filename} ({size}x{size})")
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка при создании {filename}: {e}")
    
    # Создаем site.webmanifest
    manifest_path = os.path.join(docs_img_dir, "site.webmanifest")
    manifest_content = """{
    "name": "Mariya VPN",
    "short_name": "Mariya VPN",
    "icons": [
        {
            "src": "android-chrome-192x192.png",
            "sizes": "192x192",
            "type": "image/png"
        },
        {
            "src": "android-chrome-512x512.png",
            "sizes": "512x512",
            "type": "image/png"
        }
    ],
    "theme_color": "#57a4ff",
    "background_color": "#ffffff",
    "display": "standalone"
}"""
    
    with open(manifest_path, 'w', encoding='utf-8') as f:
        f.write(manifest_content)
    print(f"✅ Создан: site.webmanifest")
    
    print("\n🎉 Все favicon иконки успешно созданы!")

if __name__ == "__main__":
    create_proper_favicons()
