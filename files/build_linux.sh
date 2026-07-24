#!/bin/bash
# Сборка Linux-приложения (исполняемый файл) из GUI-версии конвертера.
set -e

echo "Устанавливаю зависимости..."
pip3 install --break-system-packages -r requirements.txt
pip3 install --break-system-packages pyinstaller

echo "Собираю приложение..."
pyinstaller --noconfirm --onefile \
    --name "MediaConverter" \
    --add-data "converter_core.py:." \
    gui.py

echo ""
echo "Готово! Файл находится в dist/MediaConverter"
echo "Запуск: ./dist/MediaConverter"
echo ""
echo "ВАЖНО: для конвертации видео/аудио положите бинарник ffmpeg"
echo "рядом с dist/MediaConverter, либо установите его системно:"
echo "  sudo apt install ffmpeg"
