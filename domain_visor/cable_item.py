# domain_visor/cable_item.py

from PyQt6.QtCore import QRectF, Qt, QPointF
from PyQt6.QtGui import QPen, QColor, QPainterPath, QPainter
from PyQt6.QtWidgets import QGraphicsPathItem

class CableItem(QGraphicsPathItem):
    """
    Representa un cable de conexión S-shaped entre dos puertos (Paso de Commit 9).
    Responsabilidades:
    - Heredar de QGraphicsPathItem.
    - Recibir dos PortItem (from_port, to_port) en su constructor.
    - Calcular el camino curvo (cúbico Bézier) entre los centros de ambos puertos.
    - Configurar un estilo de lápiz neutral de 2px.
    """
    def __init__(self, from_port, to_port, parent=None):
        super().__init__(parent)
        self.from_port = from_port
        self.to_port = to_port

        # Establecer un zValue alto para que los cables se rendericen por encima de los bloques
        self.setZValue(15.0)

        # Generar el camino inicial
        self.update_path()

    def update_path(self):
        """
        Calcula la curva Bézier cúbica basándose en la posición absoluta
        en la escena de los centros de los puertos.
        """
        # 1. Calcular los centros de los círculos de puerto usando sus coordenadas absolutas
        # (diámetro = 8, radio = 4.0)
        p1 = QPointF(self.from_port._x + 4.0, self.from_port._y + 4.0)
        p2 = QPointF(self.to_port._x + 4.0, self.to_port._y + 4.0)

        # 2. Determinar los puntos de control para la curva Bézier horizontal (S-shaped)
        # Desfase horizontal sugerido de 50px según el lado por el que sale/entra el cable
        offset_from = 50.0 if self.from_port._side == "right" else -50.0
        offset_to = -50.0 if self.to_port._side == "left" else 50.0

        c1 = QPointF(p1.x() + offset_from, p1.y())
        c2 = QPointF(p2.x() + offset_to, p2.y())

        # 3. Construir el QPainterPath
        path = QPainterPath()
        path.moveTo(p1)
        path.cubicTo(c1, c2, p2)

        self.setPath(path)

        # 4. Configurar el estilo del cable: color gris claro y 2px de espesor
        pen = QPen(QColor("#d0d0d0"))
        pen.setWidthF(2.0)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        self.setPen(pen)
