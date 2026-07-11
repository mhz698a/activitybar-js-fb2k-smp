# domain_visor/render_engine.py

from domain_visor.models import load_from_json
from domain_visor.layout_engine import LayoutEngine
from domain_visor.superdomain_item import SuperDomainItem
from domain_visor.domain_item import DomainItem
from domain_visor.year_item import YearItem
from domain_visor.cable_item import CableItem

class RenderEngine:
    """
    Responsabilidad única de renderizado:
    JSON -> Models -> GraphicsItems -> Scene.

    El renderer ya no calcula posiciones; delega esa tarea en el LayoutEngine.
    """
    def __init__(self):
        self.layout_engine = LayoutEngine()

    def render(self, scene, container_path, domains_path):
        """
        Limpia la escena, carga el modelo, obtiene la distribución geométrica
        de LayoutEngine e instancia todos los GraphicsItems correspondientes.
        """
        # 1. Limpiar escena
        scene.clear()

        # 2. Cargar el modelo de dominios (JSON -> Models)
        container = load_from_json(domains_path, container_path)

        # 3. Obtener distribución geométrica calculada (Models -> Geometry)
        layout_data = self.layout_engine.calculate_layout(container)

        # 4. Crear los GraphicsItems y agregarlos a la escena (Geometry -> GraphicsItems -> Scene)
        domain_items_map = {}
        all_year_items = []

        # 4.1. Instanciar SuperDomainItems
        for sd, geom in layout_data["superdomains"].items():
            x, y, w, h = geom
            sd_item = SuperDomainItem(x, y, w, h, sd.title)
            scene.addItem(sd_item)

        # 4.2. Instanciar DomainItems
        for domain, geom in layout_data["domains"].items():
            x, y, w, h = geom
            dom_item = DomainItem(
                x=x,
                y=y,
                width=w,
                height=h,
                title=domain.name,
                deuterodomain=domain.deuterodomain,
                exodomain=domain.exodomain
            )
            scene.addItem(dom_item)
            domain_items_map[domain] = dom_item

        # 4.3. Instanciar YearItems como hijos de sus respectivos DomainItems
        for year, geom in layout_data["years"].items():
            x, y, w, h = geom
            parent_domain = year.parent_domain
            dom_item = domain_items_map.get(parent_domain)

            # Instanciar el año, el cual creará automáticamente sus puertos
            y_item = YearItem(
                x=x,
                y=y,
                width=w,
                height=h,
                year_value=year.value,
                parent=dom_item
            )
            all_year_items.append(y_item)

        # 4.4. Instanciar cables simulados de prueba (Commit 9)
        year_2008_item = None
        year_2015_item = None

        for item in all_year_items:
            if item._year_value == 2008:
                year_2008_item = item
            if item._year_value == 2015:
                year_2015_item = item

        # Si ambos años de prueba existen, conectamos el puerto derecho de 2008 al izquierdo de 2015
        if year_2008_item and year_2015_item:
            mock_cable = CableItem(year_2008_item.right_port, year_2015_item.left_port)
            scene.addItem(mock_cable)

        # 5. Configurar SceneRect
        sx, sy, sw, sh = layout_data["scene_rect"]
        scene.setSceneRect(sx, sy, sw, sh)
