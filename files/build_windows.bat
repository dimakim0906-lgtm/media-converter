@echo off
REM Сборка Windows-приложения (.exe) из GUI-версии конвертера.
REM Запускать ТОЛЬКО на Windows.

echo Устанавливаю зависимости...
pip install -r requirements.txt
pip install pyinstaller

echo Собираю приложение...
pyinstaller --noconfirm --onefile --windowed ^
    --name "MediaConverter" ^
    --add-data "converter_core.py;." ^
    gui.py

echo.
echo Готово! Файл находится в dist\MediaConverter.exe
echo.
echo ВАЖНО: для конвертации видео/аудио положите ffmpeg.exe
echo рядом с MediaConverter.exe (в папку dist), скачав его с
echo https://www.gyan.dev/ffmpeg/builds/ (раздел "release essentials").
pause
