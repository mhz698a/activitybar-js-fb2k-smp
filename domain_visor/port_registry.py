# domain_visor/port_registry.py

class PortRegistry:
    """
    Responsabilidad única:
    Mantener referencias entre datos lógicos (valores de año, lado de puerto)
    y objetos gráficos de puerto (PortItem).

    Reglas:
    - No debe calcular posiciones.
    - No debe crear objetos gráficos.
    - No debe conocer RenderEngine.
    - Solo almacena y recupera referencias de puertos.
    """
    def __init__(self):
        # Diccionario clave: (year_value, side) -> valor: PortItem
        self._registry = {}

    def register_port(self, year_value: int, side: str, port_item):
        """Registra una referencia de puerto para un año y un lado dados."""
        self._registry[(int(year_value), side.lower())] = port_item

    def get_port(self, year_value: int, side: str):
        """Retorna el PortItem correspondiente al año y lado solicitados."""
        return self._registry.get((int(year_value), side.lower()))
