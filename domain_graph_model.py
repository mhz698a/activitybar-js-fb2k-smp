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

    @classmethod
    def from_range(
        cls,
        id: str,
        title: str,
        range_text: str,
        deuterodomain: str,
        exodomain: str,
    ) -> 'Domain':
        if "-" not in range_text:
            raise ValueError(f"Invalid range_text format: '{range_text}'. Expected 'YYYY-YYYY'.")

        parts = range_text.split("-")
        if len(parts) != 2:
            raise ValueError(f"Invalid range_text format: '{range_text}'. Expected exactly one '-' separator.")

        try:
            start_year = int(parts[0].strip())
            end_year = int(parts[1].strip())
        except ValueError as e:
            raise ValueError(f"Could not parse years from range_text: '{range_text}'.") from e

        if start_year > end_year:
            raise ValueError(f"start_year ({start_year}) cannot be greater than end_year ({end_year}) in range_text: '{range_text}'.")

        years = list(range(start_year, end_year + 1))

        return cls(
            id=id,
            title=title,
            range_text=range_text,
            start_year=start_year,
            end_year=end_year,
            deuterodomain=deuterodomain,
            exodomain=exodomain,
            years=years
        )

@dataclass
class SuperDomain:
    id: str
    title: str
    domains: list[Domain] = field(default_factory=list)

@dataclass
class Container:
    title: str
    superdomains: list[SuperDomain] = field(default_factory=list)
