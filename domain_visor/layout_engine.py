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
        self.spacing_columns = 20.0
        self.column_height = 450.0

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
        superdomains_geom = {}
        domains_geom = {}
        years_geom = {}

        for i, sd in enumerate(container.superdomains):
            sd_x = self.margin_left + i * (self.column_width + self.spacing_columns)
            sd_y = self.margin_top
            superdomains_geom[sd] = (sd_x, sd_y, self.column_width, self.column_height)

            # Posicionar secuencialmente los DomainItems dentro de este contenedor de columna
            # Se deja un espacio vertical de 50px para el encabezado del SuperDomainItem
            current_y = sd_y + 50.0

            for domain in sd.domains:
                # Altura de cada bloque calculada como: (cantidad de años * altura por año) + 16px de padding
                years_count = len(domain.years)
                domain_height = (years_count * self.year_height) + 16.0

                dom_x = sd_x + 10.0
                dom_y = current_y
                dom_width = self.column_width - 20.0
                domains_geom[domain] = (dom_x, dom_y, dom_width, domain_height)

                # Posicionar YearItems (sus puertos se centran internamente)
                # Se inicia por debajo de la línea divisora del encabezado (28px) más un padding superior de 8px
                year_start_y = dom_y + self.header_height + self.year_top_padding
                for idx, year in enumerate(domain.years):
                    y_pos = year_start_y + idx * self.year_height
                    years_geom[year] = (dom_x, y_pos, dom_width, self.year_height)

                # Avanzar la coordenada Y para el siguiente bloque de dominio más el espacio entre bloques
                current_y += domain_height + self.spacing_blocks

        # Dimensiones totales de la escena para el bounding box
        total_width = self.margin_left + len(container.superdomains) * (self.column_width + self.spacing_columns) + self.margin_left
        total_height = self.margin_top + self.column_height + 50.0
        scene_rect = (0.0, 0.0, float(total_width), float(total_height))

        return {
            "superdomains": superdomains_geom,
            "domains": domains_geom,
            "years": years_geom,
            "scene_rect": scene_rect
        }
