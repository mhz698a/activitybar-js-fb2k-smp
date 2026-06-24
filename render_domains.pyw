# render_domains.py
# first release: 2026-06-23 20:35:00

from pathlib import Path
import sys
import json
import os
import ctypes
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon

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
        json_data = self.load_json_data()
        if not json_data:
            sys.exit(1)

        # Contenedor e interfaz principal
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(30, 20, 30, 30)
        main_layout.setSpacing(15)

        # Título General Estático
        title_label = QLabel(self.get_containter_title())
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #ffffff; padding-bottom: 10px;")
        main_layout.addWidget(title_label)

        # Layout Horizontal para las Columnas generadas dinámicamente
        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(20)

        # 2. Descubrir columnas únicas presentes en el archivo JSON (mantiene el orden de aparición)
        unique_superdomains = []        
        for item in json_data:
            s_domain = item.get("superdomain", "")
            if s_domain and s_domain not in unique_superdomains:
                unique_superdomains.append(s_domain)
        
        superdomain_meta = self.build_superdomain_metadata(json_data, unique_superdomains)

        # 3. Construir cada columna iterando sobre el JSON estructurado
        for col_key in unique_superdomains:
            meta = superdomain_meta.get(col_key, {
                "title": col_key.replace("_", " ").title(),
                "code": "[t0][e0][d:?][z0]"
            })
            
            col_widget = QWidget()
            col_layout = QVBoxLayout(col_widget)
            col_layout.setContentsMargins(0, 0, 0, 0)
            col_layout.setSpacing(8)
            col_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

            # Celda con Código Técnico
            code_label = QLabel(meta["code"])
            code_label.setFont(QFont("Consolas", 10))
            code_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            code_label.setStyleSheet("""
                background-color: #2d2d2d; 
                color: #b0b0b0; 
                border: 1px solid #444444; 
                padding: 6px;
            """)
            col_layout.addWidget(code_label)

            # Celda con Título de Columna
            title_col_label = QLabel(meta["title"])
            title_col_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
            title_col_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            title_col_label.setStyleSheet("""
                background-color: #2d2d2d; 
                color: #ffffff; 
                border: 1px solid #444444; 
                padding: 8px;
            """)
            col_layout.addWidget(title_col_label)
            col_layout.addSpacing(10)

            # 4. Filtrar y pintar los bloques de años que pertenecen a esta columna exacta
            blocks = [b for b in json_data if b.get("superdomain") == col_key]
            for block in blocks:
                # Lógica dinámica del color basada en deuterodomain
                if block.get("deuterodomain") == "alejandra_maya":
                    bg_color = "#b93a82"  # Rosa/Magenta
                else:
                    bg_color = "#6a329f"  # Morado/Púrpura

                # Parsing dinámico del rango numérico ("AAAA-AAAA")
                try:
                    start_year, end_year = map(int, block["range"].split("-"))
                    years_list = [str(y) for y in range(start_year, end_year + 1)]
                    years_text = "\n".join(years_list)
                except Exception:
                    years_text = block.get("range", "Error Rango")

                # Pintar Bloque de Años
                block_label = QLabel(years_text)
                block_label.setFont(QFont("Arial", 10))
                block_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                block_label.setStyleSheet(f"""
                    background-color: {bg_color}; 
                    color: #ffffff; 
                    border: 1.5px solid #ffffff; 
                    border-radius: 2px;
                    padding: 8px 0px;
                """)
                col_layout.addWidget(block_label)

                # Pintar Subetiqueta informativa inferior del bloque
                domain_raw = block.get("domain", "")
                domain_title = domain_raw.replace("_", " ").title()
                info_label = QLabel(f"{domain_title}\n({block.get('range', '')})")
                info_label.setFont(QFont("Arial", 8, QFont.Weight.Medium, italic=True))
                info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                info_label.setStyleSheet("color: #8a8a8a; padding-bottom: 5px;")
                col_layout.addWidget(info_label)

            columns_layout.addWidget(col_widget)

        main_layout.addLayout(columns_layout)
        self.setCentralWidget(main_widget)
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
