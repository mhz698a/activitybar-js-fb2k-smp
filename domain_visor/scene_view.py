# domain_visor/scene_view.py

import json
import traceback
from PyQt6.QtWidgets import QMainWindow, QGraphicsView, QGraphicsScene, QSplitter, QPushButton
from PyQt6.QtCore import Qt, QSettings, QByteArray
from PyQt6.QtGui import QBrush, QColor, QPainter, QShortcut, QKeySequence

from domain_visor.theme import Theme
from domain_visor.render_engine import RenderEngine
from domain_visor.json_editor import JSONEditorPanel

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

        # Crear el botón flotante
        self.toggle_button = QPushButton("◀", self)
        self.toggle_button.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #3e3e42;
                border-color: #85c1e9;
            }
            QPushButton:pressed {
                background-color: #1e1e1e;
            }
        """)
        self.toggle_button.adjustSize()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_button_position()

    def update_button_position(self):
        if hasattr(self, 'toggle_button') and self.toggle_button:
            x = 15
            scrollbar_height = self.horizontalScrollBar().height() if self.horizontalScrollBar().isVisible() else 0
            y = self.height() - self.toggle_button.height() - 15 - scrollbar_height
            self.toggle_button.move(x, y)

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
        self._first_show = True
        self.setWindowTitle("Infraestructura de años, dominios y superdominios")
        self.setStyleSheet(f"background-color: {Theme.APP_BACKGROUND}; color: {Theme.TEXT_WHITE};")
        
        self.settings = QSettings("etudetools", "year_struct_vasculum")
        self.init_ui()

    def init_ui(self):
        # 1. Crear el splitter central
        self.splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self.splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #3e3e42;
                width: 4px;
            }
        """)

        # 2. Configurar JSONEditorPanel en la izquierda
        self.json_panel = JSONEditorPanel(self)
        self.splitter.addWidget(self.json_panel)

        # 3. Configurar ZoomableGraphicsView como panel derecho
        self.view = ZoomableGraphicsView()
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.view.setFrameShape(QGraphicsView.Shape.NoFrame)
        self.view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.view.setBackgroundBrush(QBrush(QColor(Theme.APP_BACKGROUND)))
        
        # Soportar arrastre directo estilo mano además de las barras de desplazamiento (Paso 2)
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.splitter.addWidget(self.view)

        # 4. Crear la escena y asignarla al View
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)

        # 5. Instanciar RenderEngine para delegar el renderizado
        self.render_engine = RenderEngine()

        # Cargar archivo JSON e inicializar el tree view
        self.load_initial_json()

        # Conectar cambios del tree view para el guardado automático y renderizado
        self.json_panel.tree.json_changed.connect(self.on_json_data_changed)

        # Renderizar escena inicial
        self.trigger_render()

        # 6. Configurar atajos de teclado para Zoom (Paso 2)
        self.setup_shortcuts()

        # 7. Configurar vista central y tamaño mínimo, y restaurar estado de splitter
        self.setCentralWidget(self.splitter)
        self.setMinimumSize(1400, 700)
        self.showMaximized()

        self.restore_splitter_state()
        
        # Restaurar estado visible de la edición del JSON
        self.restore_editor_visible_state()
        
        # Conectar el botón para mostrar/ocultar el editor
        self.view.toggle_button.clicked.connect(self.toggle_json_editor)

    def restore_editor_visible_state(self):
        editor_visible_setting = self.settings.value("json_editor_visible")
        if editor_visible_setting is None:
            self.editor_visible = True
        elif isinstance(editor_visible_setting, str):
            self.editor_visible = (editor_visible_setting.lower() == "true")
        else:
            self.editor_visible = bool(editor_visible_setting)

        self.json_panel.setVisible(self.editor_visible)
        btn_text = "◀" if self.editor_visible else "▶"
        self.view.toggle_button.setText(btn_text)
        self.view.update_button_position()

    def toggle_json_editor(self):
        self.editor_visible = not self.editor_visible
        self.json_panel.setVisible(self.editor_visible)
        self.settings.setValue("json_editor_visible", self.editor_visible)
        
        btn_text = "◀" if self.editor_visible else "▶"
        self.view.toggle_button.setText(btn_text)
        self.view.update_button_position()

    def load_initial_json(self):
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.json_panel.tree.load_json(data)
        except Exception as e:
            self.show_error(f"Error cargando JSON inicial:\n{str(e)}")

    def on_json_data_changed(self):
        # 1. Obtener datos actuales del árbol
        try:
            data = self.json_panel.tree.get_json()
        except Exception as e:
            self.show_error(f"Error generando estructura JSON:\n{str(e)}")
            return

        # 2. Guardar automáticamente a infrastructure.json
        try:
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.show_error(f"Error escribiendo en archivo de infraestructura:\n{str(e)}")
            return

        # 3. Re-renderizar escena
        self.trigger_render()

    def trigger_render(self):
        try:
            # Intentar renderizar
            self.render_engine.render(self.scene, self._json_title, self.json_path)
            # Si fue exitoso, ocultamos el cartel de error
            self.json_panel.error_label.setVisible(False)
        except Exception as e:
            tb = traceback.format_exc()
            self.show_error(f"Error de dibujo o validación en el renderizado:\n{tb}")

    def show_error(self, message):
        self.json_panel.error_label.setText(message)
        self.json_panel.error_label.setVisible(True)

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

    def restore_splitter_state(self):
        state = self.settings.value("splitter_state")
        if state is not None:
            if isinstance(state, QByteArray):
                self.splitter.restoreState(state)
            elif isinstance(state, bytes):
                self.splitter.restoreState(QByteArray(state))
        else:
            # Por defecto, dar el 35% del ancho total al JSON editor
            self.splitter.setSizes([350, 650])

    def showEvent(self, event):
        super().showEvent(event)
        if self._first_show:
            self._first_show = False
            self.center_domains_container()

    def center_domains_container(self):
        rect = self.scene.itemsBoundingRect()
        if not rect.isNull():
            self.view.centerOn(rect.center())

    def closeEvent(self, event):
        # Guardar el estado del splitter al cerrar la aplicación
        self.settings.setValue("splitter_state", self.splitter.saveState())
        super().closeEvent(event)
