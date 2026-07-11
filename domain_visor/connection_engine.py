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
            from_port = registry.get_port(connection.from_year, "right")
            to_port = registry.get_port(connection.to_year, "left")

            if from_port and to_port:
                cable = CableItem(from_port, to_port)
                scene.addItem(cable)
