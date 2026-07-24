#!/usr/bin/env python3
"""
cli.py — консольный конвертер медиаформатов "всё во всё".

Примеры использования:

    # Один файл
    python cli.py photo.heic photo.jpg

    # Целая папка (все картинки -> png)
    python cli.py --batch ./photos --to png

    # Видео в mp3 (аудиодорожка)
    python cli.py movie.mp4 movie.mp3

    # Пакетно, с явным качеством для JPEG/WEBP
    python cli.py --batch ./photos --to jpg --quality 85
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from converter_core import convert_file, detect_kind, IMAGE_EXTENSIONS, AUDIO_EXTENSIONS, VIDEO_EXTENSIONS


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Конвертер медиаформатов: картинки, аудио, видео — локально, без загрузки в интернет.",
    )
    p.add_argument("input", nargs="?", help="Путь к входному файлу (для одиночной конвертации)")
    p.add_argument("output", nargs="?", help="Путь к выходному файлу (для одиночной конвертации)")

    p.add_argument("--batch", metavar="DIR", help="Папка с файлами для пакетной конвертации")
    p.add_argument("--to", metavar="EXT", help="Целевое расширение для пакетной конвертации (например jpg, mp3, mp4)")
    p.add_argument("--out-dir", metavar="DIR", help="Куда складывать результаты пакетной конвертации (по умолчанию: <папка>/converted)")
    p.add_argument("--quality", type=int, default=90, help="Качество для JPEG/WEBP (1-100), по умолчанию 90")
    p.add_argument("--recursive", action="store_true", help="Обходить вложенные папки при --batch")
    return p


def run_single(input_path: Path, output_path: Path, quality: int) -> int:
    if not input_path.exists():
        print(f"Файл не найден: {input_path}", file=sys.stderr)
        return 1

    print(f"Конвертирую: {input_path.name} -> {output_path.name}")
    result = convert_file(
        input_path, output_path, quality=quality,
        progress_cb=lambda line: print(f"  {line}", end="\r") if line else None,
    )
    print()
    if result.success:
        print(f"✔ Готово: {result.output_path}")
        return 0
    print(f"✘ Ошибка: {result.message}", file=sys.stderr)
    return 1


def run_batch(src_dir: Path, to_ext: str, out_dir: Path, quality: int, recursive: bool) -> int:
    if not src_dir.is_dir():
        print(f"Папка не найдена: {src_dir}", file=sys.stderr)
        return 1

    to_ext = to_ext.lower().lstrip(".")
    all_known = IMAGE_EXTENSIONS | AUDIO_EXTENSIONS | VIDEO_EXTENSIONS
    pattern = "**/*" if recursive else "*"
    files = [f for f in src_dir.glob(pattern) if f.is_file() and f.suffix.lower() in all_known]

    if not files:
        print("Не найдено поддерживаемых файлов для конвертации.")
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)
    ok, failed = 0, 0

    for f in files:
        dst = out_dir / (f.stem + "." + to_ext)
        print(f"[{ok + failed + 1}/{len(files)}] {f.name} -> {dst.name}")
        result = convert_file(f, dst, quality=quality)
        if result.success:
            ok += 1
        else:
            failed += 1
            print(f"  ✘ {result.message}", file=sys.stderr)

    print(f"\nГотово: {ok} успешно, {failed} с ошибками. Результаты в: {out_dir}")
    return 0 if failed == 0 else 2


def main() -> int:
    args = build_parser().parse_args()

    if args.batch:
        if not args.to:
            print("Для --batch обязательно укажите --to <расширение>", file=sys.stderr)
            return 1
        src_dir = Path(args.batch).expanduser().resolve()
        out_dir = Path(args.out_dir).expanduser().resolve() if args.out_dir else src_dir / "converted"
        return run_batch(src_dir, args.to, out_dir, args.quality, args.recursive)

    if not args.input or not args.output:
        build_parser().print_help()
        return 1

    return run_single(
        Path(args.input).expanduser().resolve(),
        Path(args.output).expanduser().resolve(),
        args.quality,
    )


if __name__ == "__main__":
    raise SystemExit(main())
