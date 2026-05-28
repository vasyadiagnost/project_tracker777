import calendar
from datetime import date, datetime

import customtkinter as ctk


class DatePickerDialog(ctk.CTkToplevel):
    def __init__(self, master, initial_date=None, on_select=None, title="Выбор даты"):
        super().__init__(master)
        self.on_select = on_select
        self.selected_date = initial_date or date.today()
        self.current_year = self.selected_date.year
        self.current_month = self.selected_date.month

        self.title(title)
        self.geometry("360x360")
        self.resizable(False, False)
        self.grab_set()

        self.header_label = None
        self.days_frame = None

        self._build_ui()
        self._render_calendar()

    def _build_ui(self):
        wrap = ctk.CTkFrame(self)
        wrap.pack(fill="both", expand=True, padx=10, pady=10)

        header = ctk.CTkFrame(wrap, fg_color="transparent")
        header.pack(fill="x", pady=(0, 8))

        ctk.CTkButton(header, text="◀", width=36, command=self._prev_month).pack(side="left")
        self.header_label = ctk.CTkLabel(header, text="", font=("Segoe UI", 15, "bold"))
        self.header_label.pack(side="left", expand=True)
        ctk.CTkButton(header, text="▶", width=36, command=self._next_month).pack(side="right")

        week = ctk.CTkFrame(wrap, fg_color="transparent")
        week.pack(fill="x", pady=(0, 8))
        for name in ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]:
            ctk.CTkLabel(week, text=name, width=42).pack(side="left", padx=2)

        self.days_frame = ctk.CTkFrame(wrap, fg_color="transparent")
        self.days_frame.pack(fill="both", expand=True)

        bottom = ctk.CTkFrame(wrap, fg_color="transparent")
        bottom.pack(fill="x", pady=(8, 0))
        ctk.CTkButton(bottom, text="Сегодня", command=self._pick_today).pack(side="left")
        ctk.CTkButton(bottom, text="Очистить", command=self._clear).pack(side="right", padx=(8, 0))
        ctk.CTkButton(bottom, text="Закрыть", command=self.destroy).pack(side="right")

    def _render_calendar(self):
        for child in self.days_frame.winfo_children():
            child.destroy()

        month_names = [
            "", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
            "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
        ]
        self.header_label.configure(text=f"{month_names[self.current_month]} {self.current_year}")

        cal = calendar.Calendar(firstweekday=0)
        weeks = cal.monthdayscalendar(self.current_year, self.current_month)

        for r, week in enumerate(weeks):
            for c, day in enumerate(week):
                if day == 0:
                    ctk.CTkLabel(self.days_frame, text="", width=42).grid(row=r, column=c, padx=2, pady=2)
                    continue
                btn = ctk.CTkButton(
                    self.days_frame,
                    text=str(day),
                    width=42,
                    height=32,
                    command=lambda d=day: self._select_day(d),
                )
                if (
                    self.selected_date
                    and self.selected_date.year == self.current_year
                    and self.selected_date.month == self.current_month
                    and self.selected_date.day == day
                ):
                    btn.configure(fg_color="#2F80ED")
                self.days_frame.grid_columnconfigure(c, weight=1)
                btn.grid(row=r, column=c, padx=2, pady=2)

    def _select_day(self, day: int):
        picked = date(self.current_year, self.current_month, day)
        if self.on_select:
            self.on_select(picked)
        self.destroy()

    def _prev_month(self):
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self._render_calendar()

    def _next_month(self):
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self._render_calendar()

    def _pick_today(self):
        if self.on_select:
            self.on_select(date.today())
        self.destroy()

    def _clear(self):
        if self.on_select:
            self.on_select(None)
        self.destroy()


def parse_date_safe(value: str):
    value = value.strip()
    if not value:
        return None
    return datetime.strptime(value, "%d.%m.%Y").date()
