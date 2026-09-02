"""
Хелпер для работы с PostgreSQL для мини-системы бронирования столиков.

Тот же принцип, что и в ДЗ про users/orders: драйвер знает только, как
подключиться к базе и выполнить SQL. Бизнес-логика (что такое "создать
бронирование" или "проверить доступность стола") живёт в backend.py —
драйвер про это ничего не знает.
"""

import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()


class PostgresDriver:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        if self.conn and not self.conn.closed:
            self.conn.close()

    # ---------- Схема ----------

    def create_tables(self):
        with self.conn, self.conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id         SERIAL PRIMARY KEY,
                    name       TEXT NOT NULL,
                    email      TEXT NOT NULL UNIQUE,
                    phone      TEXT DEFAULT '',
                    notes      TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT NOW()
                );
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS restaurant_tables (
                    id           SERIAL PRIMARY KEY,
                    table_number INT NOT NULL UNIQUE,
                    capacity     INT NOT NULL CHECK (capacity > 0),
                    location     TEXT DEFAULT 'зал',
                    status       TEXT NOT NULL DEFAULT 'available'
                                 CHECK (status IN ('available', 'occupied', 'maintenance'))
                );
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS bookings (
                    id            SERIAL PRIMARY KEY,
                    user_id       INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    table_id      INT NOT NULL REFERENCES restaurant_tables(id) ON DELETE CASCADE,
                    booking_date  DATE NOT NULL,
                    start_time    TIME NOT NULL,
                    end_time      TIME NOT NULL CHECK (end_time > start_time),
                    guests_count  INT NOT NULL CHECK (guests_count > 0),
                    status        TEXT NOT NULL DEFAULT 'confirmed'
                                  CHECK (status IN ('confirmed', 'cancelled', 'completed', 'no_show')),
                    cancel_reason TEXT DEFAULT '',
                    created_at    TIMESTAMP DEFAULT NOW()
                );
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_bookings_table_date
                ON bookings (table_id, booking_date);
                """
            )
            # PostgreSQL не умеет проверять данные из другой таблицы прямо в CHECK,
            # поэтому "гостей не больше вместимости стола" проверяем триггером —
            # тот же приём, что и с возрастом участников в ДЗ про спортклуб.
            cur.execute(
                """
                CREATE OR REPLACE FUNCTION check_booking_capacity() RETURNS TRIGGER AS $$
                DECLARE
                    table_capacity INT;
                BEGIN
                    SELECT capacity INTO table_capacity
                    FROM restaurant_tables WHERE id = NEW.table_id;

                    IF NEW.guests_count > table_capacity THEN
                        RAISE EXCEPTION
                            'guests_count (%) exceeds table capacity (%)',
                            NEW.guests_count, table_capacity;
                    END IF;
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
                """
            )
            cur.execute(
                """
                DROP TRIGGER IF EXISTS trg_booking_capacity ON bookings;
                CREATE TRIGGER trg_booking_capacity
                BEFORE INSERT OR UPDATE ON bookings
                FOR EACH ROW EXECUTE FUNCTION check_booking_capacity();
                """
            )

    # ---------- Универсальные обёртки над psycopg2 ----------

    def execute_write(self, query, params=None):
        """INSERT/UPDATE/DELETE без RETURNING — возвращает число задетых строк."""
        with self.conn, self.conn.cursor() as cur:
            cur.execute(query, params or ())
            return cur.rowcount

    def execute_returning_id(self, query, params=None):
        """INSERT ... RETURNING id — возвращает id новой строки."""
        with self.conn, self.conn.cursor() as cur:
            cur.execute(query, params or ())
            return cur.fetchone()[0]

    def fetch_all(self, query, params=None):
        with self.conn.cursor() as cur:
            cur.execute(query, params or ())
            columns = [desc[0] for desc in cur.description]
            return columns, cur.fetchall()

    def fetch_one(self, query, params=None):
        with self.conn.cursor() as cur:
            cur.execute(query, params or ())
            row = cur.fetchone()
            if row is None:
                return None, None
            columns = [desc[0] for desc in cur.description]
            return columns, row
