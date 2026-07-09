from PyQt6.QtWidgets import QGraphicsPathItem, QGraphicsTextItem
from PyQt6.QtGui import QColor, QPen, QBrush, QFont
from PyQt6.QtCore import Qt

class RibbonItem(QGraphicsPathItem):
    """
    Representa un ribbon (lazo/curva) en el diagrama (Fase 2).

    Responsabilidades:
    - Mostrar una forma basada en QPainterPath.
    - Mostrar un texto centrado mediante composición (QGraphicsTextItem interno).
    - Aplicar colores, bordes y estilos de fuente.
    - No conocer la estructura del JSON ni reglas de negocio.
    - No calcular su propia geometría (la recibe ya construida).
    """
    def __init__(self, path, text="", bg_color_hex="#3498db", border_color_hex="#ffffff",
                 text_color_hex="#ffffff", font_family="Arial", font_size=10,
                 is_bold=False, is_italic=False, border_width=1.5, z_value=100, parent=None):
        # path es un QPainterPath
        super().__init__(path, parent)

        self.setZValue(z_value)

        # Configurar apariencia del ribbon
        self.bg_color = QColor(bg_color_hex)
        self.border_color = QColor(border_color_hex)
        self.setBrush(QBrush(self.bg_color))

        pen = QPen(self.border_color)
        pen.setWidthF(border_width)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        self.setPen(pen)

        # Crear la etiqueta de texto como hijo (composición)
        self.label = QGraphicsTextItem(text, self)

        font = QFont(font_family, font_size)
        if is_bold:
            font.setBold(True)
        if is_italic:
            font.setItalic(True)

        self.label.setFont(font)
        self.label.setDefaultTextColor(QColor(text_color_hex))

        # Posicionar el texto inicialmente
        self.update_label_position()

    def update_label_position(self):
        """
        Centra la etiqueta de texto dentro del rectángulo delimitador del path.
        """
        path_rect = self.path().boundingRect()
        text_rect = self.label.boundingRect()

        # Cálculo de centrado relativo a las coordenadas del path
        x = path_rect.x() + (path_rect.width() - text_rect.width()) / 2
        y = path_rect.y() + (path_rect.height() - text_rect.height()) / 2

        self.label.setPos(x, y)
