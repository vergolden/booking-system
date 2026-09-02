from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """Гость системы бронирования."""
    name: str
    email: str
    phone: str = ""
    notes: str = ""  # предпочтения, аллергии, VIP-отметка и т.п.
    id: Optional[int] = None
    created_at: Optional[datetime] = None
