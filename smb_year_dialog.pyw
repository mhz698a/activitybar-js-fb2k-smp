from __future__ import annotations

import ctypes
import html
import os
import sys
from pathlib import Path

from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QIcon, QTextCursor
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
)

from pyutils.windows_share_manager import WindowsShareManager

# App ID for Taskbar Icon
MY_APP_ID = 'etudetools.smb.share_dialog.1.0'
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(MY_APP_ID)

APP_DIR = Path(__file__).resolve().parent.as_posix()
ICON_PATH = f"{APP_DIR}/assets/mpc.ico"

class SMBWorker(QObject):
    log = pyqtSignal(str, str)  # message, type (info, success, error)
    finished = pyqtSignal()
    failed = pyqtSignal(str)

    def __init__(self, folder_path: str, share_name: str):
        super().__init__()
        self.folder_path = folder_path
        self.share_name = share_name
        self.manager = WindowsShareManager()

    @pyqtSlot()
    def check_status(self):
        try:
            self.log.emit(f"Comprobando estado de '{self.share_name}'...", "info")
            if self.manager.existe_carpeta_compartida(self.share_name):
                details = self.manager.obtener_detalles_carpeta_compartida(self.share_name)
                share = details.get("share")
                access = details.get("access", [])

                if share:
                    self.log.emit(f"Recurso compartido encontrado:", "success")
                    self.log.emit(f"  Nombre: {share.get('nombre')}", "info")
                    self.log.emit(f"  Ruta: {share.get('ruta')}", "info")
                    self.log.emit(f"  Descripción: {share.get('descripcion') or '(sin descripción)'}", "info")
                    self.log.emit(f"  Estado: {share.get('estado')}", "info")

                if access:
                    self.log.emit("Permisos SMB:", "info")
                    for acc in access:
                        self.log.emit(f"  - {acc.get('account_name')}: {acc.get('access_right')} ({acc.get('access_control_type')})", "info")
            else:
                self.log.emit(f"La carpeta no está compartida como '{self.share_name}'.", "info")
        except Exception as e:
            err_msg = str(e)
            self.log.emit(f"Error al comprobar estado: {err_msg}", "error")
            self.failed.emit(err_msg)
        finally:
            self.finished.emit()

    @pyqtSlot()
    def share_read(self):
        try:
            if self.manager.existe_carpeta_compartida(self.share_name):
                self.log.emit(f"La carpeta ya está compartida como '{self.share_name}'.", "info")
            else:
                self.log.emit(f"Compartiendo '{self.share_name}' con acceso de lectura (Everyone)...", "info")
                self.manager.compartir_carpeta(
                    folder_path=self.folder_path,
                    share_name=self.share_name,
                    read_access=["Everyone"]
                )
                self.log.emit(f"Éxito: Carpeta compartida con acceso de lectura.", "success")
        except Exception as e:
            err_msg = str(e)
            self.log.emit(f"Error al compartir (Lectura): {err_msg}", "error")
            self.failed.emit(err_msg)
        finally:
            self.finished.emit()

    @pyqtSlot()
    def share_full(self):
        try:
            if self.manager.existe_carpeta_compartida(self.share_name):
                self.log.emit(f"El recurso '{self.share_name}' ya existe. Actualizando a acceso total...", "info")
                self.manager.establecer_permisos_carpeta_compartida(
                    share_name=self.share_name,
                    full_access=["Everyone"],
                    remove_existing=True
                )
                self.log.emit(f"Permisos actualizados a acceso total (Everyone).", "success")
            else:
                self.log.emit(f"Compartiendo '{self.share_name}' con acceso total (Everyone)...", "info")
                self.manager.compartir_carpeta(
                    folder_path=self.folder_path,
                    share_name=self.share_name,
                    full_access=["Everyone"]
                )
                self.log.emit(f"Éxito: Carpeta compartida con acceso total.", "success")
        except Exception as e:
            err_msg = str(e)
            self.log.emit(f"Error al compartir (Total): {err_msg}", "error")
            self.failed.emit(err_msg)
        finally:
            self.finished.emit()

    @pyqtSlot()
    def disconnect(self):
        try:
            if not self.manager.existe_carpeta_compartida(self.share_name):
                self.log.emit(f"No existe el recurso compartido '{self.share_name}'.", "info")
            else:
                self.log.emit(f"Eliminando recurso compartido '{self.share_name}'...", "info")
                self.manager.descompartir_carpeta(self.share_name)
                self.log.emit(f"Éxito: Recurso compartido eliminado.", "success")
        except Exception as e:
            err_msg = str(e)
            self.log.emit(f"Error al desconectar: {err_msg}", "error")
            self.failed.emit(err_msg)
        finally:
            self.finished.emit()


class SMBDialog(QDialog):
    def __init__(self, folder_path: str):
        super().__init__()
        self.folder_path = folder_path
        self.share_name = Path(folder_path).name

        self.setWindowTitle(f"SMB Share - {self.share_name}")
        self.setWindowIcon(QIcon(ICON_PATH))
        self.resize(600, 400)

        self.init_ui()

        self.thread = None
        self.worker = None

        # Auto-check status on open
        QtCore.QTimer.singleShot(100, self.on_check_status)

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Log View
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setStyleSheet("background-color: #1e1e1e; color: white; font-family: Consolas, monospace;")
        layout.addWidget(self.log_view)

        # Buttons row
        btn_layout = QHBoxLayout()

        style = self.style()
        uac_icon = style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_VistaShield)
        search_icon = style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileDialogContentsView)

        self.btn_read = QPushButton("Acceso de lectura")
        self.btn_read.setIcon(uac_icon)
        self.btn_read.clicked.connect(self.on_share_read)
        btn_layout.addWidget(self.btn_read)

        self.btn_full = QPushButton("Acceso total")
        self.btn_full.setIcon(uac_icon)
        self.btn_full.clicked.connect(self.on_share_full)
        btn_layout.addWidget(self.btn_full)

        self.btn_status = QPushButton("Comprobar estado")
        self.btn_status.setIcon(search_icon)
        self.btn_status.clicked.connect(self.on_check_status)
        btn_layout.addWidget(self.btn_status)

        self.btn_disconnect = QPushButton("Desconectar")
        self.btn_disconnect.setIcon(uac_icon)
        self.btn_disconnect.clicked.connect(self.on_disconnect)
        btn_layout.addWidget(self.btn_disconnect)

        layout.addLayout(btn_layout)

        # Bottom Close button
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        self.btn_close = QPushButton("Cerrar")
        self.btn_close.clicked.connect(self.close)
        bottom_layout.addWidget(self.btn_close)
        layout.addLayout(bottom_layout)

    def append_log(self, message: str, msg_type: str = "info"):
        color = "#ffffff"  # info (white)
        if msg_type == "success":
            color = "#00ff00"  # success (green)
        elif msg_type == "error":
            color = "#ff0000"  # error (red)

        escaped_msg = html.escape(message).replace("\n", "<br>").replace("  ", "&nbsp;&nbsp;")
        self.log_view.append(f'<span style="color: {color};">{escaped_msg}</span>')
        self.log_view.moveCursor(QTextCursor.MoveOperation.End)

    def set_busy(self, busy: bool):
        self.btn_read.setEnabled(not busy)
        self.btn_full.setEnabled(not busy)
        self.btn_status.setEnabled(not busy)
        self.btn_disconnect.setEnabled(not busy)
        self.btn_close.setEnabled(not busy)

    def run_worker(self, method_name: str):
        if self.thread and self.thread.isRunning():
            return

        self.set_busy(True)
        self.thread = QThread()
        self.worker = SMBWorker(self.folder_path, self.share_name)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(getattr(self.worker, method_name))
        self.worker.log.connect(self.append_log)
        self.worker.failed.connect(lambda msg: None) # Already handled via log signal
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(lambda: self.set_busy(False))

        self.thread.start()

    @pyqtSlot()
    def on_check_status(self):
        self.run_worker("check_status")

    @pyqtSlot()
    def on_share_read(self):
        self.run_worker("share_read")

    @pyqtSlot()
    def on_share_full(self):
        self.run_worker("share_full")

    @pyqtSlot()
    def on_disconnect(self):
        self.run_worker("disconnect")


def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(ICON_PATH))

    if len(sys.argv) < 2:
        QtWidgets.QMessageBox.critical(None, "Error", "Uso: smb_year_dialog.pyw <ruta_carpeta>")
        return

    folder_path = sys.argv[1]

    if not os.path.isdir(folder_path):
        QtWidgets.QMessageBox.critical(None, "Error", f"La ruta no es una carpeta válida:\n{folder_path}")
        return

    dialog = SMBDialog(os.path.abspath(folder_path))
    dialog.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
