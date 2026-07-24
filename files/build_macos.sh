#!/bin/bash
# Сборка macOS-приложения (.app) из GUI-версии конвертера.
# Запускать ТОЛЬКО на macOS.
set -e

echo "Устанавливаю зависимости..."
pip3 install -r requirements.txt
pip3 install pyinstaller

echo "Собираю приложение..."
pyinstaller --noconfirm --windowed \
    --name "MediaConverter" \
    --add-data "converter_core.py:." \
    gui.py

echo ""
echo "Готово! Приложение находится в dist/MediaConverter.app"
echo ""
echo "ВАЖНО: для конвертации видео/аудио положите бинарник ffmpeg"
echo "внутрь dist/MediaConverter.app/Contents/MacOS/ (рядом с исполняемым файлом),"
echo "скачав его через 'brew install ffmpeg' и скопировав бинарник,"
echo "либо со страницы https://evermeet.cx/ffmpeg/"
