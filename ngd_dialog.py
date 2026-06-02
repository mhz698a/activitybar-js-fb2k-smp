# ng_downloader_dialog.py
import os
import re
import sys
import ctypes
from pathlib import Path
from PyQt6 import QtCore, QtWidgets
from PyQt6.QtGui import QIcon
from pyutils.ng_worker import NGDownloadWorker

myappid = 'etudetools.newgrounds.donwloader.1.0'
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
APP_DIR = Path(__file__).resolve().parent.as_posix()

def normalize_base_folder(param: str | None) -> str:
    """
    Recibe una carpeta o un archivo.
    Si recibe un archivo, devuelve su carpeta padre.
    Si no existe, intenta crear la carpeta.
    """
    if not param:
        base = Path.cwd()
    else:
        p = Path(param).expanduser().resolve()
        base = p.parent if p.exists() and p.is_file() else p

    base.mkdir(parents=True, exist_ok=True)
    return str(base)

class NGDownloadDialog(QtWidgets.QDialog):
    def __init__(self, base_folder: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Newgrounds Downloader")
        self.resize(640, 320)

        self.base_folder = normalize_base_folder(base_folder)
        self.worker = None
        self.thread = None

        self.input_label = QtWidgets.QLabel("URL o ID:")
        self.input_edit = QtWidgets.QLineEdit()
        self.input_edit.setPlaceholderText("Pega una URL de Newgrounds o solo el ID")

        self.save_other_cb = QtWidgets.QCheckBox("Guardar en otra ubicación")
        self.save_other_cb.toggled.connect(self._toggle_other_folder)

        self.folder_edit = QtWidgets.QLineEdit(self.base_folder)
        self.folder_edit.setReadOnly(True)
        self.folder_btn = QtWidgets.QPushButton("Elegir carpeta")
        self.folder_btn.clicked.connect(self._choose_folder)

        folder_row = QtWidgets.QHBoxLayout()
        folder_row.addWidget(self.folder_edit, 1)
        folder_row.addWidget(self.folder_btn)

        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        self.log_box = QtWidgets.QPlainTextEdit()
        self.log_box.setReadOnly(True)

        self.clear_logs_btn = QtWidgets.QPushButton("Limpiar logs")
        self.clear_logs_btn.clicked.connect(self.log_box.clear)
        
        self.open_folder_btn = QtWidgets.QPushButton("Abrir carpeta")
        self.open_folder_btn.clicked.connect(self.open_download_folder)

        self.download_btn = QtWidgets.QPushButton("Descargar")
        self.download_btn.clicked.connect(self.start_download)

        bottom_row = QtWidgets.QHBoxLayout()
        bottom_row.addWidget(self.clear_logs_btn)
        bottom_row.addWidget(self.open_folder_btn)
        bottom_row.addStretch(1)
        bottom_row.addWidget(self.download_btn)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.input_label)
        layout.addWidget(self.input_edit)
        layout.addWidget(self.save_other_cb)
        layout.addLayout(folder_row)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.log_box, 1)
        layout.addLayout(bottom_row)

        self._toggle_other_folder(False)
        self._log(f"Carpeta base: {self.base_folder}")

    def _log(self, text: str):
        self.log_box.appendPlainText(text)

    def _toggle_other_folder(self, checked: bool):
        self.folder_edit.setEnabled(checked)
        self.folder_btn.setEnabled(checked)
        if not checked:
            self.folder_edit.setText(self.base_folder)

    def _choose_folder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Elegir carpeta de destino",
            self.folder_edit.text() or self.base_folder,
        )
        if folder:
            self.folder_edit.setText(folder)

    def _target_folder(self) -> str:
        folder = self.folder_edit.text().strip() if self.save_other_cb.isChecked() else self.base_folder
        folder = folder or self.base_folder
        Path(folder).mkdir(parents=True, exist_ok=True)
        return folder

    def _set_busy(self, busy: bool):
        self.download_btn.setEnabled(not busy)
        self.input_edit.setEnabled(not busy)
        self.save_other_cb.setEnabled(not busy)
        self.folder_btn.setEnabled(not busy and self.save_other_cb.isChecked())

    def start_download(self):
        song_input = self.input_edit.text().strip()
        song_id = self.extract_song_id(song_input)
        if not song_id:
            self._log("Entrada vacía.")
            return

        dest_folder = self._target_folder()

        self.progress_bar.setValue(0)
        self._set_busy(True)
        self._log(f"Destino: {dest_folder}")

        self.thread = QtCore.QThread(self)
        self.worker = NGDownloadWorker(task_id=1, song_id=song_id, dest_path=dest_folder)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.started.connect(lambda: self._log("Proceso iniciado."))
        self.worker.log.connect(self._log)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.failed.connect(self.on_failed)

        self.worker.finished.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def on_progress(self, downloaded: int, total: int):
        if total > 0:
            pct = int((downloaded / total) * 100)
            self.progress_bar.setValue(min(100, max(0, pct)))
        else:
            self.progress_bar.setRange(0, 0)

    def on_finished(self, result: dict):
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100 if not result.get("cancelled") else 0)
        self._set_busy(False)

    def on_failed(self, message: str):
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self._set_busy(False)
        self._log(f"Error: {message}")

    def open_download_folder(self):
        folder = self._target_folder()
        os.startfile(folder)

    def extract_song_id(self, value):
        value = value.strip()

        if value.isdigit():
            return value

        m = re.search(r"/audio/listen/(\d+)", value)
        if m:
            return m.group(1)

        return None


def main():
    icon_path = f"{APP_DIR}/assets/newgrounds.ico"
    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QIcon(icon_path)) 
    
    base_param = sys.argv[1] if len(sys.argv) > 1 else None
    base_folder = normalize_base_folder(base_param)
    
    dlg = NGDownloadDialog(base_folder)
    dlg.setWindowIcon(QIcon(icon_path))
    dlg.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()