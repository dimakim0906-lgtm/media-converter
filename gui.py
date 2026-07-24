#!/usr/bin/env python3
"""
gui.py — простой графический интерфейс конвертера медиаформатов (PyQt6).

Запуск:
    python gui.py

Требует: PyQt6, Pillow, pillow-heif, а для видео/аудио — установленный ffmpeg.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QComboBox, QSpinBox, QFileDialog, QProgressBar, QMessageBox,
    QListWidgetItem,
)

from converter_core import convert_file, detect_kind, IMAGE_EXTENSIONS, AUDIO_EXTENSIONS, VIDEO_EXTENSIONS

ALL_TARGET_FORMATS = {
    "image": ["jpg", "png", "webp", "bmp", "tiff", "gif"],
    "audio": ["mp3", "wav", "flac", "aac", "ogg", "m4a"],
    "video": ["mp4", "mov", "mkv", "webm", "avi"],
}


class ConvertWorker(QThread):
    progress = pyqtSignal(int, str)   # индекс файла, сообщение
    finished_all = pyqtSignal(int, int)  # ok, failed

    def __init__(self, files: list[Path], target_ext: str, out_dir: Path, quality: int):
        super().__init__()
        self.files = files
        self.target_ext = target_ext
        self.out_dir = out_dir
        self.quality = quality

    def run(self):
        ok, failed = 0, 0
        for i, f in enumerate(self.files):
            dst = self.out_dir / (f.stem + "." + self.target_ext)
            result = convert_file(f, dst, quality=self.quality)
            if result.success:
                ok += 1
                self.progress.emit(i, f"✔ {f.name} -> {dst.name}")
            else:
                failed += 1
                self.progress.emit(i, f"✘ {f.name}: {result.message}")
        self.finished_all.emit(ok, failed)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Конвертер медиаформатов — всё во всё")
        self.resize(560, 480)
        self.setAcceptDrops(True)

        self.files: list[Path] = []
        self.out_dir: Path | None = None

        layout = QVBoxLayout(self)

        hint = QLabel(
            "Перетащите файлы сюда или нажмите «Добавить файлы».\n"
            "Поддерживаются картинки (в т.ч. HEIC), аудио и видео. Всё локально."
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        btn_row = QHBoxLayout()
        self.add_btn = QPushButton("Добавить файлы")
        self.add_btn.clicked.connect(self.add_files)
        self.clear_btn = QPushButton("Очистить список")
        self.clear_btn.clicked.connect(self.clear_files)
        btn_row.addWidget(self.add_btn)
        btn_row.addWidget(self.clear_btn)
        layout.addLayout(btn_row)

        options_row = QHBoxLayout()
        options_row.addWidget(QLabel("Формат назначения:"))
        self.format_combo = QComboBox()
        options_row.addWidget(self.format_combo)

        options_row.addWidget(QLabel("Качество:"))
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(1, 100)
        self.quality_spin.setValue(90)
        options_row.addWidget(self.quality_spin)
        layout.addLayout(options_row)

        self.out_dir_label = QLabel("Папка результата: не выбрана (будет рядом с исходными файлами)")
        self.out_dir_label.setWordWrap(True)
        layout.addWidget(self.out_dir_label)

        out_dir_btn = QPushButton("Выбрать папку для результата")
        out_dir_btn.clicked.connect(self.choose_out_dir)
        layout.addWidget(out_dir_btn)

        self.convert_btn = QPushButton("Конвертировать")
        self.convert_btn.clicked.connect(self.start_conversion)
        layout.addWidget(self.convert_btn)

        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

    # --- Drag & drop ---
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = [Path(u.toLocalFile()) for u in event.mimeData().urls()]
        self._add_paths(paths)

    # --- File handling ---
    def add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Выберите файлы")
        self._add_paths([Path(p) for p in paths])

    def _add_paths(self, paths: list[Path]):
        for p in paths:
            if p.is_file() and p not in self.files:
                self.files.append(p)
                self.list_widget.addItem(QListWidgetItem(str(p)))
        self._refresh_format_options()

    def clear_files(self):
        self.files.clear()
        self.list_widget.clear()
        self.format_combo.clear()

    def choose_out_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Папка для результатов")
        if d:
            self.out_dir = Path(d)
            self.out_dir_label.setText(f"Папка результата: {d}")

    def _refresh_format_options(self):
        self.format_combo.clear()
        if not self.files:
            return
        kinds = {detect_kind(f) for f in self.files}
        if len(kinds) == 1:
            kind = kinds.pop()
            options = ALL_TARGET_FORMATS.get(kind, [])
        else:
            # Смешанные типы — покажем объединённый список
            options = sorted({fmt for k in kinds for fmt in ALL_TARGET_FORMATS.get(k, [])})
        self.format_combo.addItems(options)

    # --- Conversion ---
    def start_conversion(self):
        if not self.files:
            QMessageBox.warning(self, "Нет файлов", "Сначала добавьте файлы для конвертации.")
            return
        target_ext = self.format_combo.currentText()
        if not target_ext:
            QMessageBox.warning(self, "Нет формата", "Выберите формат назначения.")
            return

        out_dir = self.out_dir or self.files[0].parent / "converted"
        out_dir.mkdir(parents=True, exist_ok=True)

        self.progress_bar.setRange(0, len(self.files))
        self.progress_bar.setValue(0)
        self.convert_btn.setEnabled(False)
        self.status_label.setText("Конвертация запущена...")

        self.worker = ConvertWorker(self.files, target_ext, out_dir, self.quality_spin.value())
        self.worker.progress.connect(self.on_progress)
        self.worker.finished_all.connect(self.on_finished)
        self.worker.start()

    def on_progress(self, index: int, message: str):
        self.progress_bar.setValue(index + 1)
        self.status_label.setText(message)

    def on_finished(self, ok: int, failed: int):
        self.convert_btn.setEnabled(True)
        self.status_label.setText(f"Готово: {ok} успешно, {failed} с ошибками.")
        QMessageBox.information(self, "Конвертация завершена", f"Успешно: {ok}\nС ошибками: {failed}")


def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
