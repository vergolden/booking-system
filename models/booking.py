from dataclasses import dataclass
from datetime import date, time, datetime
from typing import Optional


@dataclass
class Booking:
    """Бронирование столика гостем на определённый интервал времени."""
    user_id: int
    table_id: int
    booking_date: date
    start_time: time
    end_time: time
    guests_count: int
    status: str = "confirmed"  # confirmed | cancelled | completed | no_show
    cancel_reason: str = ""
    id: Optional[int] = None
    created_at: Optional[datetime] = None
