# domain_visor/scene_view.py

from PyQt6.QtWidgets import QMainWindow, QGraphicsView, QGraphicsScene
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor, QPainter, QShortcut, QKeySequence

from domain_visor.theme import Theme
from domain_visor.render_engine import RenderEngine

class ZoomableGraphicsView(QGraphicsView):
    """
    Vista de QGraphics personalizada que soporta zoom controlado con la rueda del mouse
    y métodos auxiliares de escala (Paso 1).
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.zoom_factor = 1.0
        self.min_zoom = 0.2
        self.max_zoom = 5.0
        
        # Anclar el zoom en el centro de la vista
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)

    def wheelEvent(self, event):
        angle_delta = event.angleDelta().y()
        zoom_step = 1.15

        if angle_delta > 0:
            new_zoom = self.zoom_factor * zoom_step
        else:
            new_zoom = self.zoom_factor / zoom_step

        if self.min_zoom <= new_zoom <= self.max_zoom:
            relative_factor = new_zoom / self.zoom_factor
            self.scale(relative_factor, relative_factor)
            self.zoom_factor = new_zoom
            event.accept()
        else:
            super().wheelEvent(event)

    def zoom_in(self):
        new_zoom = self.zoom_factor * 1.15
        if new_zoom <= self.max_zoom:
            relative_factor = new_zoom / self.zoom_factor
            self.scale(relative_factor, relative_factor)
            self.zoom_factor = new_zoom

    def zoom_out(self):
        new_zoom = self.zoom_factor / 1.15
        if new_zoom >= self.min_zoom:
            relative_factor = new_zoom / self.zoom_factor
            self.scale(relative_factor, relative_factor)
            self.zoom_factor = new_zoom

    def zoom_reset(self):
        if self.zoom_factor != 1.0:
            relative_factor = 1.0 / self.zoom_factor
            self.scale(relative_factor, relative_factor)
            self.zoom_factor = 1.0


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
        self.setWindowTitle("Infraestructura de años, dominios y superdominios")
        self.setStyleSheet(f"background-color: {Theme.APP_BACKGROUND}; color: {Theme.TEXT_WHITE};")
        self.init_ui()

    def init_ui(self):
        # 1. Configurar ZoomableGraphicsView como widget central
        self.view = ZoomableGraphicsView()
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.view.setFrameShape(QGraphicsView.Shape.NoFrame)
        self.view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.view.setBackgroundBrush(QBrush(QColor(Theme.APP_BACKGROUND)))
        
        # Soportar arrastre directo estilo mano además de las barras de desplazamiento (Paso 2)
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

        # 2. Crear la escena y asignarla al View
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)

        # 3. Instanciar RenderEngine para delegar el renderizado (Commit 9.1/11)
        self.render_engine = RenderEngine()
        self.render_engine.render(self.scene, self._json_title, self.json_path)

        # 4. Configurar atajos de teclado para Zoom (Paso 2)
        self.setup_shortcuts()

        # 5. Configurar vista central y tamaño mínimo
        self.setCentralWidget(self.view)
        self.setMinimumSize(850, 650)

    def setup_shortcuts(self):
        # Atajos para Zoom In (Ctrl + + y Ctrl + =)
        self.shortcut_zoom_in_plus = QShortcut(QKeySequence("Ctrl++"), self)
        self.shortcut_zoom_in_plus.activated.connect(self.view.zoom_in)
        
        self.shortcut_zoom_in_equal = QShortcut(QKeySequence("Ctrl+="), self)
        self.shortcut_zoom_in_equal.activated.connect(self.view.zoom_in)

        # Atajo para Zoom Out (Ctrl + -)
        self.shortcut_zoom_out = QShortcut(QKeySequence("Ctrl+-"), self)
        self.shortcut_zoom_out.activated.connect(self.view.zoom_out)

        # Atajo para Resetear Zoom (Ctrl + 0)
        self.shortcut_zoom_reset = QShortcut(QKeySequence("Ctrl+0"), self)
        self.shortcut_zoom_reset.activated.connect(self.view.zoom_reset)
