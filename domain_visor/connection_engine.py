# domain_visor/connection_engine.py

from domain_visor.cable_item import CableItem

class ConnectionEngine:
    """
    Responsabilidad única:
    Conectar puertos lógicos resolviendo referencias mediante PortRegistry y crear CableItems en la escena.

    No conoce los archivos JSON ni carga datos. Solo consume Connections ya cargadas y puertos registrados.
    """
    def __init__(self):
        pass

    def create_connections(self, scene, connections, registry):
        """
        Itera sobre una lista de objetos Connection, obtiene sus puertos (derecho e izquierdo)
        desde PortRegistry, crea los objetos gráficos CableItem correspondientes y los agrega a la escena.
        """
        for connection in connections:
            # Obtener puertos izquierdo y derecho de ambos extremos
            left_from = registry.get_port(connection.from_year, "left")
            right_from = registry.get_port(connection.from_year, "right")
            left_to = registry.get_port(connection.to_year, "left")
            right_to = registry.get_port(connection.to_year, "right")

            if left_from and left_to:
                # Determinar de forma inteligente los lados de conexión según el flujo horizontal (Calibrado: Commit 12.1):
                # - Si el origen está más a la izquierda que el destino (flujo de izquierda a derecha),
                #   conectamos el puerto derecho del origen al puerto izquierdo del destino.
                # - Si el origen está más a la derecha que el destino (flujo de derecha a izquierda),
                #   conectamos el puerto izquierdo del origen al puerto derecho del destino.
                # - Si están en la misma columna, conectamos del puerto derecho al derecho de ambos años.
                if left_from._x < left_to._x:
                    from_port = right_from
                    to_port = left_to
                elif left_from._x > left_to._x:
                    from_port = left_from
                    to_port = right_to
                else:
                    from_port = right_from
                    to_port = right_to

                if from_port and to_port:
                    cable = CableItem(from_port, to_port)
                    scene.addItem(cable)
            else:
                # Respaldo clásico si no se encuentran ambos lados
                from_port = registry.get_port(connection.from_year, "right")
                to_port = registry.get_port(connection.to_year, "left")
                if from_port and to_port:
                    cable = CableItem(from_port, to_port)
                    scene.addItem(cable)
