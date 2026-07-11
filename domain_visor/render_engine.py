# domain_visor/render_engine.py

from domain_visor.models import load_from_json
from domain_visor.superdomain_item import SuperDomainItem
from domain_visor.domain_item import DomainItem
from domain_visor.year_item import YearItem

class RenderEngine:
    """
    Responsabilidad única de renderizado:
    JSON -> Models -> GraphicsItems -> Scene.

    Nada más.
    """
    def __init__(self):
        pass

    def render(self, scene, container_path, domains_path):
        """
        Limpia la escena, carga el modelo desde los archivos JSON,
        crea e instancia todos los GraphicsItems correspondientes,
        los agrega a la escena y ajusta el SceneRect.
        """
        # 1. Limpiar escena
        scene.clear()

        # 2. Cargar el modelo de dominios (JSON -> Models)
        container = load_from_json(domains_path, container_path)

        # 3. Diseñar y distribuir elementos visuales en la escena (Models -> GraphicsItems -> Scene)
        margin_left = 30
        margin_top = 40
        column_width = 200
        spacing_columns = 20
        column_height = 450
        spacing_blocks = 15

        for i, sd in enumerate(container.superdomains):
            x = margin_left + i * (column_width + spacing_columns)
            y = margin_top

            # Instanciar el SuperDomainItem contenedor
            sd_item = SuperDomainItem(x, y, column_width, column_height, sd.title)
            scene.addItem(sd_item)

            # Posicionar los DomainItems secuencialmente dentro de esta columna
            current_y = y + 50  # Deja espacio para el título del SuperDomainItem

            for domain in sd.domains:
                # Altura de cada bloque de dominio basada en la cantidad de años en el modelo
                years_count = len(domain.years)
                domain_height = (years_count * 15) + 16

                # Instanciar DomainItem dentro de la columna
                dom_item = DomainItem(
                    x=x + 10,  # 10px de margen a la izquierda dentro de la columna
                    y=current_y,
                    width=column_width - 20,  # 10px de margen a cada lado
                    height=domain_height,
                    title=domain.name,
                    deuterodomain=domain.deuterodomain,
                    exodomain=domain.exodomain
                )
                scene.addItem(dom_item)

                # Instanciar YearItems como hijos de este DomainItem
                # El encabezado mide 28px de alto. Con un top padding de 8px empezamos en +36px
                year_start_y = current_y + 36.0
                for idx, year in enumerate(domain.years):
                    y_pos = year_start_y + idx * 15.0
                    YearItem(
                        x=x + 10,
                        y=y_pos,
                        width=column_width - 20,
                        height=15,
                        year_value=year.value,
                        parent=dom_item
                    )

                # Avanzar current_y para el próximo dominio en la columna
                current_y += domain_height + spacing_blocks

        # 4. Configurar SceneRect para acomodar todos los ítems agregados
        total_width = margin_left + len(container.superdomains) * (column_width + spacing_columns) + margin_left
        total_height = margin_top + column_height + 50
        scene.setSceneRect(0.0, 0.0, float(total_width), float(total_height))
