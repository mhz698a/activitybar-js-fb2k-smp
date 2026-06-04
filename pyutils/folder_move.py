import os
import re
import shutil
import traceback
from pathlib import Path

from PyQt6.QtCore import Qt, QObject, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QPushButton,
)


def year_prefix(year) -> str:
    y = int(year)
    return f"{y - 2003:02d}."


def strip_year_prefix(name: str) -> str:
    name = str(name or "").strip()
    m = re.match(r"^\d+\.\s*(.*)$", name)
    return m.group(1).strip() if m else name


class YearPickerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Elegir año destino")
        self.resize(230, 280)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Año destino:"))

        self.table = QTableWidget(self)
        years = [str(y) for y in range(2004, Path.cwd().anchor and 9999 or 9999)]  # reemplazado abajo

        from datetime import datetime
        years = [str(y) for y in range(2004, datetime.now().year + 1)]
        columns = 4
        rows = (len(years) + columns - 1) // columns

        self.table.setColumnCount(columns)
        self.table.setRowCount(rows)
        self.table.horizontalHeader().setVisible(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.setShowGrid(False)

        for index, year in enumerate(years):
            row = index // columns
            col = index % columns
            item = QTableWidgetItem(year)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, col, item)

        for col in range(columns):
            self.table.setColumnWidth(col, 50)

        current_year = str(datetime.now().year)
        for r in range(self.table.rowCount()):
            for c in range(self.table.columnCount()):
                item = self.table.item(r, c)
                if item and item.text() == current_year:
                    self.table.setCurrentCell(r, c)
                    break

        layout.addWidget(self.table)

        buttons = QHBoxLayout()
        btn_ok = QPushButton("Aceptar")
        btn_cancel = QPushButton("Cancelar")
        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)
        buttons.addStretch()
        buttons.addWidget(btn_ok)
        buttons.addWidget(btn_cancel)
        layout.addLayout(buttons)

    def selected_year(self):
        item = self.table.currentItem()
        return item.text() if item else None


class FolderMoveWorker(QObject):
    progress = pyqtSignal(int, int, str)
    log = pyqtSignal(str)
    error = pyqtSignal(str)
    finished = pyqtSignal(str, str)

    def __init__(self, source_dir, dest_year, base_root):
        super().__init__()
        self.source_dir = Path(source_dir)
        self.dest_year = str(dest_year)
        self.base_root = Path(base_root)

    def _count_files(self, root: Path) -> int:
        total = 0
        for _, _, files in os.walk(root):
            total += len(files)
        return max(total, 1)

    @pyqtSlot()
    def run(self):
        try:
            if not self.source_dir.exists() or not self.source_dir.is_dir():
                raise FileNotFoundError(f"No existe la carpeta origen: {self.source_dir}")

            src_year = ""
            try:
                src_year = self.source_dir.parents[1].name
            except Exception:
                src_year = ""

            base_name = strip_year_prefix(self.source_dir.name)
            dst_prefix = year_prefix(self.dest_year)

            dest_base = self.base_root / self.dest_year / f"{dst_prefix} music"
            dest_dir = dest_base / f"{dst_prefix} {base_name}"

            if self.source_dir.resolve() == dest_dir.resolve():
                self.log.emit("La carpeta ya está en ese destino.")
                self.finished.emit(src_year, self.dest_year)
                return

            if dest_dir.exists():
                raise FileExistsError(f"Ya existe el destino: {dest_dir}")

            self.log.emit(f"Origen: {self.source_dir}")
            self.log.emit(f"Destino: {dest_dir}")

            total = self._count_files(self.source_dir)
            done = 0

            dest_dir.mkdir(parents=True, exist_ok=False)

            for dirpath, dirnames, filenames in os.walk(self.source_dir):
                rel = Path(dirpath).relative_to(self.source_dir)
                current_target_dir = dest_dir / rel
                current_target_dir.mkdir(parents=True, exist_ok=True)

                for filename in filenames:
                    src_file = Path(dirpath) / filename
                    dst_file = current_target_dir / filename
                    shutil.copy2(src_file, dst_file)
                    done += 1
                    self.progress.emit(done, total, str(src_file))

            shutil.rmtree(self.source_dir)

            self.progress.emit(total, total, str(self.source_dir))
            self.log.emit("Movimiento completado.")
            self.finished.emit(src_year, self.dest_year)

        except Exception:
            self.error.emit(traceback.format_exc())