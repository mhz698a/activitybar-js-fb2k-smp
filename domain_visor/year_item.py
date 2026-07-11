# domain_visor/year_item.py

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QFont, QColor, QPainter
from PyQt6.QtWidgets import QGraphicsItem

from domain_visor.port_item import PortItem

class YearItem(QGraphicsItem):
    """
    Representa un año individual dentro de un dominio (Paso de Commit 5 y 6).
    Responsabilidades:
    - Dibujar únicamente el número del año en paint().
    - Fondo transparente y sin bordes.
    - Utilizar la fuente del visor actual (Arial 10) y texto blanco.
    - Heredar de QGraphicsItem y asociarse jerárquicamente a su DomainItem padre.
    - Instanciar e incorporar dos puertos (PortItem) de conexión: izquierdo y derecho.
    """
    def __init__(self, x, y, width, height, year_value, parent=None):
        super().__init__(parent)
        self._x = float(x)
        self._y = float(y)
        self._width = float(width)
        self._height = float(height)
        self._year_value = year_value

        # Instanciar puertos de conexión izquierdo y derecho (Commit 6)
        # Diámetro de 8px, centrados verticalmente con el año (de altura 15px)
        port_diameter = 8.0
        port_y = self._y + (self._height - port_diameter) / 2.0

        # El puerto izquierdo se ubica cerca del borde izquierdo (ej. 4px de margen)
        left_port_x = self._x + 4.0
        self.left_port = PortItem(left_port_x, port_y, port_diameter, "left", parent=self)

        # El puerto derecho se ubica cerca del borde derecho (ej. 12px de margen desde el final)
        right_port_x = self._x + self._width - 12.0
        self.right_port = PortItem(right_port_x, port_y, port_diameter, "right", parent=self)

    def boundingRect(self) -> QRectF:
        # Retorna el área que cubre este ítem de año
        return QRectF(self._x, self._y, self._width, self._height)

    def paint(self, painter, option, widget=None):
        painter.save()

        # Activar suavizado para texto perfecto
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        # Configurar fuente Arial 10, color blanco
        font = QFont("Arial", 10)
        painter.setFont(font)
        painter.setPen(QColor("#ffffff"))

        # Dibujar el año centrado en su rectángulo
        rect = QRectF(self._x, self._y, self._width, self._height)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(self._year_value))

        painter.restore()
