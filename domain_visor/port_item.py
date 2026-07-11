# domain_visor/port_item.py

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QPen, QBrush, QColor, QPainter
from PyQt6.QtWidgets import QGraphicsItem

class PortItem(QGraphicsItem):
    """
    Representa un puerto de conexión (círculo) a los lados de un año (Paso de Commit 6).
    Responsabilidades:
    - Dibujar un círculo con fondo transparente y borde blanco de 8px de diámetro.
    - Conocer su lado ("left" o "right") para referencias futuras de conexión.
    - Heredar de QGraphicsItem y asociarse jerárquicamente a su YearItem padre.
    """
    def __init__(self, x, y, diameter, side, parent=None):
        super().__init__(parent)
        self._x = float(x)
        self._y = float(y)
        self._diameter = float(diameter)
        self._side = side  # "left" o "right"

    def boundingRect(self) -> QRectF:
        # Retorna el área que cubre este puerto, incluyendo un pequeño margen para el borde
        return QRectF(self._x - 2.0, self._y - 2.0, self._diameter + 4.0, self._diameter + 4.0)

    def paint(self, painter, option, widget=None):
        painter.save()

        # Activar suavizado para un círculo perfecto
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Configurar borde blanco y fondo transparente (sin pincel)
        pen = QPen(QColor("#ffffff"))
        pen.setWidthF(1.5)
        painter.setPen(pen)
        painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))

        # Dibujar círculo
        rect = QRectF(self._x, self._y, self._diameter, self._diameter)
        painter.drawEllipse(rect)

        painter.restore()
