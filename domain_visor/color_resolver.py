# domain_visor/color_resolver.py

from domain_visor.theme import Theme

class ColorResolver:
    """
    Responsabilidad única:
    Convertir un `role` de dominio en colores visuales (fondo, borde) en formato hex,
    obteniendo los valores desde la clase central Theme.

    Reglas:
    - No debe importar PyQt6.
    - No debe conocer DomainItem.
    - No debe acceder a modelos.
    - Debe contener únicamente reglas lógicas de mapeo visual.
    """
    @staticmethod
    def resolve_colors(role: str) -> tuple[str, str]:
        # Obtener color de borde desde el tema centralizado
        border_color = Theme.DOMAIN_BORDER

        # Mapear roles lógicos a variables de colores del tema centralizado
        if role == "exodomain_aurora_maya":
            bg_color = Theme.ROLE_EXODOMAIN_BG
        elif role == "deuterodomain_alejandra_maya":
            bg_color = Theme.ROLE_DEUTERODOMAIN_BG
        else:
            bg_color = Theme.ROLE_DEFAULT_BG

        return bg_color, border_color
