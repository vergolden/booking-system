from dataclasses import dataclass
from typing import Optional


@dataclass
class Table:
    """Столик в ресторане."""
    number: int
    capacity: int
    location: str = "зал"
    status: str = "available"  # available | occupied | maintenance
    id: Optional[int] = None
