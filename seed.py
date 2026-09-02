"""
Наполняет базу demo-данными: 5 гостей, 5 столов, 7 броней.
Специально включён один конфликт (уже забронированный интервал) —
чтобы в GUI/CLI можно было продемонстрировать, что check_table_availability
реально его ловит.

Запуск: python seed.py
"""

from datetime import date, datetime, timedelta

import backend

TODAY = date.today()
TOMORROW = TODAY + timedelta(days=1)


def t(hhmm):
    return datetime.strptime(hhmm, "%H:%M").time()


def run():
    backend.create_tables()

    users = [
        backend.create_user("Ирина Фёдорова", "irina.fedorova@example.com", "+7 900 111-22-33", "предпочитает столик у окна"),
        backend.create_user("Игорь Кузнецов", "igor.kuznetsov@example.com", "+7 900 222-33-44", ""),
        backend.create_user("Мария Соколова", "maria.sokolova@example.com", "+7 900 333-44-55", "аллергия на орехи"),
        backend.create_user("Андрей Волков", "andrey.volkov@example.com", "+7 900 444-55-66", "VIP"),
        backend.create_user("Ольга Смирнова", "olga.smirnova@example.com", "+7 900 555-66-77", ""),
    ]

    tables = [
        backend.create_table(1, capacity=2, location="у окна"),
        backend.create_table(2, capacity=4, location="зал"),
        backend.create_table(3, capacity=4, location="зал"),
        backend.create_table(4, capacity=6, location="терраса"),
        backend.create_table(5, capacity=2, location="барная стойка"),
    ]

    # обычные брони на сегодня
    backend.create_booking(users[0], tables[0], TODAY, t("19:00"), t("21:00"), 2)
    backend.create_booking(users[1], tables[1], TODAY, t("18:00"), t("20:00"), 4)
    backend.create_booking(users[2], tables[2], TODAY, t("20:00"), t("22:00"), 3)

    # бронь на завтра, стол 4 занят вечером
    backend.create_booking(users[3], tables[3], TOMORROW, t("19:00"), t("22:00"), 5)

    # эта бронь у стола 4 на завтра НЕ конфликтует (раньше и с запасом по буферу)
    backend.create_booking(users[4], tables[3], TOMORROW, t("13:00"), t("15:00"), 2)

    # гость с активной бронью, но без визитов "в прошлом" — для примера аналитики
    backend.create_booking(users[4], tables[4], TODAY, t("12:00"), t("13:00"), 1)
    backend.cancel_booking(
        backend.get_all_bookings(booking_date=TODAY)[-1]["id"],
        reason="гость передумал",
    )

    print("Готово: 5 гостей, 5 столов, брони созданы.")
    print(f"Намеренный конфликт для демонстрации: стол №4 на {TOMORROW} уже занят 19:00–22:00.")
    print("Попробуйте в GUI забронировать стол №4 на", TOMORROW, "на 20:00–21:00 — система должна отказать.")


if __name__ == "__main__":
    run()
