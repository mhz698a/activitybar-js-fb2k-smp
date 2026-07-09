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

from domain_item import DomainItem
from domain_label_item import DomainLabelItem

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
        try:
            start_year, end_year = map(int, range_text.split("-"))
            return end_year - start_year + 1
        except Exception:
            return 0

    def calculate_scene_rect(self):
        """
        Calcula el tamaño lógico del diagrama (Paso 4).
        Basado en el análisis del renderizador antiguo:
        - Márgenes: 30 (L), 20 (T), 30 (R), 30 (B).
        - Espaciado título principal: 15 (espacio) + ~30 (altura título) + 10 (padding-bottom).
        - Espaciado entre columnas: 20.
        - Espaciado interno columna: 8.
        """
        margin_left = 30
        margin_top = 20
        margin_right = 30
        margin_bottom = 30
        spacing_main = 15
        spacing_columns = 20
        spacing_blocks = 8

        # Título principal (~18pt + padding)
        title_height = 40

        # Superdomains (columnas)
        unique_superdomains = []
        for item in self.json_data:
            sd = item.get("superdomain", "")
            if sd and sd not in unique_superdomains:
                unique_superdomains.append(sd)

        num_columns = len(unique_superdomains)
        column_width = 200 # Ancho aproximado para el cálculo lógico inicial

        total_width = margin_left + margin_right + (num_columns * column_width) + (max(0, num_columns - 1) * spacing_columns)

        # Altura máxima de columna
        max_col_height = 0
        for sd in unique_superdomains:
            col_height = 0
            # Meta code label (~10pt + padding)
            col_height += 30 + spacing_blocks
            # Title col label (~11pt + padding)
            col_height += 35 + 10 + spacing_blocks

            blocks = [b for b in self.json_data if b.get("superdomain") == sd]
            for block in blocks:
                # Bloque de años (Arial 10, ~15px por línea)
                years = self._range_year_count(block.get("range", ""))
                block_content_height = (years * 15) + 16 # padding
                col_height += block_content_height + spacing_blocks

                # Subetiqueta (~8pt, 2 líneas + padding)
                col_height += 40 + 5 # padding-bottom

            if col_height > max_col_height:
                max_col_height = col_height

        total_height = margin_top + title_height + spacing_main + max_col_height + margin_bottom

        return 0, 0, total_width, total_height

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

    def render_scene(self, partial=False):
        """
        Realiza el renderizado de la escena (Pasos 7, 8, 9).
        """
        margin_left = 30
        margin_top = 20
        spacing_main = 15
        spacing_columns = 20
        spacing_blocks = 8
        column_width = 200

        # Título General
        title_item = DomainLabelItem(self.get_containter_title(), font_size=18, is_bold=True)
        # Centrado manual aproximado (usando rect de la escena)
        scene_w = self.scene.sceneRect().width()
        title_w = title_item.boundingRect().width()
        title_item.set_absolute_position((scene_w - title_w) / 2, margin_top)
        self.scene.addItem(title_item)

        y_start_columns = margin_top + 40 + spacing_main

        unique_superdomains = []
        for item in self.json_data:
            sd = item.get("superdomain", "")
            if sd and sd not in unique_superdomains:
                unique_superdomains.append(sd)

        for i, sd in enumerate(unique_superdomains):
            # Si es parcial, solo procesamos el primer superdomain
            if partial and i > 0:
                break

            current_x = margin_left + i * (column_width + spacing_columns)
            current_y = y_start_columns

            meta = self.superdomain_meta.get(sd, {"code": "[?]", "title": sd})

            # Celda Código (Paso 9)
            code_item = DomainItem((current_x, current_y, column_width, 30), "#2d2d2d", border_color_hex="#444444", border_width=1)
            self.scene.addItem(code_item)
            code_label = DomainLabelItem(meta["code"], font_family="Consolas", font_size=10, color_hex="#b0b0b0")
            cl_w = code_label.boundingRect().width()
            code_label.set_absolute_position(current_x + (column_width - cl_w) / 2, current_y + 5)
            self.scene.addItem(code_label)

            current_y += 30 + spacing_blocks

            # Celda Título Columna (Paso 9)
            title_col_item = DomainItem((current_x, current_y, column_width, 35), "#2d2d2d", border_color_hex="#444444", border_width=1)
            self.scene.addItem(title_col_item)
            title_col_label = DomainLabelItem(meta["title"], font_size=11, is_bold=True)
            tcl_w = title_col_label.boundingRect().width()
            title_col_label.set_absolute_position(current_x + (column_width - tcl_w) / 2, current_y + 8)
            self.scene.addItem(title_col_label)

            current_y += 35 + 10

            blocks = [b for b in self.json_data if b.get("superdomain") == sd]
            for j, block in enumerate(blocks):
                # Si es parcial, solo procesamos el primer bloque
                if partial and j > 0:
                    break

                bg = "#b93a82" if block.get("deuterodomain") == "alejandra_maya" else "#6a329f"

                years_count = self._range_year_count(block.get("range", ""))
                try:
                    start_year, end_year = map(int, block["range"].split("-"))
                    years_text = "\n".join(str(y) for y in range(start_year, end_year + 1))
                except Exception:
                    years_text = block.get("range", "Error")

                block_h = (years_count * 15) + 16
                domain_item = DomainItem((current_x, current_y, column_width, block_h), bg)
                self.scene.addItem(domain_item)

                years_label = DomainLabelItem(years_text, font_size=10)
                yl_w = years_label.boundingRect().width()
                years_label.set_absolute_position(current_x + (column_width - yl_w) / 2, current_y + 8)
                self.scene.addItem(years_label)

                current_y += block_h + spacing_blocks

                domain_title = block.get("domain", "").replace("_", " ").title()
                info_text = f"{domain_title}\n({block.get('range', '')})"
                info_label = DomainLabelItem(info_text, font_size=8, color_hex="#8a8a8a", is_italic=True)
                il_w = info_label.boundingRect().width()
                info_label.set_absolute_position(current_x + (column_width - il_w) / 2, current_y)
                self.scene.addItem(info_label)

                current_y += 40 + 5

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

        # 4. Crear la escena y asignarla al View (Paso 3)
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)

        # 5. Calcular SceneRect (Paso 4)
        rect = self.calculate_scene_rect()
        self.scene.setSceneRect(float(rect[0]), float(rect[1]), float(rect[2]), float(rect[3]))

        # 6. Renderizado (Pasos 7, 8, 9)
        self.render_scene(partial=False)

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
