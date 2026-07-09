from dataclasses import dataclass, field

@dataclass
class Domain:
    id: str
    title: str
    range_text: str
    start_year: int
    end_year: int
    deuterodomain: str
    exodomain: str
    years: list[int] = field(default_factory=list)

@dataclass
class SuperDomain:
    id: str
    title: str
    domains: list[Domain] = field(default_factory=list)

@dataclass
class Container:
    title: str
    superdomains: list[SuperDomain] = field(default_factory=list)
