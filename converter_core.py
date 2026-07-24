"""
converter_core.py
Ядро универсального конвертера медиафайлов.

Поддерживает:
- Картинки: HEIC/HEIF, JPG, PNG, WEBP, BMP, TIFF, GIF  (через Pillow + pillow-heif)
- Видео/Аудио: mp4, mov, mkv, avi, webm, mp3, wav, flac, aac, ogg и т.д. (через ffmpeg)

Всё выполняется локально, без загрузки файлов куда-либо.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional


def _app_base_dir() -> Path:
    """Папка, где лежит приложение (учитывает сборку через PyInstaller)."""
    if getattr(sys, "frozen", False):
        # PyInstaller onefile: временная папка с ресурсами
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass)
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


def _bundled_ffmpeg_path() -> Optional[Path]:
    """Ищет ffmpeg рядом с приложением (bin/ffmpeg, bin/ffmpeg.exe, ffmpeg рядом)."""
    base = _app_base_dir()
    exe_name = "ffmpeg.exe" if sys.platform.startswith("win") else "ffmpeg"
    candidates = [
        base / exe_name,
        base / "bin" / exe_name,
        base / "ffmpeg" / exe_name,
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None

# --- Ленивая проверка/регистрация HEIC-плагина для Pillow ---
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    HEIC_SUPPORTED = True
except ImportError:
    HEIC_SUPPORTED = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif",
    ".gif", ".heic", ".heif",
}

AUDIO_EXTENSIONS = {
    ".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma", ".opus",
}

VIDEO_EXTENSIONS = {
    ".mp4", ".mov", ".mkv", ".avi", ".webm", ".flv", ".wmv", ".m4v",
}


class ConversionError(Exception):
    """Ошибка конвертации файла."""


@dataclass
class ConversionResult:
    success: bool
    input_path: Path
    output_path: Optional[Path]
    message: str = ""


def detect_kind(path: Path) -> str:
    """Определяет тип файла: 'image', 'audio', 'video' или 'unknown'."""
    ext = path.suffix.lower()
    if ext in IMAGE_EXTENSIONS:
        return "image"
    if ext in AUDIO_EXTENSIONS:
        return "audio"
    if ext in VIDEO_EXTENSIONS:
        return "video"
    return "unknown"


def get_ffmpeg_command() -> Optional[str]:
    """Возвращает путь к ffmpeg: сначала рядом с приложением, потом системный PATH."""
    bundled = _bundled_ffmpeg_path()
    if bundled:
        return str(bundled)
    system = shutil.which("ffmpeg")
    return system


def ffmpeg_available() -> bool:
    return get_ffmpeg_command() is not None


# --------------------------------------------------------------------------
# Картинки
# --------------------------------------------------------------------------

def convert_image(
    src: Path,
    dst: Path,
    quality: int = 90,
) -> ConversionResult:
    """
    Конвертирует изображение (включая HEIC/HEIF) в целевой формат,
    определяемый расширением dst.
    """
    if not PIL_AVAILABLE:
        return ConversionResult(
            False, src, None,
            "Pillow не установлен. Выполните: pip install Pillow pillow-heif",
        )

    ext = src.suffix.lower()
    if ext in {".heic", ".heif"} and not HEIC_SUPPORTED:
        return ConversionResult(
            False, src, None,
            "Для HEIC/HEIF нужен пакет pillow-heif. Выполните: pip install pillow-heif",
        )

    try:
        img = Image.open(src)
        target_ext = dst.suffix.lower()

        # JPEG не поддерживает альфа-канал/палитру — конвертируем в RGB
        if target_ext in {".jpg", ".jpeg"} and img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGB")

        dst.parent.mkdir(parents=True, exist_ok=True)

        save_kwargs = {}
        if target_ext in {".jpg", ".jpeg", ".webp"}:
            save_kwargs["quality"] = quality
        if target_ext in {".jpg", ".jpeg"}:
            save_kwargs["optimize"] = True

        img.save(dst, **save_kwargs)
        return ConversionResult(True, src, dst, "OK")
    except Exception as e:  # noqa: BLE001
        return ConversionResult(False, src, None, f"Ошибка: {e}")


# --------------------------------------------------------------------------
# Видео / Аудио (через системный ffmpeg)
# --------------------------------------------------------------------------

def convert_media(
    src: Path,
    dst: Path,
    extra_args: Optional[list[str]] = None,
    progress_cb: Optional[Callable[[str], None]] = None,
) -> ConversionResult:
    """
    Конвертирует аудио/видео файл через ffmpeg.
    extra_args — дополнительные флаги ffmpeg (например ["-b:a", "192k"]).
    """
    ffmpeg_cmd = get_ffmpeg_command()
    if not ffmpeg_cmd:
        return ConversionResult(
            False, src, None,
            "ffmpeg не найден. Установите его: "
            "https://ffmpeg.org/download.html "
            "(Windows: choco install ffmpeg / winget install ffmpeg; "
            "macOS: brew install ffmpeg; Linux: apt install ffmpeg) "
            "— или положите ffmpeg рядом с приложением.",
        )

    dst.parent.mkdir(parents=True, exist_ok=True)
    cmd = [ffmpeg_cmd, "-y", "-i", str(src)]
    if extra_args:
        cmd += extra_args
    cmd.append(str(dst))

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert process.stdout is not None
        for line in process.stdout:
            if progress_cb:
                progress_cb(line.strip())
        process.wait()

        if process.returncode == 0 and dst.exists():
            return ConversionResult(True, src, dst, "OK")
        return ConversionResult(
            False, src, None,
            f"ffmpeg завершился с кодом {process.returncode}",
        )
    except Exception as e:  # noqa: BLE001
        return ConversionResult(False, src, None, f"Ошибка: {e}")


# --------------------------------------------------------------------------
# Единая точка входа
# --------------------------------------------------------------------------

def convert_file(
    src: Path,
    dst: Path,
    quality: int = 90,
    extra_ffmpeg_args: Optional[list[str]] = None,
    progress_cb: Optional[Callable[[str], None]] = None,
) -> ConversionResult:
    """Определяет тип файла и вызывает нужный конвертер."""
    kind = detect_kind(src)
    if kind == "image":
        return convert_image(src, dst, quality=quality)
    if kind in ("audio", "video"):
        return convert_media(src, dst, extra_args=extra_ffmpeg_args, progress_cb=progress_cb)
    return ConversionResult(False, src, None, f"Неизвестный/неподдерживаемый формат: {src.suffix}")
