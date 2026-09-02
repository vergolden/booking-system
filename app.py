"""
Графический интерфейс мини-системы бронирования столиков (tkinter).

Три вкладки — Гости / Столы / Брони — плюс Аналитика. Вся логика (CRUD,
проверка доступности, статистика) уже реализована в backend.py — здесь
только форма, таблица и вызовы этих функций.
"""

import tkinter as tk
from datetime import datetime
from tkinter import messagebox, simpledialog, ttk

import backend

STATUS_LABELS = {
    "confirmed": "подтверждена",
    "cancelled": "отменена",
    "completed": "завершена",
    "no_show": "неявка",
}


def parse_date(text):
    return datetime.strptime(text.strip(), "%Y-%m-%d").date()


def parse_time(text):
    return datetime.strptime(text.strip(), "%H:%M").time()


class UsersTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=10)
        self.selected_id = None
        self._build_form()
        self._build_table()
        self.refresh()

    def _build_form(self):
        form = ttk.LabelFrame(self, text="Гость", padding=10)
        form.pack(fill="x", pady=(0, 10))

        ttk.Label(form, text="Имя").grid(row=0, column=0, sticky="w")
        self.name_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.name_var, width=30).grid(row=0, column=1, padx=5)

        ttk.Label(form, text="Email").grid(row=0, column=2, sticky="w")
        self.email_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.email_var, width=30).grid(row=0, column=3, padx=5)

        ttk.Label(form, text="Телефон").grid(row=1, column=0, sticky="w")
        self.phone_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.phone_var, width=30).grid(row=1, column=1, padx=5)

        ttk.Label(form, text="Заметки").grid(row=1, column=2, sticky="w")
        self.notes_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.notes_var, width=30).grid(row=1, column=3, padx=5)

        buttons = ttk.Frame(form)
        buttons.grid(row=2, column=0, columnspan=4, pady=(10, 0))
        ttk.Button(buttons, text="Добавить", command=self.add_user).pack(side="left", padx=5)
        ttk.Button(buttons, text="Сохранить изменения", command=self.update_user).pack(side="left", padx=5)
        ttk.Button(buttons, text="Удалить", command=self.delete_user).pack(side="left", padx=5)
        ttk.Button(buttons, text="Очистить форму", command=self.clear_form).pack(side="left", padx=5)

    def _build_table(self):
        columns = ("id", "name", "email", "phone", "notes")
        headers = {"id": "ID", "name": "Имя", "email": "Email", "phone": "Телефон", "notes": "Заметки"}
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=10)
        for col in columns:
            self.tree.heading(col, text=headers[col])
            self.tree.column(col, width=140 if col != "id" else 40)
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for user in backend.get_all_users():
            self.tree.insert("", "end", values=(
                user["id"], user["name"], user["email"], user["phone"], user["notes"]
            ))

    def on_select(self, _event):
        selection = self.tree.selection()
        if not selection:
            return
        values = self.tree.item(selection[0], "values")
        self.selected_id = int(values[0])
        self.name_var.set(values[1])
        self.email_var.set(values[2])
        self.phone_var.set(values[3])
        self.notes_var.set(values[4])

    def clear_form(self):
        self.selected_id = None
        self.name_var.set("")
        self.email_var.set("")
        self.phone_var.set("")
        self.notes_var.set("")

    def add_user(self):
        if not self.name_var.get() or not self.email_var.get():
            messagebox.showwarning("Проверка", "Имя и Email обязательны.")
            return
        try:
            new_id = backend.create_user(
                self.name_var.get(), self.email_var.get(), self.phone_var.get(), self.notes_var.get()
            )
        except Exception as exc:
            messagebox.showerror("Ошибка", str(exc))
            return
        messagebox.showinfo("Готово", f"Гость добавлен, ID {new_id}.")
        self.clear_form()
        self.refresh()

    def update_user(self):
        if self.selected_id is None:
            messagebox.showwarning("Проверка", "Сначала выберите гостя в таблице.")
            return
        try:
            backend.update_user(
                self.selected_id, self.name_var.get(), self.email_var.get(),
                self.phone_var.get(), self.notes_var.get()
            )
        except Exception as exc:
            messagebox.showerror("Ошибка", str(exc))
            return
        messagebox.showinfo("Готово", "Данные гостя обновлены.")
        self.refresh()

    def delete_user(self):
        if self.selected_id is None:
            messagebox.showwarning("Проверка", "Сначала выберите гостя в таблице.")
            return
        if not messagebox.askyesno("Подтверждение", "Удалить гостя? Все его брони тоже удалятся."):
            return
        backend.delete_user(self.selected_id)
        self.clear_form()
        self.refresh()


class TablesTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=10)
        self.selected_id = None
        self._build_form()
        self._build_table()
        self.refresh()

    def _build_form(self):
        form = ttk.LabelFrame(self, text="Стол", padding=10)
        form.pack(fill="x", pady=(0, 10))

        ttk.Label(form, text="Номер").grid(row=0, column=0, sticky="w")
        self.number_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.number_var, width=10).grid(row=0, column=1, padx=5)

        ttk.Label(form, text="Вместимость").grid(row=0, column=2, sticky="w")
        self.capacity_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.capacity_var, width=10).grid(row=0, column=3, padx=5)

        ttk.Label(form, text="Расположение").grid(row=1, column=0, sticky="w")
        self.location_var = tk.StringVar(value="зал")
        ttk.Entry(form, textvariable=self.location_var, width=20).grid(row=1, column=1, padx=5)

        ttk.Label(form, text="Статус").grid(row=1, column=2, sticky="w")
        self.status_var = tk.StringVar(value="available")
        ttk.Combobox(
            form, textvariable=self.status_var, width=17, state="readonly",
            values=["available", "occupied", "maintenance"],
        ).grid(row=1, column=3, padx=5)

        buttons = ttk.Frame(form)
        buttons.grid(row=2, column=0, columnspan=4, pady=(10, 0))
        ttk.Button(buttons, text="Добавить", command=self.add_table).pack(side="left", padx=5)
        ttk.Button(buttons, text="Сохранить изменения", command=self.update_table).pack(side="left", padx=5)
        ttk.Button(buttons, text="Удалить", command=self.delete_table).pack(side="left", padx=5)
        ttk.Button(buttons, text="Очистить форму", command=self.clear_form).pack(side="left", padx=5)

    def _build_table(self):
        columns = ("id", "table_number", "capacity", "location", "status")
        headers = {"id": "ID", "table_number": "№", "capacity": "Мест", "location": "Расположение", "status": "Статус"}
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=10)
        for col in columns:
            self.tree.heading(col, text=headers[col])
            self.tree.column(col, width=100 if col != "id" else 40)
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for table in backend.get_all_tables():
            self.tree.insert("", "end", values=(
                table["id"], table["table_number"], table["capacity"], table["location"], table["status"]
            ))

    def on_select(self, _event):
        selection = self.tree.selection()
        if not selection:
            return
        values = self.tree.item(selection[0], "values")
        self.selected_id = int(values[0])
        self.number_var.set(values[1])
        self.capacity_var.set(values[2])
        self.location_var.set(values[3])
        self.status_var.set(values[4])

    def clear_form(self):
        self.selected_id = None
        self.number_var.set("")
        self.capacity_var.set("")
        self.location_var.set("зал")
        self.status_var.set("available")

    def add_table(self):
        try:
            number = int(self.number_var.get())
            capacity = int(self.capacity_var.get())
        except ValueError:
            messagebox.showwarning("Проверка", "Номер и вместимость должны быть числами.")
            return
        try:
            new_id = backend.create_table(number, capacity, self.location_var.get(), self.status_var.get())
        except Exception as exc:
            messagebox.showerror("Ошибка", str(exc))
            return
        messagebox.showinfo("Готово", f"Стол добавлен, ID {new_id}.")
        self.clear_form()
        self.refresh()

    def update_table(self):
        if self.selected_id is None:
            messagebox.showwarning("Проверка", "Сначала выберите стол в таблице.")
            return
        try:
            number = int(self.number_var.get())
            capacity = int(self.capacity_var.get())
            backend.update_table(self.selected_id, number, capacity, self.location_var.get(), self.status_var.get())
        except Exception as exc:
            messagebox.showerror("Ошибка", str(exc))
            return
        messagebox.showinfo("Готово", "Данные стола обновлены.")
        self.refresh()

    def delete_table(self):
        if self.selected_id is None:
            messagebox.showwarning("Проверка", "Сначала выберите стол в таблице.")
            return
        if not messagebox.askyesno("Подтверждение", "Удалить стол? Все его брони тоже удалятся."):
            return
        backend.delete_table(self.selected_id)
        self.clear_form()
        self.refresh()


class BookingsTab(ttk.Frame):
    def __init__(self, parent, users_tab, tables_tab):
        super().__init__(parent, padding=10)
        self.users_tab = users_tab
        self.tables_tab = tables_tab
        self.selected_id = None
        self._build_form()
        self._build_filters()
        self._build_table()
        self.refresh()

    def _combo_maps(self):
        users = backend.get_all_users()
        tables = backend.get_all_tables()
        self.user_by_label = {f"{u['id']} — {u['name']}": u["id"] for u in users}
        self.table_by_label = {f"№{t['table_number']} (до {t['capacity']} чел., {t['location']})": t["id"] for t in tables}
        return list(self.user_by_label), list(self.table_by_label)

    def _build_form(self):
        form = ttk.LabelFrame(self, text="Бронирование", padding=10)
        form.pack(fill="x", pady=(0, 10))

        user_labels, table_labels = self._combo_maps()

        ttk.Label(form, text="Гость").grid(row=0, column=0, sticky="w")
        self.user_var = tk.StringVar()
        self.user_combo = ttk.Combobox(form, textvariable=self.user_var, width=28, state="readonly", values=user_labels)
        self.user_combo.grid(row=0, column=1, padx=5)

        ttk.Label(form, text="Стол").grid(row=0, column=2, sticky="w")
        self.table_var = tk.StringVar()
        self.table_combo = ttk.Combobox(form, textvariable=self.table_var, width=28, state="readonly", values=table_labels)
        self.table_combo.grid(row=0, column=3, padx=5)

        ttk.Label(form, text="Дата (ГГГГ-ММ-ДД)").grid(row=1, column=0, sticky="w")
        self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(form, textvariable=self.date_var, width=15).grid(row=1, column=1, padx=5, sticky="w")

        ttk.Label(form, text="Начало (ЧЧ:ММ)").grid(row=1, column=2, sticky="w")
        self.start_var = tk.StringVar(value="19:00")
        ttk.Entry(form, textvariable=self.start_var, width=15).grid(row=1, column=3, padx=5, sticky="w")

        ttk.Label(form, text="Конец (ЧЧ:ММ)").grid(row=2, column=0, sticky="w")
        self.end_var = tk.StringVar(value="21:00")
        ttk.Entry(form, textvariable=self.end_var, width=15).grid(row=2, column=1, padx=5, sticky="w")

        ttk.Label(form, text="Гостей").grid(row=2, column=2, sticky="w")
        self.guests_var = tk.StringVar(value="2")
        ttk.Entry(form, textvariable=self.guests_var, width=15).grid(row=2, column=3, padx=5, sticky="w")

        buttons = ttk.Frame(form)
        buttons.grid(row=3, column=0, columnspan=4, pady=(10, 0))
        ttk.Button(buttons, text="Проверить доступность", command=self.check_availability).pack(side="left", padx=5)
        ttk.Button(buttons, text="Создать бронь", command=self.add_booking).pack(side="left", padx=5)
        ttk.Button(buttons, text="Отменить бронь", command=self.cancel_booking).pack(side="left", padx=5)
        ttk.Button(buttons, text="Завершена", command=self.complete_booking).pack(side="left", padx=5)
        ttk.Button(buttons, text="Неявка", command=self.no_show_booking).pack(side="left", padx=5)
        ttk.Button(buttons, text="Удалить", command=self.delete_booking).pack(side="left", padx=5)

    def _build_filters(self):
        filters = ttk.LabelFrame(self, text="Фильтры", padding=10)
        filters.pack(fill="x", pady=(0, 10))

        ttk.Label(filters, text="Дата").grid(row=0, column=0, sticky="w")
        self.filter_date_var = tk.StringVar()
        ttk.Entry(filters, textvariable=self.filter_date_var, width=15).grid(row=0, column=1, padx=5)

        ttk.Label(filters, text="Статус").grid(row=0, column=2, sticky="w")
        self.filter_status_var = tk.StringVar(value="все")
        ttk.Combobox(
            filters, textvariable=self.filter_status_var, width=15, state="readonly",
            values=["все"] + list(STATUS_LABELS.keys()),
        ).grid(row=0, column=3, padx=5)

        ttk.Button(filters, text="Применить", command=self.refresh).grid(row=0, column=4, padx=5)
        ttk.Button(filters, text="Сбросить", command=self.reset_filters).grid(row=0, column=5, padx=5)

    def reset_filters(self):
        self.filter_date_var.set("")
        self.filter_status_var.set("все")
        self.refresh()

    def _build_table(self):
        columns = ("id", "user_name", "table_number", "booking_date", "start_time", "end_time", "guests_count", "status")
        headers = {
            "id": "ID", "user_name": "Гость", "table_number": "Стол", "booking_date": "Дата",
            "start_time": "Начало", "end_time": "Конец", "guests_count": "Гостей", "status": "Статус",
        }
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=10)
        for col in columns:
            self.tree.heading(col, text=headers[col])
            self.tree.column(col, width=90 if col != "user_name" else 150)
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def refresh(self):
        self._combo_maps()
        self.user_combo["values"] = list(self.user_by_label)
        self.table_combo["values"] = list(self.table_by_label)

        booking_date = None
        if self.filter_date_var.get().strip():
            try:
                booking_date = parse_date(self.filter_date_var.get())
            except ValueError:
                messagebox.showwarning("Проверка", "Дата фильтра должна быть в формате ГГГГ-ММ-ДД.")
                return
        status = None if self.filter_status_var.get() == "все" else self.filter_status_var.get()

        self.tree.delete(*self.tree.get_children())
        for booking in backend.get_all_bookings(booking_date=booking_date, status=status):
            self.tree.insert("", "end", values=(
                booking["id"], booking["user_name"], booking["table_number"], booking["booking_date"],
                str(booking["start_time"])[:5], str(booking["end_time"])[:5],
                booking["guests_count"], STATUS_LABELS.get(booking["status"], booking["status"]),
            ))

    def on_select(self, _event):
        selection = self.tree.selection()
        if not selection:
            return
        values = self.tree.item(selection[0], "values")
        self.selected_id = int(values[0])

    def _read_form(self):
        user_label = self.user_var.get()
        table_label = self.table_var.get()
        if user_label not in self.user_by_label or table_label not in self.table_by_label:
            raise ValueError("Выберите гостя и стол из списка.")
        user_id = self.user_by_label[user_label]
        table_id = self.table_by_label[table_label]
        booking_date = parse_date(self.date_var.get())
        start_time = parse_time(self.start_var.get())
        end_time = parse_time(self.end_var.get())
        guests_count = int(self.guests_var.get())
        return user_id, table_id, booking_date, start_time, end_time, guests_count, user_label, table_label

    def check_availability(self):
        try:
            _, table_id, booking_date, start_time, end_time, _, _, table_label = self._read_form()
        except ValueError as exc:
            messagebox.showwarning("Проверка", str(exc))
            return
        available, reason = backend.check_table_availability(table_id, booking_date, start_time, end_time)
        if available:
            messagebox.showinfo("Доступность", f"Стол {table_label} свободен на {booking_date} {start_time}–{end_time}.")
        else:
            messagebox.showwarning("Доступность", f"Стол занят: {reason}")

    def add_booking(self):
        try:
            user_id, table_id, booking_date, start_time, end_time, guests_count, user_label, table_label = self._read_form()
        except ValueError as exc:
            messagebox.showwarning("Проверка", str(exc))
            return
        try:
            new_id = backend.create_booking(user_id, table_id, booking_date, start_time, end_time, guests_count)
        except Exception as exc:
            messagebox.showerror("Не удалось создать бронь", str(exc))
            return
        messagebox.showinfo(
            "Бронь создана",
            f"№{new_id}\nГость: {user_label}\nСтол: {table_label}\n"
            f"Дата: {booking_date}\nВремя: {start_time}–{end_time}\nГостей: {guests_count}\nСтатус: подтверждена",
        )
        self.refresh()

    def cancel_booking(self):
        if self.selected_id is None:
            messagebox.showwarning("Проверка", "Сначала выберите бронь в таблице.")
            return
        reason = simpledialog.askstring("Причина отмены", "Укажите причину отмены (можно оставить пустым):")
        backend.cancel_booking(self.selected_id, reason or "")
        self.refresh()

    def complete_booking(self):
        if self.selected_id is None:
            messagebox.showwarning("Проверка", "Сначала выберите бронь в таблице.")
            return
        backend.mark_booking_completed(self.selected_id)
        self.refresh()

    def no_show_booking(self):
        if self.selected_id is None:
            messagebox.showwarning("Проверка", "Сначала выберите бронь в таблице.")
            return
        backend.mark_booking_no_show(self.selected_id)
        self.refresh()

    def delete_booking(self):
        if self.selected_id is None:
            messagebox.showwarning("Проверка", "Сначала выберите бронь в таблице.")
            return
        if not messagebox.askyesno("Подтверждение", "Удалить бронь безвозвратно?"):
            return
        backend.delete_booking(self.selected_id)
        self.selected_id = None
        self.refresh()


class AnalyticsTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=10)

        ttk.Button(self, text="Обновить", command=self.refresh).pack(anchor="w", pady=(0, 10))

        ttk.Label(self, text="Загрузка столов (число активных/завершённых броней)").pack(anchor="w")
        self.load_tree = ttk.Treeview(self, columns=("table_number", "capacity", "bookings_count"), show="headings", height=6)
        for col, title in [("table_number", "Стол"), ("capacity", "Вместимость"), ("bookings_count", "Броней")]:
            self.load_tree.heading(col, text=title)
        self.load_tree.pack(fill="x", pady=(0, 15))

        ttk.Label(self, text="Распределение броней по статусам").pack(anchor="w")
        self.status_tree = ttk.Treeview(self, columns=("status", "total", "percent"), show="headings", height=6)
        for col, title in [("status", "Статус"), ("total", "Кол-во"), ("percent", "% от всех")]:
            self.status_tree.heading(col, text=title)
        self.status_tree.pack(fill="x")

        self.refresh()

    def refresh(self):
        self.load_tree.delete(*self.load_tree.get_children())
        for row in backend.get_table_load_stats():
            self.load_tree.insert("", "end", values=(row["table_number"], row["capacity"], row["bookings_count"]))

        self.status_tree.delete(*self.status_tree.get_children())
        for row in backend.get_status_breakdown():
            label = STATUS_LABELS.get(row["status"], row["status"])
            self.status_tree.insert("", "end", values=(label, row["total"], f"{row['percent']}%"))


def main():
    backend.create_tables()

    root = tk.Tk()
    root.title("Мини-система бронирования столиков")
    root.geometry("900x600")

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)

    users_tab = UsersTab(notebook)
    tables_tab = TablesTab(notebook)
    bookings_tab = BookingsTab(notebook, users_tab, tables_tab)
    analytics_tab = AnalyticsTab(notebook)

    notebook.add(users_tab, text="Гости")
    notebook.add(tables_tab, text="Столы")
    notebook.add(bookings_tab, text="Брони")
    notebook.add(analytics_tab, text="Аналитика")

    def on_tab_changed(_event):
        current = notebook.select()
        widget = notebook.nametowidget(current)
        if isinstance(widget, (UsersTab, TablesTab, BookingsTab, AnalyticsTab)):
            widget.refresh()

    notebook.bind("<<NotebookTabChanged>>", on_tab_changed)

    root.mainloop()


if __name__ == "__main__":
    main()
