# domain_visor/color_resolver.py

class ColorResolver:
    """
    Responsabilidad única:
    Convertir un `role` de dominio en colores visuales (fondo, borde) en formato hex.

    Reglas:
    - No debe importar PyQt6.
    - No debe conocer DomainItem.
    - No debe acceder a modelos.
    - Debe contener únicamente reglas visuales de color.
    """
    @staticmethod
    def resolve_colors(role: str) -> tuple[str, str]:
        # Borde blanco por defecto según el diseño actual del visor
        border_color = "#ffffff"

        if role == "exodomain_aurora_maya":
            bg_color = "#2b73d6"      # Azul
        elif role == "deuterodomain_alejandra_maya":
            bg_color = "#b93a82"      # Rosa/Magenta
        else:
            bg_color = "#7c3ab9"      # Morado/Púrpura por defecto

        return bg_color, border_color
