# domain_visor/render_engine.py

from domain_visor.models import load_from_json
from domain_visor.layout_engine import LayoutEngine
from domain_visor.color_resolver import ColorResolver
from domain_visor.port_registry import PortRegistry
from domain_visor.superdomain_item import SuperDomainItem
from domain_visor.domain_item import DomainItem
from domain_visor.year_item import YearItem
from domain_visor.cable_item import CableItem

class RenderEngine:
    """
    Coordinador de renderizado puro (JSON -> Models -> GraphicsItems -> Scene).
    Delega el cálculo de diseño al LayoutEngine, la resolución de color al ColorResolver
    y la resolución de puertos lógicos/visuales al PortRegistry.
    """
    def __init__(self):
        self.layout_engine = LayoutEngine()

    def render(self, scene, container_path, domains_path):
        """
        Limpia la escena, carga el modelo jerárquico, obtiene la geometría de LayoutEngine,
        resuelve colores y puertos, e instancia todos los gráficos de forma dinámica.
        """
        # 1. Limpiar escena e instanciar registro de puertos desacoplado
        scene.clear()
        registry = PortRegistry()

        # 2. Cargar el modelo jerárquico unificado
        container = load_from_json(domains_path, container_path)

        # 3. Obtener geometría espacial del LayoutEngine (Geometry -> GraphicsItems -> Scene)
        layout_data = self.layout_engine.calculate_layout(container)

        domain_items_map = {}

        # 4.1. Instanciar SuperDomainItems
        for sd, geom in layout_data["superdomains"].items():
            x, y, w, h = geom
            sd_item = SuperDomainItem(x, y, w, h, sd.title)
            scene.addItem(sd_item)

        # 4.2. Instanciar DomainItems resolviendo sus colores con ColorResolver
        for domain, geom in layout_data["domains"].items():
            x, y, w, h = geom
            bg_color, border_color = ColorResolver.resolve_colors(domain.role)

            dom_item = DomainItem(
                x=x,
                y=y,
                width=w,
                height=h,
                title=domain.name,
                background_color=bg_color,
                border_color=border_color
            )
            scene.addItem(dom_item)
            domain_items_map[domain] = dom_item

        # 4.3. Instanciar YearItems y registrar sus puertos en PortRegistry
        for year, geom in layout_data["years"].items():
            x, y, w, h = geom
            parent_domain = year.parent_domain
            dom_item = domain_items_map.get(parent_domain)

            y_item = YearItem(
                x=x,
                y=y,
                width=w,
                height=h,
                year_value=year.value,
                parent=dom_item
            )

            # Registrar puertos del año en el registro desacoplado
            registry.register_port(year.value, "left", y_item.left_port)
            registry.register_port(year.value, "right", y_item.right_port)

        # 5. Renderizar cables de forma 100% dinámica mediante el PortRegistry y container.connections
        for connection in container.connections:
            from_port = registry.get_port(connection.from_year, "right")
            to_port = registry.get_port(connection.to_year, "left")

            if from_port and to_port:
                cable = CableItem(from_port, to_port)
                scene.addItem(cable)

        # 6. Configurar el tamaño del lienzo de la escena
        sx, sy, sw, sh = layout_data["scene_rect"]
        scene.setSceneRect(sx, sy, sw, sh)
