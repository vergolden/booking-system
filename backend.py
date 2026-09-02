"""
Бизнес-логика мини-системы бронирования: CRUD для гостей, столов и броней,
проверка доступности стола и небольшая аналитика.

Драйвер (postgres_driver.py) ничего не знает про "бронирование" — здесь мы
собираем из его универсальных методов конкретные операции, как в уроке:
"сделай функции для файла backend.py, а не для драйвера базы данных".
"""

from datetime import date, datetime, timedelta

from postgres_driver import PostgresDriver

DEFAULT_BUFFER_MINUTES = 15  # запас на уборку/пересадку стола между бронями


def _rows_to_dicts(columns, rows):
    return [dict(zip(columns, row)) for row in rows]


def create_tables():
    with PostgresDriver() as db:
        db.create_tables()


# ==================== USERS ====================

def create_user(name, email, phone="", notes=""):
    with PostgresDriver() as db:
        return db.execute_returning_id(
            "INSERT INTO users (name, email, phone, notes) VALUES (%s, %s, %s, %s) RETURNING id;",
            (name, email, phone, notes),
        )


def get_all_users():
    with PostgresDriver() as db:
        columns, rows = db.fetch_all(
            "SELECT id, name, email, phone, notes, created_at FROM users ORDER BY id;"
        )
        return _rows_to_dicts(columns, rows)


def get_user_by_id(user_id):
    with PostgresDriver() as db:
        columns, row = db.fetch_one(
            "SELECT id, name, email, phone, notes, created_at FROM users WHERE id = %s;",
            (user_id,),
        )
        return dict(zip(columns, row)) if row else None


def update_user(user_id, name, email, phone, notes):
    with PostgresDriver() as db:
        return db.execute_write(
            "UPDATE users SET name = %s, email = %s, phone = %s, notes = %s WHERE id = %s;",
            (name, email, phone, notes, user_id),
        )


def delete_user(user_id):
    with PostgresDriver() as db:
        return db.execute_write("DELETE FROM users WHERE id = %s;", (user_id,))


# ==================== TABLES ====================

def create_table(table_number, capacity, location="зал", status="available"):
    with PostgresDriver() as db:
        return db.execute_returning_id(
            """INSERT INTO restaurant_tables (table_number, capacity, location, status)
               VALUES (%s, %s, %s, %s) RETURNING id;""",
            (table_number, capacity, location, status),
        )


def get_all_tables():
    with PostgresDriver() as db:
        columns, rows = db.fetch_all(
            "SELECT id, table_number, capacity, location, status FROM restaurant_tables ORDER BY table_number;"
        )
        return _rows_to_dicts(columns, rows)


def get_table_by_id(table_id):
    with PostgresDriver() as db:
        columns, row = db.fetch_one(
            "SELECT id, table_number, capacity, location, status FROM restaurant_tables WHERE id = %s;",
            (table_id,),
        )
        return dict(zip(columns, row)) if row else None


def update_table(table_id, table_number, capacity, location, status):
    with PostgresDriver() as db:
        return db.execute_write(
            """UPDATE restaurant_tables
               SET table_number = %s, capacity = %s, location = %s, status = %s
               WHERE id = %s;""",
            (table_number, capacity, location, status, table_id),
        )


def delete_table(table_id):
    with PostgresDriver() as db:
        return db.execute_write("DELETE FROM restaurant_tables WHERE id = %s;", (table_id,))


# ==================== BOOKINGS ====================

def check_table_availability(table_id, booking_date, start_time, end_time,
                              buffer_minutes=DEFAULT_BUFFER_MINUTES, exclude_booking_id=None):
    """
    Проверяет, свободен ли стол на [start_time, end_time] в booking_date.

    Учитывает буфер (по умолчанию 15 минут) до и после уже существующих
    подтверждённых броней того же стола — время на уборку/пересадку.
    Без буфера две брони "18:00-19:00" и "19:00-20:00" формально не пересекаются,
    но реальному ресторану нужно время между гостями.

    Возвращает (True, None), если можно бронировать, иначе (False, "причина").
    """
    with PostgresDriver() as db:
        query = """
            SELECT id, start_time, end_time
            FROM bookings
            WHERE table_id = %s AND booking_date = %s AND status = 'confirmed'
        """
        params = [table_id, booking_date]
        if exclude_booking_id is not None:
            query += " AND id != %s"
            params.append(exclude_booking_id)
        columns, rows = db.fetch_all(query, tuple(params))

    buffer = timedelta(minutes=buffer_minutes)
    anchor = date.today()
    new_start = datetime.combine(anchor, start_time) - buffer
    new_end = datetime.combine(anchor, end_time) + buffer

    for row in rows:
        existing = dict(zip(columns, row))
        exist_start = datetime.combine(anchor, existing["start_time"])
        exist_end = datetime.combine(anchor, existing["end_time"])
        if new_start < exist_end and exist_start < new_end:
            return False, (
                f"пересекается с бронью #{existing['id']} "
                f"({existing['start_time']}–{existing['end_time']}, буфер {buffer_minutes} мин)"
            )

    return True, None


def create_booking(user_id, table_id, booking_date, start_time, end_time, guests_count):
    available, reason = check_table_availability(table_id, booking_date, start_time, end_time)
    if not available:
        raise ValueError(f"Стол недоступен: {reason}")

    with PostgresDriver() as db:
        return db.execute_returning_id(
            """INSERT INTO bookings (user_id, table_id, booking_date, start_time, end_time, guests_count)
               VALUES (%s, %s, %s, %s, %s, %s) RETURNING id;""",
            (user_id, table_id, booking_date, start_time, end_time, guests_count),
        )


def get_all_bookings(booking_date=None, status=None, table_id=None):
    """Список броней с именем гостя и номером стола. Параметры — необязательные фильтры."""
    query = """
        SELECT b.id, b.user_id, u.name AS user_name, b.table_id, t.table_number,
               b.booking_date, b.start_time, b.end_time, b.guests_count,
               b.status, b.cancel_reason, b.created_at
        FROM bookings b
        JOIN users u ON u.id = b.user_id
        JOIN restaurant_tables t ON t.id = b.table_id
        WHERE 1 = 1
    """
    params = []
    if booking_date is not None:
        query += " AND b.booking_date = %s"
        params.append(booking_date)
    if status is not None:
        query += " AND b.status = %s"
        params.append(status)
    if table_id is not None:
        query += " AND b.table_id = %s"
        params.append(table_id)
    query += " ORDER BY b.booking_date, b.start_time;"

    with PostgresDriver() as db:
        columns, rows = db.fetch_all(query, tuple(params))
        return _rows_to_dicts(columns, rows)


def get_booking_by_id(booking_id):
    with PostgresDriver() as db:
        columns, row = db.fetch_one(
            """SELECT id, user_id, table_id, booking_date, start_time, end_time,
                      guests_count, status, cancel_reason, created_at
               FROM bookings WHERE id = %s;""",
            (booking_id,),
        )
        return dict(zip(columns, row)) if row else None


def update_booking(booking_id, user_id, table_id, booking_date, start_time, end_time, guests_count):
    available, reason = check_table_availability(
        table_id, booking_date, start_time, end_time, exclude_booking_id=booking_id
    )
    if not available:
        raise ValueError(f"Стол недоступен: {reason}")

    with PostgresDriver() as db:
        return db.execute_write(
            """UPDATE bookings
               SET user_id = %s, table_id = %s, booking_date = %s,
                   start_time = %s, end_time = %s, guests_count = %s
               WHERE id = %s;""",
            (user_id, table_id, booking_date, start_time, end_time, guests_count, booking_id),
        )


def cancel_booking(booking_id, reason=""):
    with PostgresDriver() as db:
        return db.execute_write(
            "UPDATE bookings SET status = 'cancelled', cancel_reason = %s WHERE id = %s;",
            (reason, booking_id),
        )


def mark_booking_completed(booking_id):
    with PostgresDriver() as db:
        return db.execute_write(
            "UPDATE bookings SET status = 'completed' WHERE id = %s;", (booking_id,)
        )


def mark_booking_no_show(booking_id):
    with PostgresDriver() as db:
        return db.execute_write(
            "UPDATE bookings SET status = 'no_show' WHERE id = %s;", (booking_id,)
        )


def delete_booking(booking_id):
    with PostgresDriver() as db:
        return db.execute_write("DELETE FROM bookings WHERE id = %s;", (booking_id,))


# ==================== АНАЛИТИКА ====================

def get_table_load_stats():
    """Сколько подтверждённых/завершённых броней приходится на каждый стол — где нагрузка выше."""
    with PostgresDriver() as db:
        columns, rows = db.fetch_all(
            """
            SELECT t.table_number, t.capacity, COUNT(b.id) AS bookings_count
            FROM restaurant_tables t
            LEFT JOIN bookings b ON b.table_id = t.id AND b.status IN ('confirmed', 'completed')
            GROUP BY t.id, t.table_number, t.capacity
            ORDER BY bookings_count DESC, t.table_number;
            """
        )
        return _rows_to_dicts(columns, rows)


def get_status_breakdown():
    """Распределение броней по статусам, включая долю отмен и неявок."""
    with PostgresDriver() as db:
        columns, rows = db.fetch_all(
            """
            SELECT status, COUNT(*) AS total,
                   ROUND(100.0 * COUNT(*) / NULLIF(SUM(COUNT(*)) OVER (), 0), 1) AS percent
            FROM bookings
            GROUP BY status
            ORDER BY total DESC;
            """
        )
        return _rows_to_dicts(columns, rows)
