from tkinter import messagebox

import customtkinter as ctk

from services.settings_service import SettingsService


class SettingsTab:
    def __init__(self, parent, session, app):
        self.parent = parent
        self.session = session
        self.app = app

        self.risk_days_entry = None
        self.summary_width_entry = None
        self.summary_limit_entry = None
        self.default_active_var = ctk.BooleanVar(value=True)

        self.dashboard_vars: dict[str, ctk.BooleanVar] = {}

        self._build_ui()

    def _build_ui(self):
        container = ctk.CTkScrollableFrame(self.parent)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        general = self._create_card(container, "Основные настройки")
        general.pack(fill="x", padx=4, pady=(0, 12))

        general_grid = ctk.CTkFrame(general, fg_color="transparent")
        general_grid.pack(fill="x", padx=16, pady=(4, 14))
        general_grid.grid_columnconfigure(0, weight=1)

        self._add_field_title(general_grid, 0, "Горизонт зоны риска (дней)")
        self._add_field_hint(general_grid, 1, "Сколько дней считать ближайшей зоной внимания.")
        self.risk_days_entry = ctk.CTkEntry(general_grid)
        self.risk_days_entry.grid(row=2, column=0, sticky="ew", padx=6, pady=(0, 12))

        self._add_field_title(general_grid, 3, 'Ширина блока "Утренняя сводка", пикселей')
        self._add_field_hint(general_grid, 4, "Управляет шириной правого блока на главной вкладке.")
        self.summary_width_entry = ctk.CTkEntry(general_grid)
        self.summary_width_entry.grid(row=5, column=0, sticky="ew", padx=6, pady=(0, 12))

        self._add_field_title(general_grid, 6, "Сколько строк показывать в утренней сводке")
        self._add_field_hint(general_grid, 7, "Лимит строк в кратком обзоре на главной.")
        self.summary_limit_entry = ctk.CTkEntry(general_grid)
        self.summary_limit_entry.grid(row=8, column=0, sticky="ew", padx=6, pady=(0, 6))

        dashboard = self._create_card(container, "Главная вкладка")
        dashboard.pack(fill="x", padx=4, pady=(0, 12))

        ctk.CTkLabel(
            dashboard,
            text="Какие чекбоксы и режимы показывать на главной.",
            text_color=("gray30", "gray70"),
            anchor="w",
        ).pack(fill="x", padx=16, pady=(2, 8))

        checks_wrap = ctk.CTkFrame(dashboard, fg_color="transparent")
        checks_wrap.pack(fill="x", padx=16, pady=(0, 14))

        options = [
            ("dashboard_show_overdue", "Просрочено"),
            ("dashboard_show_today", "Сегодня"),
            ("dashboard_show_3days", "3 дня"),
            ("dashboard_show_blockers", "Блокеры"),
            ("dashboard_show_waiting", "Ожидаем ответ"),
            ("dashboard_show_no_next_step", "Без next step"),
            ("dashboard_show_on_review", "На проверке"),
            ("dashboard_show_no_control", "Без контроля"),
            ("dashboard_show_all_active", "Все активные"),
            ("dashboard_show_completed", "Завершённые"),
        ]

        for i, (key, label) in enumerate(options):
            var = ctk.BooleanVar(value=False)
            self.dashboard_vars[key] = var
            ctk.CTkCheckBox(
                checks_wrap,
                text=label,
                variable=var,
            ).grid(row=i // 2, column=i % 2, sticky="w", padx=8, pady=6)

        tasks = self._create_card(container, "Поведение задач")
        tasks.pack(fill="x", padx=4, pady=(0, 12))

        ctk.CTkLabel(
            tasks,
            text="Настройки, влияющие на поведение вкладки “Задачи”.",
            text_color=("gray30", "gray70"),
            anchor="w",
        ).pack(fill="x", padx=16, pady=(2, 8))

        tasks_body = ctk.CTkFrame(tasks, fg_color="transparent")
        tasks_body.pack(fill="x", padx=16, pady=(0, 14))

        ctk.CTkCheckBox(
            tasks_body,
            text="Во вкладке 'Задачи' по умолчанию показывать только активные",
            variable=self.default_active_var,
        ).pack(anchor="w", padx=6, pady=6)

        actions = ctk.CTkFrame(container, fg_color="transparent")
        actions.pack(fill="x", padx=4, pady=(6, 10))

        ctk.CTkButton(
            actions,
            text="На главную",
            command=lambda: self.app.tabview.set("Главная"),
            width=140,
        ).pack(side="left")

        ctk.CTkButton(
            actions,
            text="Сбросить к значениям по умолчанию",
            command=self._reset_defaults,
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            actions,
            text="Сохранить настройки",
            command=self._save,
        ).pack(side="right")

    def _create_card(self, parent, title: str) -> ctk.CTkFrame:
        card = ctk.CTkFrame(parent, corner_radius=14)
        ctk.CTkLabel(
            card,
            text=title,
            font=("Segoe UI", 17, "bold"),
            anchor="w",
        ).pack(fill="x", padx=16, pady=(14, 2))
        return card

    def _add_field_title(self, parent, row: int, text: str) -> None:
        ctk.CTkLabel(
            parent,
            text=text,
            anchor="w",
            font=("Segoe UI", 13, "bold"),
        ).grid(row=row, column=0, sticky="w", padx=6, pady=(4, 0))

    def _add_field_hint(self, parent, row: int, text: str) -> None:
        ctk.CTkLabel(
            parent,
            text=text,
            anchor="w",
            text_color=("gray35", "gray70"),
        ).grid(row=row, column=0, sticky="w", padx=6, pady=(0, 4))

    def _load(self):
        settings = SettingsService.get_all(self.session)

        self.risk_days_entry.delete(0, "end")
        self.risk_days_entry.insert(0, settings.get("risk_days", "3"))

        self.summary_width_entry.delete(0, "end")
        self.summary_width_entry.insert(0, settings.get("summary_box_width", "480"))

        self.summary_limit_entry.delete(0, "end")
        self.summary_limit_entry.insert(0, settings.get("summary_limit_items", "5"))

        self.default_active_var.set(settings.get("default_active_only_tasks", "1") == "1")

        for key, var in self.dashboard_vars.items():
            var.set(settings.get(key, "0") == "1")

    def _save(self):
        try:
            risk_days = int((self.risk_days_entry.get() or "3").strip())
            summary_width = int((self.summary_width_entry.get() or "480").strip())
            summary_limit = int((self.summary_limit_entry.get() or "5").strip())
        except ValueError:
            messagebox.showerror("Ошибка", "Числовые поля должны содержать числа.")
            return

        payload = {
            "risk_days": str(risk_days),
            "summary_box_width": str(summary_width),
            "summary_limit_items": str(summary_limit),
            "default_active_only_tasks": "1" if self.default_active_var.get() else "0",
        }
        for key, var in self.dashboard_vars.items():
            payload[key] = "1" if var.get() else "0"

        SettingsService.set_many(self.session, payload)
        messagebox.showinfo("Готово", "Настройки сохранены.")
        self.app.refresh_all()

    def _reset_defaults(self):
        SettingsService.set_many(self.session, SettingsService.DEFAULTS.copy())
        self._load()
        self.app.refresh_all()
        messagebox.showinfo("Готово", "Настройки сброшены к значениям по умолчанию.")

    def refresh(self):
        self._load()
