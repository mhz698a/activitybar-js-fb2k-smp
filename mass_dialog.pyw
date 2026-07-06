import sys
import os
import traceback
import ctypes
from pathlib import Path
from PyQt6 import QtWidgets, QtCore, QtGui
from mutagen.id3 import ID3, TALB, TPE1, ID3NoHeaderError
from mutagen.mp4 import MP4
from pyutils.wctime import setctime_blocking

# App ID for Taskbar Icon (following repository convention)
MY_APP_ID = 'etudetools.files_mgr.mass_dialog.1.0'
try:
    if sys.platform == 'win32':
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(MY_APP_ID)
except Exception:
    pass

APP_DIR = Path(__file__).resolve().parent.as_posix()
ICON_PATH = f"{APP_DIR}/assets/mpc.ico"
TXT_RUTAS = r"C:\Users\miche\OneDrive\foobar2000\profile\foobar_selection.txt"

def exception_hook(exctype, value, tb):
    """Global exception handler to show traceback in a QMessageBox."""
    err_msg = "".join(traceback.format_exception(exctype, value, tb))
    # Ensure there is a QApplication instance
    if not QtWidgets.QApplication.instance():
        app = QtWidgets.QApplication(sys.argv)
    QtWidgets.QMessageBox.critical(None, "Error Crítico", f"Se ha producido un error inesperado:\n\n{err_msg}")
    sys.exit(1)

sys.excepthook = exception_hook

class MassWorker(QtCore.QObject):
    finished = QtCore.pyqtSignal(bool)
    error = QtCore.pyqtSignal(str)
    locked_file = QtCore.pyqtSignal(str)
    progress = QtCore.pyqtSignal(int, int)

    def __init__(self, files, album_val, artist_val):
        super().__init__()
        self.files = files # list of tuples (path, album, artist)
        self.album_val = album_val
        self.artist_val = artist_val

    def run(self):
        all_success = True
        try:
            total = len(self.files)
            for i, (file_path, _, _) in enumerate(self.files):
                try:
                    # Save mtime and atime
                    stat = os.stat(file_path)
                    mtime = stat.st_mtime
                    atime = stat.st_atime
                    ctime = getattr(stat, 'st_ctime', mtime)

                    ext = os.path.splitext(file_path)[1].lower()
                    
                    if ext == '.mp3':
                        try:
                            audio = ID3(file_path)
                        except ID3NoHeaderError:
                            audio = ID3()
                        
                        if self.album_val is not None:
                            audio.add(TALB(encoding=3, text=self.album_val))
                        if self.artist_val is not None:
                            audio.add(TPE1(encoding=3, text=self.artist_val))
                        
                        if not getattr(audio, 'filename', None):
                             audio.save(file_path)
                        else:
                             audio.save()

                    elif ext in ['.mp4', '.m4a', '.m4v']:
                        audio = MP4(file_path)
                        if self.album_val is not None:
                            audio["\xa9alb"] = [self.album_val]
                        if self.artist_val is not None:
                            audio["\xa9ART"] = [self.artist_val]
                        audio.save()
                    
                    # Restore mtime
                    os.utime(file_path, (atime, mtime))
                    setctime_blocking(file_path, ctime)
                    
                except PermissionError:
                    all_success = False
                    self.locked_file.emit(f"Archivo en uso: {os.path.basename(file_path)}")
                except Exception as e:
                    # For other errors, we report them
                    raise e
                
                self.progress.emit(i + 1, total)
            
            self.finished.emit(all_success)
        except Exception:
            self.error.emit(traceback.format_exc())

class MassDialog(QtWidgets.QDialog):
    def __init__(self, files):
        super().__init__()
        self.files = files # list of tuples (path, album, artist)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Asignación masiva de etiquetas")
        if os.path.exists(ICON_PATH):
            self.setWindowIcon(QtGui.QIcon(ICON_PATH))
        self.resize(800, 500)
        self.setModal(False)

        layout = QtWidgets.QVBoxLayout(self)

        # File list view
        self.file_list_text = QtWidgets.QTextEdit()
        self.file_list_text.setReadOnly(True)
        
        display_lines = []
        for path, alb, art in self.files:
            display_lines.append(f'{path} ["{alb}", "{art}"]')

        self.file_list_text.setPlainText("\n".join(display_lines))
        
        layout.addWidget(QtWidgets.QLabel("Archivos a procesar:"))
        layout.addWidget(self.file_list_text)

        # Album row
        album_layout = QtWidgets.QHBoxLayout()
        self.album_cb = QtWidgets.QCheckBox("Álbum")
        self.album_input = QtWidgets.QLineEdit()
        album_layout.addWidget(self.album_cb)
        album_layout.addWidget(self.album_input)
        layout.addLayout(album_layout)

        # Artist row
        artist_layout = QtWidgets.QHBoxLayout()
        self.artist_cb = QtWidgets.QCheckBox("Artista")
        self.artist_input = QtWidgets.QLineEdit()
        artist_layout.addWidget(self.artist_cb)
        artist_layout.addWidget(self.artist_input)
        layout.addLayout(artist_layout)

        # Buttons
        btn_layout = QtWidgets.QHBoxLayout()
        self.apply_btn = QtWidgets.QPushButton("Aplicar")
        self.cancel_btn = QtWidgets.QPushButton("Cancelar")
        btn_layout.addStretch()
        btn_layout.addWidget(self.apply_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        # Status bar
        self.status_bar = QtWidgets.QStatusBar()
        layout.addWidget(self.status_bar)

        # Connections
        self.apply_btn.clicked.connect(self.on_apply)
        self.cancel_btn.clicked.connect(self.close)

        self.clear_status_timer = QtCore.QTimer()
        self.clear_status_timer.setSingleShot(True)
        self.clear_status_timer.timeout.connect(self.clear_status_bar)

    def on_apply(self):
        album_checked = self.album_cb.isChecked()
        artist_checked = self.artist_cb.isChecked()

        if not album_checked and not artist_checked:
            self.status_bar.showMessage("Selecciona al menos una etiqueta para aplicar.", 3000)
            return

        if album_checked and not self.album_input.text().strip():
            self.status_bar.showMessage("El valor de Álbum no puede estar vacío.", 3000)
            return
        
        if artist_checked and not self.artist_input.text().strip():
            self.status_bar.showMessage("El valor de Artista no puede estar vacío.", 3000)
            return

        album_val = self.album_input.text() if album_checked else None
        artist_val = self.artist_input.text() if artist_checked else None

        self.set_busy(True)
        
        self.thread = QtCore.QThread()
        self.worker = MassWorker(self.files, album_val, artist_val)
        self.worker.moveToThread(self.thread)
        
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_worker_error)
        self.worker.locked_file.connect(self.on_locked_file)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def set_busy(self, busy):
        self.apply_btn.setEnabled(not busy)
        self.album_cb.setEnabled(not busy)
        self.artist_cb.setEnabled(not busy)
        self.album_input.setEnabled(not busy)
        self.artist_input.setEnabled(not busy)
        self.cancel_btn.setEnabled(not busy)

    def on_finished(self, success):
        if success:
            self.close()
        else:
            self.set_busy(False)

    def on_worker_error(self, err_traceback):
        QtWidgets.QMessageBox.critical(
            self, "Error", f"Ocurrió un error durante el proceso:\n\n{err_traceback}")
        self.set_busy(False)

    def on_locked_file(self, message):
        self.status_bar.showMessage(message)
        self.status_bar.setStyleSheet("background-color: yellow;")
        self.clear_status_timer.start(5000)

    def clear_status_bar(self):
        self.status_bar.clearMessage()
        self.status_bar.setStyleSheet("")

def get_metadata(file_path):
    album = ""
    artist = ""
    ext = os.path.splitext(file_path)[1].lower()
    try:
        if ext == '.mp3':
            try:
                audio = ID3(file_path)
                if 'TALB' in audio:
                    album = str(audio['TALB'])
                if 'TPE1' in audio:
                    artist = str(audio['TPE1'])
            except ID3NoHeaderError:
                pass
        elif ext in ['.mp4', '.m4a', '.m4v']:
            audio = MP4(file_path)
            if "\xa9alb" in audio:
                album = audio["\xa9alb"][0]
            if "\xa9ART" in audio:
                artist = audio["\xa9ART"][0]
    except Exception:
        pass
    return album, artist

def load_files(file_path):
    if not os.path.exists(file_path):
        QtWidgets.QMessageBox.critical(None, "Error", f"El archivo '{file_path}' no existe.")
        sys.exit(1)

    content = None
    # Try UTF-8 (and strip BOM)
    try:
        # Use 'utf-8-sig' to automatically handle BOM if present
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()
    except UnicodeDecodeError:
        # Try CP1252
        try:
            with open(file_path, 'r', encoding='cp1252') as f:
                content = f.read()
                # Manually strip BOM if present in CP1252
                if content.startswith('\ufeff'):
                    content = content[1:]
        except Exception:
            raise

    if content is None:
        return []

    lines = content.splitlines()
    valid_files_data = []
    supported_exts = ['.mp3', '.mp4', '.m4a', '.m4v']
    
    for line in lines:
        line = line.strip()
        # Remove any leading \ufeff
        line = line.lstrip('\ufeff')
        if not line:
            continue
        if os.path.isfile(line):
            ext = os.path.splitext(line)[1].lower()
            if ext in supported_exts:
                abs_path = os.path.abspath(line)
                alb, art = get_metadata(abs_path)
                valid_files_data.append((abs_path, alb, art))
    
    return valid_files_data

def main():
    app = QtWidgets.QApplication(sys.argv)
    
    if len(sys.argv) < 2:
        txt_path = TXT_RUTAS
    else:
        txt_path = sys.argv[1]
    
    try:
        files = load_files(txt_path)
    except Exception:
        err_msg = traceback.format_exc()
        
        # 1. Crear la instancia del cuadro de diálogo
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Icon.Critical)
        msg.setWindowTitle("Error de Lectura")
        
        # 2. Separar el mensaje amigable del error técnico
        msg.setText("Error al leer el archivo de entrada.")
        msg.setInformativeText("Haz clic en 'Show Details...' para ver el error técnico.")
        msg.setDetailedText(err_msg) # Aquí se guarda el traceback
        
        # 3. Mostrar la ventana
        msg.exec()
        return

    if not files:
        QtWidgets.QMessageBox.information(None, "Sin archivos", "No se encontraron archivos válidos para procesar.")
        return

    dialog = MassDialog(files)
    dialog.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
