from PyQt6.QtWidgets import QGraphicsRectItem
from PyQt6.QtGui import QColor, QPen, QBrush
from PyQt6.QtCore import Qt

class DomainItem(QGraphicsRectItem):
    """
    Representa un dominio en el diagrama (Paso 5).
    Responsabilidades:
    - almacenar datos del dominio
    - almacenar el rectángulo
    - aplicar color
    - aplicar borde
    - no contener texto
    - no conocer JSON
    - no contener lógica de layout
    """
    def __init__(self, rect_data, bg_color_hex, border_color_hex="#ffffff", border_width=1.5, parent=None):
        # rect_data: (x, y, w, h)
        super().__init__(rect_data[0], rect_data[1], rect_data[2], rect_data[3], parent)

        self.bg_color = QColor(bg_color_hex)
        self.border_color = QColor(border_color_hex)

        self.setBrush(QBrush(self.bg_color))

        pen = QPen(self.border_color)
        pen.setWidthF(border_width)
        pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        self.setPen(pen)

        # Almacenar datos del dominio (opcional, para referencia futura)
        self.domain_data = {}

    def set_domain_data(self, data):
        self.domain_data = data
