#!/usr/bin/env python3
"""
Скрипт для объединения README.md из частей
"""

import os
import re

def build_readme():
    """Объединяет README.md из частей"""
    
    # Читаем основной файл из docs/
    with open('docs/README.md', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Ищем директивы включения файлов
    pattern = r'<!-- INCLUDE: (.+?) -->'
    
    def replace_include(match):
        filename = match.group(1)
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            return f"<!-- Файл {filename} не найден -->"
    
    # Заменяем директивы включения
    new_content = re.sub(pattern, replace_include, content)
    
    # Записываем результат в корневую папку
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ README.md обновлен из docs/README.md")

if __name__ == "__main__":
    build_readme()
