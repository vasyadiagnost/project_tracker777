from tkinter import messagebox, ttk

import customtkinter as ctk

from services.settings_service import SettingsService
from services.task_service import TaskService
from ui.dialogs.task_dialog import TaskDialog


class TasksTab:
    def __init__(self, parent, session, app):
        self.parent = parent
        self.session = session
        self.app = app
        self.tree = None
        self.current_task_id: int | None = None

        self.search_entry = None
        self.project_combo = None
        self.stage_combo = None
        self.status_combo = None
        self.dri_combo = None
        default_active = SettingsService.get_bool(session, "default_active_only_tasks", True)
        self.show_active_only = ctk.BooleanVar(value=default_active)

        self._build_ui()

    def _build_ui(self):
        filters = ctk.CTkFrame(self.parent)
        filters.pack(fill="x", padx=10, pady=10)
        for i in range(8):
            filters.grid_columnconfigure(i, weight=0)
        filters.grid_columnconfigure(0, weight=1)

        self.search_entry = ctk.CTkEntry(filters, placeholder_text="Поиск по задаче / описанию / next step")
        self.search_entry.grid(row=1, column=0, padx=(8, 8), pady=8, sticky="ew")
        ctk.CTkLabel(filters, text="Поиск").grid(row=0, column=0, sticky="w", padx=(8, 8), pady=(8, 0))

        ctk.CTkLabel(filters, text="Название проекта").grid(row=0, column=1, sticky="w", padx=8, pady=(8, 0))
        self.project_combo = ctk.CTkComboBox(filters, values=[""], command=lambda _v: self._on_project_changed(), width=170)
        self.project_combo.grid(row=1, column=1, padx=8, pady=8)

        ctk.CTkLabel(filters, text="Этап проекта").grid(row=0, column=2, sticky="w", padx=8, pady=(8, 0))
        self.stage_combo = ctk.CTkComboBox(filters, values=[""], width=170)
        self.stage_combo.grid(row=1, column=2, padx=8, pady=8)

        ctk.CTkLabel(filters, text="Статус").grid(row=0, column=3, sticky="w", padx=8, pady=(8, 0))
        self.status_combo = ctk.CTkComboBox(filters, values=[""] + TaskService.TASK_STATUSES, width=140)
        self.status_combo.grid(row=1, column=3, padx=8, pady=8)

        ctk.CTkLabel(filters, text="DRI / ответственный").grid(row=0, column=4, sticky="w", padx=8, pady=(8, 0))
        self.dri_combo = ctk.CTkComboBox(filters, values=[""], width=170)
        self.dri_combo.grid(row=1, column=4, padx=8, pady=8)

        ctk.CTkCheckBox(filters, text="Только активные", variable=self.show_active_only).grid(row=1, column=5, padx=8, pady=8, sticky="w")
        ctk.CTkButton(filters, text="Применить", width=120, command=self.refresh).grid(row=1, column=6, padx=8, pady=8)
        ctk.CTkButton(filters, text="Сброс", width=110, command=self._reset_filters).grid(row=1, column=7, padx=8, pady=8)

        actions = ctk.CTkFrame(self.parent, fg_color="transparent")
        actions.pack(fill="x", padx=10, pady=(0, 6))
        left = ctk.CTkFrame(actions, fg_color="transparent")
        left.pack(side="left")
        ctk.CTkButton(left, text="Добавить", width=140, command=self._add_task).grid(row=0, column=0, padx=(0, 8))
        ctk.CTkButton(left, text="Редактировать", width=140, command=self._edit_selected).grid(row=0, column=1, padx=(0, 8))
        ctk.CTkButton(left, text="Быстро выполнить", width=160, command=self._quick_complete_selected).grid(row=0, column=2)
        ctk.CTkButton(actions, text="На главную", width=140, command=lambda: self.app.tabview.set("Главная")).pack(side="right")

        table_frame = ctk.CTkFrame(self.parent)
        table_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        columns = ("signal", "title", "project", "stage", "dri", "controller", "due", "control", "status", "next_step", "quality", "updated")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        headers = {
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
            "quality": "Качество",
            "updated": "Обновлено",
        }
        widths = {"signal": 170, "title": 220, "project": 130, "stage": 100, "dri": 120, "controller": 120, "due": 90, "control": 90, "status": 100, "next_step": 210, "quality": 220, "updated": 120}
        for col in columns:
            self.tree.heading(col, text=headers[col])
            self.tree.column(col, width=widths[col], anchor="w")
        self.tree.pack(fill="both", expand=True, padx=6, pady=6)
        self.tree.bind("<<TreeviewSelect>>", self._on_task_select)
        self.tree.bind("<Double-1>", lambda _e: self._edit_selected())

        self._configure_tree_tags()

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

    def _selected_from_tree(self) -> int | None:
        selection = self.tree.selection()
        if selection:
            return int(selection[0])
        focused = self.tree.focus()
        if focused:
            return int(focused)
        return self.current_task_id

    def _on_task_select(self, _event=None):
        self.current_task_id = self._selected_from_tree()

    def select_task(self, task_id: int):
        iid = str(task_id)
        if self.tree.exists(iid):
            self.tree.selection_set(iid)
            self.tree.focus(iid)
            self.tree.see(iid)
            self.current_task_id = task_id

    def edit_task_by_id(self, task_id: int):
        task = TaskService.get_task(self.session, task_id)
        if task:
            self.select_task(task_id)
            TaskDialog(self.app, self.session, self.app.refresh_all, task=task)

    def _on_project_changed(self):
        projects_map = TaskService.get_projects_map(self.session)
        project_title = self.project_combo.get().strip()
        project_id = None
        for pid, title in projects_map.items():
            if title == project_title:
                project_id = pid
                break
        stages_map = TaskService.get_stages_map(self.session, project_id)
        self.stage_combo.configure(values=[""] + list(stages_map.values()))
        self.stage_combo.set("")

    def _reset_filters(self):
        self.search_entry.delete(0, "end")
        self.project_combo.set("")
        self.stage_combo.configure(values=[""])
        self.stage_combo.set("")
        self.status_combo.set("")
        self.dri_combo.set("")
        self.show_active_only.set(SettingsService.get_bool(self.session, "default_active_only_tasks", True))
        self.refresh()

    def _add_task(self):
        TaskDialog(self.app, self.session, self.app.refresh_all)

    def _edit_selected(self):
        task_id = self._selected_from_tree()
        self.current_task_id = task_id
        if not task_id:
            return
        self.edit_task_by_id(task_id)

    def _quick_complete_selected(self):
        task_id = self._selected_from_tree()
        self.current_task_id = task_id
        if not task_id:
            return
        if not messagebox.askyesno("Подтверждение", "Отметить выбранную задачу выполненной?"):
            return
        try:
            TaskService.quick_complete(self.session, task_id, author="user")
        except Exception as exc:
            messagebox.showerror("Ошибка", str(exc))
            return
        self.app.refresh_all()

    def refresh(self):
        projects_map = TaskService.get_projects_map(self.session)
        self.project_combo.configure(values=[""] + list(projects_map.values()))

        responsibles = sorted({row["dri"] for row in TaskService.list_tasks(self.session, only_active=False) if row["dri"]})
        self.dri_combo.configure(values=[""] + responsibles)

        selected_project_id = None
        selected_project_title = self.project_combo.get().strip()
        for project_id, title in projects_map.items():
            if title == selected_project_title:
                selected_project_id = project_id
                break

        stages_map = TaskService.get_stages_map(self.session, selected_project_id)
        current_stage_value = self.stage_combo.get().strip()
        self.stage_combo.configure(values=[""] + list(stages_map.values()))
        if current_stage_value not in stages_map.values():
            self.stage_combo.set("")
        selected_stage_id = None
        selected_stage_title = self.stage_combo.get().strip()
        for stage_id, title in stages_map.items():
            if title == selected_stage_title:
                selected_stage_id = stage_id
                break

        rows = TaskService.list_tasks(
            self.session,
            search_text=self.search_entry.get(),
            project_id=selected_project_id,
            stage_id=selected_stage_id,
            status=self.status_combo.get().strip(),
            dri=self.dri_combo.get().strip(),
            only_active=self.show_active_only.get(),
        )

        selected_before = self.current_task_id
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.current_task_id = None

        for row in rows:
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
                    row["quality"],
                    row["updated_at"],
                ),
                tags=(self._pick_row_tag(row),),
            )

        if selected_before and self.tree.exists(str(selected_before)):
            self.select_task(selected_before)
