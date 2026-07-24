# Как собрать готовое приложение (.exe / .app / бинарник)

Чтобы человек мог просто **скачать и запустить** программу без установки Python,
собираем её в один исполняемый файл через [PyInstaller](https://pyinstaller.org/).

⚠️ **Важно**: PyInstaller собирает приложение только под ту ОС, на которой запущен.
Собрать `.exe` для Windows можно только на Windows, `.app` для macOS — только на Mac
(либо через виртуалку/CI, например GitHub Actions).

## Готовый Linux-бинарник

В этой поставке уже лежит собранный и проверенный файл `dist/MediaConverter` —
можно скачать и запускать сразу на Linux (`chmod +x MediaConverter && ./MediaConverter`).

## Сборка под Windows

1. Установите Python 3.10+ с [python.org](https://www.python.org/downloads/) (отметьте "Add to PATH").
2. Скопируйте папку проекта на компьютер с Windows.
3. Запустите `build_windows.bat` двойным кликом (или через cmd).
4. Готовый файл появится в `dist\MediaConverter.exe`.
5. **Для видео/аудио**: скачайте ffmpeg (например, сборку "essentials" с
   https://www.gyan.dev/ffmpeg/builds/), возьмите из архива `ffmpeg.exe`
   и положите его **рядом** с `MediaConverter.exe`. Программа сама его найдёт.

## Сборка под macOS

1. Установите Python 3.10+ (`brew install python`, если нет).
2. В терминале: `cd media_converter && chmod +x build_macos.sh && ./build_macos.sh`
3. Готовое приложение появится в `dist/MediaConverter.app`.
4. **Для видео/аудио**: `brew install ffmpeg`, затем скопируйте бинарник
   (`which ffmpeg` покажет путь) внутрь `MediaConverter.app/Contents/MacOS/`.
5. При первом запуске macOS может попросить разрешить запуск приложения
   от неизвестного разработчика (Системные настройки → Конфиденциальность → «Всё равно открыть»).

## Сборка под Linux

```bash
cd media_converter
chmod +x build_linux.sh
./build_linux.sh
```

Готовый файл: `dist/MediaConverter`. Для видео/аудио — либо `sudo apt install ffmpeg`,
либо положить бинарник `ffmpeg` рядом с `MediaConverter`.

## Раздача пользователям

Проще всего — заархивировать папку `dist/` (с exe/app и, если нужно, ffmpeg внутри)
в .zip и отправить/выложить на скачивание. Пользователю не потребуется ни Python,
ни пакеты — только распаковать архив и запустить файл.

Если нужно распространять через много компьютеров или автоматизировать сборку под
все три ОС сразу — можно настроить GitHub Actions с матрицей `windows-latest`,
`macos-latest`, `ubuntu-latest`, которая соберёт все три версии одновременно.
