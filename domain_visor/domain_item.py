# domain_visor/domain_item.py

from PyQt6.QtCore import QRectF, Qt, QLineF
from PyQt6.QtGui import QFont, QPen, QBrush, QColor, QPainter
from PyQt6.QtWidgets import QGraphicsItem

class DomainItem(QGraphicsItem):
    """
    Representa un dominio o bloque en el diagrama (Paso de Commit 4).
    Responsabilidades:
    - Dibujar un contenedor con fondo de color según el rol del dominio.
    - Dibujar un encabezado con el título del dominio.
    - Dibujar una línea divisora horizontal a una altura fija de 28px.
    - No mostrar años ni conexiones/cables (eso se agregará en commits posteriores).
    """
    def __init__(self, x, y, width, height, title, deuterodomain="", exodomain=""):
        super().__init__()
        self._x = float(x)
        self._y = float(y)
        self._width = float(width)
        self._height = float(height)
        self._title = title
        self._deuterodomain = deuterodomain
        self._exodomain = exodomain

    def boundingRect(self) -> QRectF:
        # Retorna el área que cubre este ítem, incluyendo un pequeño margen para el borde
        return QRectF(self._x - 2.0, self._y - 2.0, self._width + 4.0, self._height + 4.0)

    def paint(self, painter, option, widget=None):
        painter.save()

        # Activar suavizado
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        # Determinar el color de fondo según deuterodominio/exodominio
        if self._exodomain == "aurora_maya":
            bg_color = QColor("#2b73d6")  # Azul (exodominios / dominios terciarios)
        elif self._deuterodomain == "alejandra_maya":
            bg_color = QColor("#b93a82")  # Rosa/Magenta
        else:
            bg_color = QColor("#7c3ab9")  # Morado/Púrpura

        border_color = QColor("#ffffff")  # Borde blanco según el estilo actual del visor

        # 1. Dibujar el fondo y borde del bloque redondeado
        rect = QRectF(self._x, self._y, self._width, self._height)
        painter.setBrush(QBrush(bg_color))
        pen = QPen(border_color)
        pen.setWidthF(1.5)
        painter.setPen(pen)
        painter.drawRoundedRect(rect, 4.0, 4.0)

        # 2. Dibujar la línea divisora horizontal del encabezado a 28px de altura
        divider_y = self._y + 28.0
        # Dibujamos una línea recta de borde a borde
        painter.drawLine(QLineF(self._x, divider_y, self._x + self._width, divider_y))

        # 3. Dibujar el título del dominio en el encabezado
        font = QFont("Arial", 10, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QColor("#ffffff"))

        # El rectángulo del encabezado va desde self._y hasta divider_y
        header_rect = QRectF(self._x, self._y, self._width, 28.0)
        formatted_title = self._title.replace("_", " ").title()
        painter.drawText(header_rect, Qt.AlignmentFlag.AlignCenter, formatted_title)

        painter.restore()
