# domain_visor/scene_view.py

from PyQt6.QtWidgets import QMainWindow, QGraphicsView, QGraphicsScene
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor, QPainter

from domain_visor.theme import Theme
from domain_visor.render_engine import RenderEngine

class VasculumApp(QMainWindow):
    """
    Ventana principal del visor de infraestructura.
    Responsable únicamente de configurar la ventana principal, la vista y la escena de QGraphics.
    Delega todo el renderizado y la lógica de creación de gráficos al RenderEngine.
    """
    def __init__(self, json_path, json_title):
        super().__init__()
        self.json_path = json_path
        self._json_title = json_title
        self.setWindowTitle("Visor de infraestructura de dominios")
        self.setStyleSheet(f"background-color: {Theme.APP_BACKGROUND}; color: {Theme.TEXT_WHITE};")
        self.init_ui()

    def init_ui(self):
        # 1. Configurar QGraphicsView como widget central
        self.view = QGraphicsView()
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.view.setFrameShape(QGraphicsView.Shape.NoFrame)
        self.view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.view.setBackgroundBrush(QBrush(QColor(Theme.APP_BACKGROUND)))
        self.view.setDragMode(QGraphicsView.DragMode.NoDrag)

        # 2. Crear la escena y asignarla al View
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)

        # 3. Instanciar RenderEngine para delegar el renderizado (Commit 9.1/11)
        self.render_engine = RenderEngine()
        self.render_engine.render(self.scene, self._json_title, self.json_path)

        # 4. Configurar vista central y tamaño mínimo
        self.setCentralWidget(self.view)
        self.setMinimumSize(850, 650)
