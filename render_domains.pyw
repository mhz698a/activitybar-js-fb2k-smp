# render_domains.py
# first release: 2026-06-23 20:35:00

from pathlib import Path
import sys
import json
import os
import ctypes
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QMessageBox, QGraphicsView, QGraphicsScene
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon, QBrush, QColor, QPainter

# --- ANÁLISIS DEL RENDERIZADOR ACTUAL (PASO 1) ---
# Responsabilidades identificadas:
# - Construcción de ventana: VasculumApp.__init__ e init_ui.
# - Renderizado: Actualmente NO usa paintEvent. Usa QLabels en layouts.
# - Cálculos de geometría (Layout-based):
#   - Márgenes: main_layout(30, 20, 30, 30).
#   - Espaciado: main(15), columnas(20), bloques(8).
#   - Título principal: Arial 18 Bold, centrado.
#   - Columnas: Título (Arial 11 Bold) + Código (Consolas 10).
#   - Bloques: Fondo según deuterodomain (#b93a82 o #6a329f), Arial 10.
#   - Subetiquetas: Arial 8 Italic.
# - Carga de datos: load_json_data() carga desde domains.json.
# --------------------------------------------------

APP_DIR = Path(__file__).resolve().parent.as_posix()
ICON_WIN = f"{APP_DIR}/assets/online.ico"
JSON_DOMAINS = f"{APP_DIR}/__structure__/domains.json"
CONTAINER_DOMAINS = f"{APP_DIR}/__structure__/container.json"

myappid = 'etudetools.year_struct.render_domains.1.0'
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)


class VasculumApp(QMainWindow):
    def __init__(self, json_path, json_title):
        super().__init__()
        self.json_path = json_path
        self._json_title = json_title
        self.setWindowTitle("Visor de infraestrucutra de dominios")
        self.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")
        self.init_ui()

    def load_json_data(self):
        """Carga el archivo JSON de forma dinámica y maneja errores."""
        if not os.path.exists(self.json_path):
            QMessageBox.critical(self, "Error", f"No se encontró el archivo: {self.json_path}")
            return []
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Error de Lectura", f"No se pudo parsear el JSON:\n{str(e)}")
            return []

    def get_containter_title(self) -> str:
        # Validar si el archivo realmente existe en el disco
        if not os.path.exists(self._json_title):
            return "Contenedor Desconocido"
            
        try:
            # Abrir y cargar el archivo JSON de manera segura
            with open(self._json_title, 'r', encoding='utf-8') as f:
                data = json.load(f)  # Se usa json.load() para archivos, no loads()
            
            # Validar que la lista no esté vacía y extraer el título
            if isinstance(data, list) and len(data) > 0:
                return (data[0].get("title_container", "Sin Título")).replace("_", " ").title()
            
            return "Estructura JSON Inválida"
            
        except Exception:
            return "Error al leer título"
            
    def _range_year_count(self, range_text: str) -> int:
        start_year, end_year = map(int, range_text.split("-"))
        return end_year - start_year + 1

    def build_superdomain_metadata(self, json_data, unique_superdomains):
        """
        Calcula los metadatos de cada superdomain directamente desde el JSON.

        t = total de años del superdomain
        e = años del segundo bloque del superdomain
        d = años de cada bloque, marcando el segundo con paréntesis
        z = diferencia contra el primer superdomain
        """
        
        meta = {}
        first_total = None

        for index, superdomain in enumerate(unique_superdomains):
            blocks = [b for b in json_data if b.get("superdomain") == superdomain]

            counts = []
            for block in blocks:
                try:
                    counts.append(self._range_year_count(block.get("range", "")))
                except Exception:
                    counts.append(0)

            total_years = sum(counts)

            if first_total is None:
                first_total = total_years

            second_count = counts[1] if len(counts) > 1 else 0
            d_text = "-".join(
                f"({count})" if i == 1 else str(count)
                for i, count in enumerate(counts)
            ) or "?"

            z = abs(first_total - total_years) if first_total is not None else 0

            meta[superdomain] = {
                "title": superdomain.replace("_", " ").title(),
                "code": f"[t{total_years}][e{second_count}][d:{d_text}][z{z}]"
            }

        return meta
    
    def init_ui(self):
        # 1. Cargar datos frescos del archivo
        self.json_data = self.load_json_data()
        if not self.json_data:
            sys.exit(1)

        # 2. Preparar metadatos (necesarios para futuros pasos de renderizado)
        unique_superdomains = []
        for item in self.json_data:
            s_domain = item.get("superdomain", "")
            if s_domain and s_domain not in unique_superdomains:
                unique_superdomains.append(s_domain)

        self.superdomain_meta = self.build_superdomain_metadata(self.json_data, unique_superdomains)

        # 3. Configurar QGraphicsView como widget central (Paso 2)
        self.view = QGraphicsView()
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.view.setFrameShape(QGraphicsView.Shape.NoFrame)
        self.view.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.view.setBackgroundBrush(QBrush(QColor("#1e1e1e")))
        self.view.setDragMode(QGraphicsView.DragMode.NoDrag)

        self.setCentralWidget(self.view)
        self.setMinimumSize(850, 650)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    try:
        app.setWindowIcon(QIcon(ICON_WIN))
    except Exception:
        pass

    window = VasculumApp(JSON_DOMAINS, CONTAINER_DOMAINS)
    window.show()
    sys.exit(app.exec())
