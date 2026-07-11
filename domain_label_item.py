from PyQt6.QtWidgets import QGraphicsTextItem
from PyQt6.QtGui import QFont, QColor

class DomainLabelItem(QGraphicsTextItem):
    """
    Representa una etiqueta de texto en el diagrama (Paso 6).
    Responsabilidades:
    - mostrar texto
    - configurar fuente
    - configurar color
    - posición absoluta
    - no conocer dominio
    - no realizar cálculos
    """
    def __init__(self, text, font_family="Arial", font_size=10, color_hex="#ffffff", is_bold=False, is_italic=False, parent=None):
        super().__init__(text, parent)

        font = QFont(font_family, font_size)
        if is_bold:
            font.setBold(True)
        if is_italic:
            font.setItalic(True)

        self.setFont(font)
        self.setDefaultTextColor(QColor(color_hex))

    def set_absolute_position(self, x, y):
        self.setPos(x, y)
