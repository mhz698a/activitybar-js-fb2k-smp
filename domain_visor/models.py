# domain_visor/models.py

import json
import os

class Year:
    def __init__(self, value: int, parent_domain=None):
        self.value = value
        self.parent_domain = parent_domain

    def __repr__(self):
        return f"Year({self.value})"


class Domain:
    def __init__(self, name: str, range_text: str, start_year: int, end_year: int, years: list = None, role: str = "", norm_baas: str = ""):
        self.name = name
        self.range_text = range_text
        self.start_year = start_year
        self.end_year = end_year
        self.years = years if years is not None else []
        self.role = role
        self.norm_baas = norm_baas

    def __repr__(self):
        return f"Domain(name={self.name}, range={self.range_text}, years_count={len(self.years)})"


class SuperDomain:
    def __init__(self, name: str, title: str, domains: list = None):
        self.name = name
        self.title = title
        self.domains = domains if domains is not None else []

    def __repr__(self):
        return f"SuperDomain(name={self.name}, title={self.title}, domains_count={len(self.domains)})"


class Container:
    def __init__(self, title: str, superdomains: list = None):
        self.title = title
        self.superdomains = superdomains if superdomains is not None else []

    def __repr__(self):
        return f"Container(title={self.title}, superdomains_count={len(self.superdomains)})"


class Connection:
    def __init__(self, from_year: int, to_year: int, name: str, type: str):
        self.from_year = from_year
        self.to_year = to_year
        self.name = name
        self.type = type

    def __repr__(self):
        return f"Connection(from={self.from_year}, to={self.to_year}, name={self.name}, type={self.type})"


def load_from_json(domains_path: str, container_path: str) -> Container:
    """
    Loads JSON data from container_path and domains_path,
    transforms them into a Container object hierarchy, and returns it.
    This is the only function that reads JSON and creates model objects.
    """
    # 1. Load container title
    container_title = "Contenedor Desconocido"
    if os.path.exists(container_path):
        try:
            with open(container_path, 'r', encoding='utf-8') as f:
                c_data = json.load(f)
                if isinstance(c_data, list) and len(c_data) > 0:
                    container_title = c_data[0].get("title_container", "Sin Título")
        except Exception:
            pass

    # 2. Load domains data
    domains_data = []
    if os.path.exists(domains_path):
        try:
            with open(domains_path, 'r', encoding='utf-8') as f:
                domains_data = json.load(f)
        except Exception:
            pass

    # 3. Build hierarchy
    # Group domains by superdomain to preserve order of first appearance
    superdomains_map = {}
    superdomains_list = []

    for item in domains_data:
        sd_name = item.get("superdomain", "")
        if not sd_name:
            continue

        if sd_name not in superdomains_map:
            sd_title = sd_name.replace("_", " ").title()
            sd_obj = SuperDomain(name=sd_name, title=sd_title)
            superdomains_map[sd_name] = sd_obj
            superdomains_list.append(sd_obj)

        sd_obj = superdomains_map[sd_name]

        # Parse range, start_year, end_year
        range_text = item.get("range", "")
        try:
            start_year, end_year = map(int, range_text.split("-"))
        except Exception:
            start_year, end_year = 0, 0

        # Extract role and norm_baas
        role = item.get("role", "")
        norm_baas = item.get("norm_BaaS", item.get("norm_baas", ""))

        # Instantiate Domain (initially without years)
        domain_name = item.get("domain", "")
        domain_obj = Domain(
            name=domain_name,
            range_text=range_text,
            start_year=start_year,
            end_year=end_year,
            years=[],
            role=role,
            norm_baas=norm_baas
        )

        # Build Year objects and set their parent_domain reference
        years = []
        if start_year and end_year:
            for y in range(start_year, end_year + 1):
                years.append(Year(value=y, parent_domain=domain_obj))
        domain_obj.years = years

        # Add domain to the superdomain
        sd_obj.domains.append(domain_obj)

    return Container(title=container_title, superdomains=superdomains_list)
