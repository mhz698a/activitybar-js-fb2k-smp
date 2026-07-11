# domain_visor/year_item.py

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QFont, QColor, QPainter
from PyQt6.QtWidgets import QGraphicsItem

class YearItem(QGraphicsItem):
    """
    Representa un año individual dentro de un dominio (Paso de Commit 5).
    Responsabilidades:
    - Dibujar únicamente el número del año en paint().
    - Fondo transparente y sin bordes.
    - Utilizar la fuente del visor actual (Arial 10) y texto blanco.
    - Heredar de QGraphicsItem y asociarse jerárquicamente a su DomainItem padre.
    """
    def __init__(self, x, y, width, height, year_value, parent=None):
        super().__init__(parent)
        self._x = float(x)
        self._y = float(y)
        self._width = float(width)
        self._height = float(height)
        self._year_value = year_value

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
