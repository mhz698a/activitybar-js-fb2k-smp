import ctypes
from pathlib import Path
import sys
import os
import shutil
import argparse
from datetime import datetime
import traceback
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QPlainTextEdit, QPushButton, QLabel
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5 import QtGui
import pywinstyles
import requests


# ==========================
# CONFIGURACIÓN FIJA
# ==========================
TXT_RUTAS = r"C:\Users\miche\OneDrive\foobar2000\profile\\foobar_selection.txt"
CARPETA_PAPELERA = r"E:\_Exclude\l_reallydeleted"
APP_DIR = Path(__file__).resolve().parent.as_posix()
ICON_WIN = f"{APP_DIR}/assets/mpc.ico"

# ==========================
# REQUEST POST COMMANDS
# ==========================

BEERWEB = "http://localhost:8880"

# ==========================
# Windows AppID (taskbar icon grouping)
# ==========================
myappid = 'etude_moving.fb2k_ownfileoperations.file_deletinons.v1'
try: 
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception: 
    pass


# ==========================
# QSS TEMA OSCURO
# ==========================
QSS_DARK = """
QWidget {
    background-color: #1e1e1e;
    color: #d4d4d4;
    font-family: Segoe UI;
    font-size: 10pt;
}

QPlainTextEdit {
    background-color: #252526;
    border: 1px solid #3c3c3c;
    padding: 6px;
}

QPushButton {
    background-color: #333333;
    border: 1px solid #3c3c3c;
    padding: 6px 14px;
}

QPushButton:hover {
    background-color: #3f3f3f;
}

QPushButton:pressed {
    background-color: #2a2a2a;
}

QTabWidget::pane {
    border: 1px solid #3c3c3c;
}

QTabBar::tab {
    background: #2d2d2d;
    padding: 6px 12px;
}

QTabBar::tab:selected {
    background: #1e1e1e;
}
QPushButton:disabled {
    background-color: #2b2b2b;
    color: #7a7a7a;
    border: 1px solid #444444;
}
QPushButton:disabled:hover {
    background-color: #2b2b2b;
}
"""


# ==========================
# VENTANA PRINCIPAL
# ==========================
class MoveToTrashApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Delete Files (move to recicler bin) - foobar2000")

        # Ventana fija
        self.setFixedSize(720, 480)

        # Si luego quieres permitir redimensionar:
        # self.setMinimumSize(720, 480)
        # self.resize(900, 600)
        
        # Title bar Dark Theme
        pywinstyles.change_header_color(self, color="#232629")

        self.init_ui()
        self.cargar_rutas()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.tab_inicio = QWidget()
        self.tab_resultados = QWidget()

        self.tabs.addTab(self.tab_inicio, "List")
        self.tabs.addTab(self.tab_resultados, "Results")

        self.init_tab_inicio()
        self.init_tab_resultados()
        
        # -------------------------------------------------
        # Pregunta global
        self.lbl_pregunta = QLabel("¿Deseas eliminar (mover a papelera) estos elementos?")
        layout.addWidget(self.lbl_pregunta)

        # Botones globales
        btn_layout = QHBoxLayout()

        self.btn_eliminar = QPushButton("Delete")
        self.btn_eliminar_dup = QPushButton("Delete Duplicate")
        self.btn_cancelar = QPushButton("Close")

        self.btn_eliminar.clicked.connect(self.procesar_archivos)
        self.btn_eliminar_dup.clicked.connect(lambda: self.procesar_archivos(duplicado=True))
        self.btn_cancelar.clicked.connect(self.close)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_eliminar)
        btn_layout.addWidget(self.btn_eliminar_dup)
        btn_layout.addWidget(self.btn_cancelar)

        layout.addLayout(btn_layout)

    # --------------------------
    # TAB INICIO
    # --------------------------
    def init_tab_inicio(self):
        layout = QVBoxLayout(self.tab_inicio)

        label = QLabel("Paths detected:")
        layout.addWidget(label)

        self.txt_rutas = QPlainTextEdit()
        self.txt_rutas.setReadOnly(True)
        self.txt_rutas.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.txt_rutas)


    # --------------------------
    # TAB RESULTADOS
    # --------------------------
    def init_tab_resultados(self):
        layout = QVBoxLayout(self.tab_resultados)

        self.txt_resultados = QPlainTextEdit()
        self.txt_resultados.setReadOnly(True)
        self.txt_resultados.setTextInteractionFlags(Qt.TextSelectableByMouse)

        layout.addWidget(self.txt_resultados)

    # --------------------------
    # CARGA DE RUTAS
    # --------------------------
    def cargar_rutas(self):
        rutas_normalizadas = []
        
        with open(TXT_RUTAS, "r", encoding="utf-8", errors="ignore") as f:
            for linea in f:
                ruta = linea.strip().replace('\ufeff','')
                if not ruta:
                    continue
                rutas_normalizadas.append(os.path.normpath(ruta))

        self.rutas = rutas_normalizadas
        self.txt_rutas.setPlainText("\n".join(self.rutas))
        print("\n".join(self.rutas))

    # --------------------------
    # PROCESAMIENTO
    # --------------------------
    def procesar_archivos(self, duplicado=False):
        self.btn_eliminar.setEnabled(False)
        self.btn_eliminar_dup.setEnabled(False)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        separador = f"\n==== {timestamp} ====\n"
        self.txt_resultados.appendPlainText(separador)

        has_errors = False
        num_trying = 0

        for ruta in self.rutas:
            while True:
                            
                try:
                    if not os.path.exists(ruta):
                        self.log_fallo("NO EXISTE", repr(ruta))
                        has_errors = True
                        continue

                    nombre = os.path.basename(ruta)
                    base, ext = os.path.splitext(nombre)
                    
                    if duplicado:
                        base = f"{base}_duplicated"

                    destino = os.path.join(CARPETA_PAPELERA, base + ext)
                    
                    # -------------------------------------------------
                    # Cambio: si destino existe, buscamos un nombre alternativo
                    # añadiendo '_' al nombre (sin tocar la extensión) hasta que
                    # encontremos uno libre.
                    # -------------------------------------------------
                    if os.path.exists(destino):
                        base, ext = os.path.splitext(nombre)
                        candidate = None
                        suffix = "_"
                        # Intentar con sufijos crecientes ("_", "__", "___", ...)
                        while True:
                            new_name = f"{base}{suffix}{ext}"
                            candidate = os.path.join(CARPETA_PAPELERA, new_name)
                            if not os.path.exists(candidate):
                                # candidato libre encontrado
                                destino = candidate
                                nombre = new_name  # actualizar nombre final (opcional)
                                break
                            # si existe, añadir otro '_' y repetir
                            suffix += "_"

                    # Intentamos mover al destino (sea original o renombrado)
                    shutil.move(ruta, destino)
                    # Loguear indicando si hubo renombrado (comparación simple)
                    self.log_ok(ruta, destino)
                    break
                    
                except PermissionError:
                    num_trying += 1
                    moved_count = len(self.rutas)
                    
                    try:
                        if moved_count > 1:
                            # Detener reproducción si se movieron más de 2 archivos
                            requests.post(f"{BEERWEB}/api/player/stop")
                            # self.txt_resultados.appendPlainText("✔ Playback stopped (moved >2 files)")
                        else:
                            # Pasar al siguiente item si se movieron 1 o 2 archivos
                            requests.post(f"{BEERWEB}/api/player/next")
                            # self.txt_resultados.appendPlainText("✔ Moved to next item")
                    except Exception as e:
                        self.txt_resultados.appendPlainText(f"FAIL controlling playback: {e}")
                    
                    if num_trying > 1:   
                        self.log_fallo("ACCESO DENEGADO", ruta)
                        has_errors = True
                        break
                    
                except Exception as e:
                    self.log_fallo(f"ERROR: {e}", ruta)
                    has_errors = True
                    break

        if not has_errors:
            self.limpiar_dead_items()
            QTimer.singleShot(10, self.close)
        else:
            self.btn_eliminar.setEnabled(True)
            self.btn_eliminar_dup.setEnabled(True)
            self.tabs.setCurrentWidget(self.tab_resultados)

    # --------------------------
    # LIMPIAR DEAD ITEMS (ROBUSTO)
    # --------------------------
    def limpiar_dead_items(self):
        try:
            # 1. Obtener todas las playlists para buscar la "Current" (la seleccionada en pantalla)
            # Esto funciona incluso si la música está en STOP.
            playlists_resp = requests.get(f"{BEERWEB}/api/playlists").json()
            
            target_id = None
            target_title = "Unknown"

            if 'playlists' in playlists_resp:
                for pl in playlists_resp['playlists']:
                    # isCurrent es la flag de la playlist que estás viendo en foobar
                    if pl.get('isCurrent'):
                        target_id = pl['id']
                        target_title = pl.get('title', 'Unknown')
                        break
            
            if not target_id:
                self.txt_resultados.appendPlainText("⚠ No 'Current' playlist found (is Foobar open?)")
                return

            self.txt_resultados.appendPlainText(f"Scanning playlist: '{target_title}' [{target_id}]...")

            # 2. Pedir los items de ESE ID específico
            # Pedimos 0:20000 para cubrir playlists grandes
            url = f"{BEERWEB}/api/playlists/{target_id}/items/0:20000"
            params = {'columns': ['%path%']} # IMPORTANTE: Pedir la columna path
            
            resp = requests.get(url, params=params).json()

            if 'error' in resp:
                self.txt_resultados.appendPlainText(f"⚠ API Error: {resp['error'].get('message')}")
                return

            # 3. Extraer items
            items = []
            if "playlistItems" in resp and "items" in resp["playlistItems"]:
                items = resp["playlistItems"]["items"]
            elif "items" in resp:
                items = resp["items"]

            # 4. Buscar índices de archivos que NO existen en disco
            indices_to_remove = []
            
            for index, item in enumerate(items):
                path = None
                # Beefweb devuelve las columnas en una lista
                if "columns" in item and len(item["columns"]) > 0:
                    path = item["columns"][0]
                
                # Si tenemos ruta pero el archivo no existe -> a la lista de borrar
                if path and not os.path.exists(path):
                    indices_to_remove.append(index)

            if not indices_to_remove:
                self.txt_resultados.appendPlainText("✔ No dead items found in current playlist.")
                return

            # 5. Ejecutar borrado
            payload = {"items": indices_to_remove}
            del_url = f"{BEERWEB}/api/playlists/{target_id}/items/remove"
            del_resp = requests.post(del_url, json=payload)
            
            if del_resp.status_code in [200, 204]:
                self.txt_resultados.appendPlainText(f"✔ Cleaned {len(indices_to_remove)} dead items.")
            else:
                self.txt_resultados.appendPlainText(f"⚠ Delete failed. Code: {del_resp.status_code}")

        except Exception:
            self.txt_resultados.appendPlainText(f"FAIL cleaning dead items: {traceback.format_exc()}")
    
    # --------------------------
    # LOGS
    # --------------------------
    def log_ok(self, origen, destino):
        self.txt_resultados.appendPlainText(
            f"OK: {origen} -> {destino}"
        )

    def log_fallo(self, motivo, ruta):
        self.txt_resultados.appendPlainText(
            f"FAIL ({motivo}): {ruta}"
        )


# ==========================
# MAIN
# ==========================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Guardar una ruta en un archivo txt")
    parser.add_argument("ruta", help="Ruta a guardar")
    args = parser.parse_args()
    if not args.ruta.endswith(".txt"):
        with open(TXT_RUTAS, "w", encoding="utf-8") as f:
            f.write(args.ruta)
                
    app = QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon(ICON_WIN))
    app.setStyleSheet(QSS_DARK)

    w = MoveToTrashApp()
    w.show()

    sys.exit(app.exec_())
