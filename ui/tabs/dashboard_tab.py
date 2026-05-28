import tkinter as tk
from tkinter import ttk

import customtkinter as ctk

from services.dashboard_service import DashboardService
from services.project_service import ProjectService
from services.settings_service import SettingsService
from services.task_service import TaskService
from ui.dialogs.task_dialog import TaskDialog


class DashboardTab:
    FILTER_META = [
        ("dashboard_show_overdue", "Просрочено", True),
        ("dashboard_show_today", "Сегодня", True),
        ("dashboard_show_3days", "3 дня", True),
        ("dashboard_show_blockers", "Блокеры", True),
        ("dashboard_show_waiting", "Ожидаем ответ", True),
        ("dashboard_show_no_next_step", "Без next step", True),
        ("dashboard_show_on_review", "На проверке", True),
        ("dashboard_show_no_control", "Без контроля", True),
        ("dashboard_show_stuck", "Зависли", True),
        ("dashboard_show_all_active", "Все активные", False),
        ("dashboard_show_completed", "Завершённые", False),
    ]

    def __init__(self, parent, session, app):
        self.parent = parent
        self.session = session
        self.app = app

        self.counter_labels: dict[str, ctk.CTkLabel] = {}
        self.counter_frames: dict[str, ctk.CTkFrame] = {}
        self.filter_vars: dict[str, tk.BooleanVar] = {}
        self.filter_checkboxes: dict[str, ctk.CTkCheckBox] = {}
        self.tree = None
        self.summary_box = None
        self.red_projects_tree = None
        self.right_panel = None
        self._filters_initialized = False

        self._build_ui()

    def _build_ui(self):
        top = ctk.CTkFrame(self.parent)
        top.pack(fill="x", padx=10, pady=(10, 6))

        for title in ["Просрочено", "Сегодня", "3 дня", "Блокеры", "Ожидаем ответ", "Без next step", "На проверке", "Без контроля", "Зависли"]:
            card = ctk.CTkFrame(top, corner_radius=12)
            card.pack(side="left", fill="x", expand=True, padx=4, pady=4)
            ctk.CTkLabel(card, text=title).pack(pady=(10, 2))
            label = ctk.CTkLabel(card, text="0", font=("Segoe UI", 18, "bold"))
            label.pack(pady=(0, 10))
            self.counter_frames[title] = card
            self.counter_labels[title] = label

        filters = ctk.CTkFrame(self.parent)
        filters.pack(fill="x", padx=10, pady=6)

        for _key, title, default in self.FILTER_META:
            var = tk.BooleanVar(value=default)
            self.filter_vars[title] = var
            checkbox = ctk.CTkCheckBox(filters, text=title, variable=var, command=self.refresh)
            checkbox.pack(side="left", padx=8, pady=8)
            self.filter_checkboxes[title] = checkbox

        actions = ctk.CTkFrame(self.parent, fg_color="transparent")
        actions.pack(fill="x", padx=10, pady=(0, 6))
        ctk.CTkButton(actions, text="Обновить", width=140, command=self.refresh).pack(side="right")
        ctk.CTkButton(actions, text="Новый проект", width=140, command=lambda: self.app.tabview.set("Проекты")).pack(side="right", padx=(0, 8))
        ctk.CTkButton(actions, text="Новая задача", width=140, command=self._add_task).pack(side="right", padx=(0, 8))

        body = ctk.CTkFrame(self.parent)
        body.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        body.grid_columnconfigure(0, weight=3)
        body.grid_columnconfigure(1, weight=2)
        body.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(body)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        self.right_panel = ctk.CTkFrame(body)
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        self.right_panel.grid_rowconfigure(1, weight=1)
        self.right_panel.grid_rowconfigure(3, weight=1)
        self.right_panel.grid_columnconfigure(0, weight=1)

        columns = ("signal", "title", "project", "stage", "dri", "controller", "due", "control", "status", "next_step")
        self.tree = ttk.Treeview(left, columns=columns, show="headings")
        headings = {
            "signal": "Сигнал",
            "title": "Задача",
            "project": "Проект",
            "stage": "Этап",
            "dri": "DRI",
            "controller": "Контролёр",
            "due": "Срок",
            "control": "Контроль",
            "status": "Статус",
            "next_step": "Следующий шаг",
        }
        widths = {"signal": 165, "title": 210, "project": 120, "stage": 90, "dri": 110, "controller": 110, "due": 80, "control": 80, "status": 95, "next_step": 160}
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="w")
        self.tree.pack(fill="both", expand=True, padx=6, pady=6)
        self.tree.bind("<Double-1>", self._edit_task)

        self._configure_tree_tags()

        ctk.CTkLabel(self.right_panel, text="Утренняя сводка", font=("Segoe UI", 15, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 4))
        self.summary_box = ctk.CTkTextbox(self.right_panel, width=480, height=220)
        self.summary_box.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.summary_box.configure(state="disabled")

        ctk.CTkLabel(self.right_panel, text="Красные проекты сегодня", font=("Segoe UI", 15, "bold")).grid(row=2, column=0, sticky="w", padx=10, pady=(4, 4))
        rp_frame = ctk.CTkFrame(self.right_panel)
        rp_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=(0, 10))
        rp_cols = ("health", "project", "reason", "action")
        self.red_projects_tree = ttk.Treeview(rp_frame, columns=rp_cols, show="headings", height=7)
        rp_headers = {"health": "●", "project": "Проект", "reason": "Причина", "action": "Действие"}
        rp_widths = {"health": 36, "project": 150, "reason": 105, "action": 145}
        for col in rp_cols:
            self.red_projects_tree.heading(col, text=rp_headers[col])
            self.red_projects_tree.column(col, width=rp_widths[col], anchor="w")
        self.red_projects_tree.pack(fill="both", expand=True, padx=6, pady=6)
        self.red_projects_tree.bind("<Double-1>", self._open_red_project)

    def _configure_tree_tags(self):
        self.tree.tag_configure("overdue", background="#FDE7E9")
        self.tree.tag_configure("today", background="#FFF4DB")
        self.tree.tag_configure("soon", background="#FFFBE8")
        self.tree.tag_configure("blocker", background="#FBE4FF")
        self.tree.tag_configure("waiting", background="#E8F1FF")
        self.tree.tag_configure("review", background="#E8FFF2")
        self.tree.tag_configure("weak", background="#F3F3F3")
        self.tree.tag_configure("done", background="#EAF7EA")
        self.tree.tag_configure("stuck", background="#FFEBD9")

    def _counter_color(self, title: str, value: int) -> str:
        if title == "Просрочено" and value > 0:
            return "#F6D9DD"
        if title in {"Сегодня", "3 дня"} and value > 0:
            return "#FCEBC8"
        if title == "Блокеры" and value > 0:
            return "#F2D8FF"
        if title in {"Ожидаем ответ", "Без контроля"} and value > 0:
            return "#DDEBFF"
        if title in {"Без next step", "На проверке"} and value > 0:
            return "#E6F2E6"
        if title == "Зависли" and value > 0:
            return "#FFE5CC"
        return "transparent"

    def _apply_settings(self):
        summary_width = SettingsService.get_int(self.session, "summary_box_width", 480)
        try:
            self.summary_box.configure(width=max(320, summary_width))
        except Exception:
            pass

        for key, title, default in self.FILTER_META:
            show_checkbox = SettingsService.get_bool(self.session, key, default)
            checkbox = self.filter_checkboxes[title]

            if show_checkbox:
                checkbox.pack_configure(side="left", padx=8, pady=8)
            else:
                checkbox.pack_forget()

            # Инициализируем состояние фильтров только один раз.
            # Иначе при каждом refresh чекбокс моментально "откатывается"
            # обратно к значению из настроек и выглядит как сломанный.
            if not self._filters_initialized:
                self.filter_vars[title].set(show_checkbox)

        self._filters_initialized = True

    def _add_task(self):
        TaskDialog(self.app, self.session, self.app.refresh_all)

    def _edit_task(self, _event=None):
        selection = self.tree.selection()
        if not selection:
            return
        task_id = int(selection[0])
        self.app.open_task(task_id)

    def _open_red_project(self, _event=None):
        selection = self.red_projects_tree.selection()
        if not selection:
            return
        project_id = int(selection[0])
        self.app.open_project(project_id)

    def _set_summary(self, text: str):
        self.summary_box.configure(state="normal")
        self.summary_box.delete("1.0", "end")
        self.summary_box.insert("1.0", text)
        self.summary_box.configure(state="disabled")

    def _pick_row_tag(self, row: dict) -> str:
        signal = row["signal"]
        status = row["status"]
        quality = row["quality"]

        if status == "Выполнена":
            return "done"
        if "ПРОСРОЧЕНО" in signal:
            return "overdue"
        if "БЛОКЕР" in signal:
            return "blocker"
        if status == "На проверке":
            return "review"
        if status == "Ожидаем ответ":
            return "waiting"
        if "СЕГОДНЯ" in signal:
            return "today"
        if "3 ДНЯ" in signal:
            return "soon"
        if "ЗАВИСЛА" in signal:
            return "stuck"
        if quality:
            return "weak"
        return ""

    def _health_icon(self, health: str) -> str:
        return {"red": "🔴", "yellow": "🟡", "green": "🟢", "empty": "⚪"}.get(health, "⚪")

    def _project_reason(self, row: dict) -> str:
        if row["overdue_tasks"] > 0:
            return f"Просрочек: {row['overdue_tasks']}"
        if row["blockers"] > 0:
            return f"Блокеров: {row['blockers']}"
        return "Риск"

    def refresh(self):
        self._apply_settings()

        counters = DashboardService.get_counters(self.session)
        for title, label in self.counter_labels.items():
            value = int(counters.get(title, 0))
            label.configure(text=str(value))
            self.counter_frames[title].configure(fg_color=self._counter_color(title, value))

        self._set_summary(DashboardService.build_morning_summary(self.session))

        for item in self.tree.get_children():
            self.tree.delete(item)
        for item in self.red_projects_tree.get_children():
            self.red_projects_tree.delete(item)

        red_projects = ProjectService.get_red_projects_today(self.session, limit=5)
        for row in red_projects:
            self.red_projects_tree.insert(
                "",
                "end",
                iid=str(row["id"]),
                values=(
                    self._health_icon(row["health"]),
                    row["title"],
                    self._project_reason(row),
                    row["next_action"],
                ),
            )

        show_all_active = self.filter_vars["Все активные"].get()
        show_completed = self.filter_vars["Завершённые"].get()
        tasks = TaskService.list_tasks(self.session, only_active=not show_completed)

        for row in tasks:
            signal = row["signal"]
            include = False

            if show_all_active and row["status"] not in ["Выполнена", "Отменена"]:
                include = True
            if show_completed and row["status"] == "Выполнена":
                include = True

            checks = {
                "Просрочено": "ПРОСРОЧЕНО" in signal,
                "Сегодня": "СЕГОДНЯ" in signal,
                "3 дня": "3 ДНЯ" in signal,
                "Блокеры": "БЛОКЕР" in signal,
                "Ожидаем ответ": row["status"] == "Ожидаем ответ",
                "Без next step": "НЕТ NEXT STEP" in signal,
                "На проверке": row["status"] == "На проверке",
                "Без контроля": "НЕТ КОНТРОЛЯ" in signal,
                "Зависли": "ЗАВИСЛА" in signal,
            }
            for title, state in checks.items():
                if self.filter_vars[title].get() and state:
                    include = True
                    break
            if not include:
                continue

            self.tree.insert(
                "",
                "end",
                iid=str(row["id"]),
                values=(
                    row["signal"],
                    row["title"],
                    row["project"],
                    row["stage"],
                    row["dri"],
                    row["controller"],
                    row["due_date"],
                    row["control_date"],
                    row["status"],
                    row["next_step"],
                ),
                tags=(self._pick_row_tag(row),),
            )
