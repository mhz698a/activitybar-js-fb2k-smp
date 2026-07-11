# domain_visor/layout_engine.py

class LayoutEngine:
    """
    Responsabilidad única de diseño y posicionamiento:
    Define constantes de espaciado y calcula la geometría exacta de todos los elementos visuales.

    El renderer ya no calcula posiciones; en su lugar, consume los resultados de esta clase.
    """
    def __init__(self):
        # Constantes de márgenes y geometría del lienzo
        self.margin_left = 30.0
        self.margin_top = 40.0

        # Constantes de columnas de SuperDomain
        self.column_width = 200.0
        self.spacing_columns = 40.0  # Calibrado: incrementado de 20.0 a 40.0 para mayor separación
        self.column_height = 450.0  # Altura por defecto

        # Constantes de bloques de Domain y espaciado
        self.spacing_blocks = 15.0
        self.header_height = 28.0

        # Constantes de YearItem
        self.year_height = 15.0
        self.year_top_padding = 8.0

    def calculate_layout(self, container):
        """
        Calcula la geometría (x, y, ancho, alto) para cada SuperDomain, Domain y Year.

        Retorna un diccionario estructurado:
            {
                "superdomains": {sd_obj: (x, y, w, h)},
                "domains": {domain_obj: (x, y, w, h)},
                "years": {year_obj: (x, y, w, h)},
                "scene_rect": (x, y, w, h)
            }
        """
        # Paso de Calibración (Commit 12.1):
        # Primero, calculamos dinámicamente la altura necesaria para cada columna de SuperDomain,
        # previniendo desbordamientos (overflows) si hay muchos dominios o años en una columna.
        max_needed_height = self.column_height

        for sd in container.superdomains:
            # Espacio vertical inicial: 50px de espacio superior para el título de la columna
            col_height = 50.0
            for domain in sd.domains:
                # Altura correcta del dominio considerando: encabezado (28px) + padding superior (8px)
                # + (años * 15px) + padding inferior (8px)
                years_count = len(domain.years)
                domain_height = self.header_height + self.year_top_padding + (years_count * self.year_height) + self.year_top_padding
                col_height += domain_height + self.spacing_blocks

            # Dejamos un margen inferior de padding al final de la columna
            col_height += 15.0
            if col_height > max_needed_height:
                max_needed_height = col_height

        # Asignamos la altura de columna calculada dinámicamente
        active_column_height = max_needed_height

        superdomains_geom = {}
        domains_geom = {}
        years_geom = {}

        for i, sd in enumerate(container.superdomains):
            sd_x = self.margin_left + i * (self.column_width + self.spacing_columns)
            sd_y = self.margin_top
            superdomains_geom[sd] = (sd_x, sd_y, self.column_width, active_column_height)

            # Posicionar secuencialmente los DomainItems dentro de este contenedor de columna
            # Se deja un espacio vertical de 50px para el encabezado del SuperDomainItem
            current_y = sd_y + 50.0

            for domain in sd.domains:
                # Altura calibrada del bloque de dominio
                years_count = len(domain.years)
                domain_height = self.header_height + self.year_top_padding + (years_count * self.year_height) + self.year_top_padding

                dom_x = sd_x + 10.0
                dom_y = current_y
                dom_width = self.column_width - 20.0
                domains_geom[domain] = (dom_x, dom_y, dom_width, domain_height)

                # Posicionar YearItems
                year_start_y = dom_y + self.header_height + self.year_top_padding
                for idx, year in enumerate(domain.years):
                    y_pos = year_start_y + idx * self.year_height
                    years_geom[year] = (dom_x, y_pos, dom_width, self.year_height)

                # Avanzar la coordenada Y para el siguiente bloque de dominio más el espacio entre bloques
                current_y += domain_height + self.spacing_blocks

        # Dimensiones totales de la escena para el bounding box
        total_width = self.margin_left + len(container.superdomains) * (self.column_width + self.spacing_columns) + self.margin_left
        total_height = self.margin_top + active_column_height + 50.0
        scene_rect = (0.0, 0.0, float(total_width), float(total_height))

        return {
            "superdomains": superdomains_geom,
            "domains": domains_geom,
            "years": years_geom,
            "scene_rect": scene_rect
        }
