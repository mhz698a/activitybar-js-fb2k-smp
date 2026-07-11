# domain_visor/scene_view.py

from pathlib import Path
import os
import json
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QGraphicsView, QGraphicsScene
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor, QPainter

from domain_visor.superdomain_item import SuperDomainItem

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
            import sys
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
        self.view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.view.setBackgroundBrush(QBrush(QColor("#1e1e1e")))
        self.view.setDragMode(QGraphicsView.DragMode.NoDrag)

        # 4. Crear la escena y asignarla al View (Paso 3)
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)

        # 5. Instanciar y agregar SuperDomainItems vacíos
        margin_left = 30
        margin_top = 40
        column_width = 200
        spacing_columns = 20
        column_height = 450

        for i, sd in enumerate(unique_superdomains):
            x = margin_left + i * (column_width + spacing_columns)
            y = margin_top
            title = sd.replace("_", " ").title()

            item = SuperDomainItem(x, y, column_width, column_height, title)
            self.scene.addItem(item)

        # Configurar SceneRect para acomodar los ítems
        total_width = margin_left + len(unique_superdomains) * (column_width + spacing_columns) + margin_left
        total_height = margin_top + column_height + 50
        self.scene.setSceneRect(0, 0, total_width, total_height)

        # 6. Configurar vista central y tamaño mínimo
        self.setCentralWidget(self.view)
        self.setMinimumSize(850, 650)
