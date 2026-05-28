from datetime import datetime

import customtkinter as ctk
from tkinter import messagebox, ttk

from services.reference_service import ReferenceService
from services.task_service import TaskService
from ui.dialogs.date_picker_dialog import DatePickerDialog, parse_date_safe


class TaskDialog(ctk.CTkToplevel):
    def __init__(self, master, session, on_saved, task=None, preset_project_id: int | None = None):
        super().__init__(master)
        self.session = session
        self.on_saved = on_saved
        self.task = task
        self.preset_project_id = preset_project_id

        self.title("Задача")
        self.geometry("1060x980")
        self.minsize(940, 780)
        self.grab_set()

        self.projects_map = TaskService.get_projects_map(self.session)
        self.project_titles = [""] + list(self.projects_map.values())
        self.responsibles = ReferenceService.get_responsibles(self.session)
        self.priorities = ReferenceService.get_priorities(self.session)
        self.stage_map = {}
        self.dep_map = {}

        self._build_ui()
        self._bind_date_buttons()
        self._fill_if_edit()
        self._refresh_history()

    def _build_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.form = ctk.CTkScrollableFrame(self)
        self.form.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        self.form.grid_columnconfigure(1, weight=1)

        row = 0

        self._add_label("Название", row)
        self.title_entry = ctk.CTkEntry(self.form)
        self.title_entry.grid(row=row, column=1, sticky="ew", padx=12, pady=6)
        row += 1

        self._add_label("Проект", row)
        self.project_combo = ctk.CTkComboBox(self.form, values=self.project_titles, command=lambda _v: self._on_project_changed())
        self.project_combo.grid(row=row, column=1, sticky="ew", padx=12, pady=6)
        row += 1

        self._add_label("Этап", row)
        self.stage_combo = ctk.CTkComboBox(self.form, values=[""])
        self.stage_combo.grid(row=row, column=1, sticky="ew", padx=12, pady=6)
        row += 1

        self._add_label("Инициатор", row)
        self.initiator_entry = ctk.CTkEntry(self.form)
        self.initiator_entry.grid(row=row, column=1, sticky="ew", padx=12, pady=6)
        row += 1

        self._add_label("DRI", row)
        self.dri_combo = ctk.CTkComboBox(self.form, values=self.responsibles or [""])
        self.dri_combo.grid(row=row, column=1, sticky="ew", padx=12, pady=6)
        row += 1

        self._add_label("Соисполнители", row)
        self.co_entry = ctk.CTkEntry(self.form)
        self.co_entry.grid(row=row, column=1, sticky="ew", padx=12, pady=6)
        row += 1

        self._add_label("Контролёр", row)
        self.controller_combo = ctk.CTkComboBox(self.form, values=self.responsibles or [""])
        self.controller_combo.grid(row=row, column=1, sticky="ew", padx=12, pady=6)
        row += 1

        self._add_label("Статус", row)
        self.status_combo = ctk.CTkComboBox(self.form, values=TaskService.TASK_STATUSES)
        self.status_combo.grid(row=row, column=1, sticky="ew", padx=12, pady=6)
        self.status_combo.set("Новая")
        row += 1

        self._add_label("Приоритет", row)
        self.priority_combo = ctk.CTkComboBox(self.form, values=self.priorities or ["Средний"])
        self.priority_combo.grid(row=row, column=1, sticky="ew", padx=12, pady=6)
        self.priority_combo.set("Средний")
        row += 1

        self._add_label("Плановая дата начала (дд.мм.гггг)", row)
        self.start_entry, self.start_button = self._create_date_row(row)
        row += 1

        self._add_label("Срок (дд.мм.гггг)", row)
        self.due_entry, self.due_button = self._create_date_row(row)
        row += 1

        self._add_label("Контрольная дата (дд.мм.гггг)", row)
        self.control_entry, self.control_button = self._create_date_row(row)
        row += 1

        self._add_label("Начало действия зависит от выполнения другого действия", row)
        dep_wrap = ctk.CTkFrame(self.form, fg_color="transparent")
        dep_wrap.grid(row=row, column=1, sticky="ew", padx=12, pady=6)
        self.dep_enabled_var = ctk.BooleanVar(value=False)
        self.dep_enabled_checkbox = ctk.CTkCheckBox(dep_wrap, text="", variable=self.dep_enabled_var, command=self._toggle_dependency_ui)
        self.dep_enabled_checkbox.pack(side="left")
        row += 1

        self._add_label("Мастер-действие по выбранному проекту", row)
        self.dep_task_combo = ctk.CTkComboBox(self.form, values=[""])
        self.dep_task_combo.grid(row=row, column=1, sticky="ew", padx=12, pady=6)
        row += 1

        self._add_label("Описание", row)
        self.description_text = ctk.CTkTextbox(self.form, height=90)
        self.description_text.grid(row=row, column=1, sticky="nsew", padx=12, pady=6)
        row += 1

        self._add_label("Ожидаемый результат", row)
        self.expected_text = ctk.CTkTextbox(self.form, height=70)
        self.expected_text.grid(row=row, column=1, sticky="nsew", padx=12, pady=6)
        row += 1

        self._add_label("Следующий шаг", row)
        self.next_step_text = ctk.CTkTextbox(self.form, height=70)
        self.next_step_text.grid(row=row, column=1, sticky="nsew", padx=12, pady=6)
        row += 1

        self._add_label("Ждём от кого", row)
        self.waiting_entry = ctk.CTkEntry(self.form)
        self.waiting_entry.grid(row=row, column=1, sticky="ew", padx=12, pady=6)
        row += 1

        self._add_label("Блокер / примечание", row)
        self.blocker_text = ctk.CTkTextbox(self.form, height=70)
        self.blocker_text.grid(row=row, column=1, sticky="nsew", padx=12, pady=6)
        row += 1

        ctk.CTkLabel(self.form, text="Предупреждения качества задачи", anchor="w").grid(row=row, column=0, sticky="nw", padx=12, pady=6)
        self.quality_box = ctk.CTkTextbox(self.form, height=85)
        self.quality_box.grid(row=row, column=1, sticky="nsew", padx=12, pady=6)
        self.quality_box.configure(state="disabled")
        row += 1

        ctk.CTkLabel(self.form, text="История изменений", anchor="w").grid(row=row, column=0, sticky="nw", padx=12, pady=6)
        history_frame = ctk.CTkFrame(self.form)
        history_frame.grid(row=row, column=1, sticky="nsew", padx=12, pady=6)
        columns = ("dt", "event", "old", "new", "comment", "author")
        self.history_tree = ttk.Treeview(history_frame, columns=columns, show="headings", height=8)
        headers = {
            "dt": "Когда",
            "event": "Событие",
            "old": "Старое",
            "new": "Новое",
            "comment": "Комментарий",
            "author": "Автор",
        }
        widths = {"dt": 130, "event": 130, "old": 120, "new": 120, "comment": 220, "author": 110}
        for col in columns:
            self.history_tree.heading(col, text=headers[col])
            self.history_tree.column(col, width=widths[col], anchor="w")
        self.history_tree.pack(fill="both", expand=True, padx=6, pady=6)
        row += 1

        button_frame = ctk.CTkFrame(self.form, fg_color="transparent")
        button_frame.grid(row=row, column=0, columnspan=2, sticky="e", padx=12, pady=12)
        if self.task:
            ctk.CTkButton(button_frame, text="Отметить выполненной", width=180, command=self._quick_complete).pack(side="right", padx=(8, 0))
        ctk.CTkButton(button_frame, text="Проверить качество", width=180, command=self._preview_quality).pack(side="right", padx=(8, 0))
        ctk.CTkButton(button_frame, text="Сохранить", width=140, command=self._save).pack(side="right", padx=(8, 0))
        ctk.CTkButton(button_frame, text="Отмена", width=140, command=self.destroy).pack(side="right")

    def _create_date_row(self, row: int):
        frame = ctk.CTkFrame(self.form, fg_color="transparent")
        frame.grid(row=row, column=1, sticky="ew", padx=12, pady=6)
        frame.grid_columnconfigure(0, weight=1)

        entry = ctk.CTkEntry(frame)
        entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        button = ctk.CTkButton(frame, text="📅", width=46)
        button.grid(row=0, column=1)
        return entry, button

    def _bind_date_buttons(self):
        def _make(entry_widget):
            def _open():
                try:
                    initial = parse_date_safe(entry_widget.get())
                except Exception:
                    initial = None

                def _set(picked):
                    entry_widget.delete(0, "end")
                    if picked:
                        entry_widget.insert(0, picked.strftime("%d.%m.%Y"))

                DatePickerDialog(self, initial_date=initial, on_select=_set)
            return _open

        self.start_button.configure(command=_make(self.start_entry))
        self.due_button.configure(command=_make(self.due_entry))
        self.control_button.configure(command=_make(self.control_entry))

    def _add_label(self, text: str, row: int) -> None:
        ctk.CTkLabel(self.form, text=text, anchor="w", wraplength=250).grid(row=row, column=0, sticky="w", padx=12, pady=6)

    def _resolve_project_id(self) -> int | None:
        selected = self.project_combo.get().strip()
        for project_id, title in self.projects_map.items():
            if title == selected:
                return project_id
        return None

    def _resolve_stage_id(self) -> int | None:
        selected = self.stage_combo.get().strip()
        for stage_id, title in self.stage_map.items():
            if title == selected:
                return stage_id
        return None

    def _resolve_dep_task_id(self) -> int | None:
        selected = self.dep_task_combo.get().strip()
        for task_id, title in self.dep_map.items():
            if title == selected:
                return task_id
        return None

    def _toggle_dependency_ui(self):
        state = "normal" if self.dep_enabled_var.get() else "disabled"
        self.dep_task_combo.configure(state=state)

    def _refresh_dependency_tasks(self):
        project_id = self._resolve_project_id()
        self.dep_map = TaskService.get_project_tasks_map(self.session, project_id, self.task.id if self.task else None)
        current = self.dep_task_combo.get().strip()
        self.dep_task_combo.configure(values=[""] + list(self.dep_map.values()))
        if current not in self.dep_map.values():
            self.dep_task_combo.set("")
        self._toggle_dependency_ui()

    def _on_project_changed(self):
        project_id = self._resolve_project_id()
        self.stage_map = TaskService.get_stages_map(self.session, project_id)
        self.stage_combo.configure(values=[""] + list(self.stage_map.values()))
        if not self.task:
            self.stage_combo.set("")
        self._refresh_dependency_tasks()

    def _fill_if_edit(self):
        if self.task and self.task.project:
            self.project_combo.set(self.task.project.title)
            self._on_project_changed()
        elif self.preset_project_id and self.preset_project_id in self.projects_map:
            self.project_combo.set(self.projects_map[self.preset_project_id])
            self._on_project_changed()
        else:
            self._refresh_dependency_tasks()

        if not self.task:
            return

        self.title_entry.insert(0, self.task.title)
        if self.task.stage:
            self.stage_combo.set(self.task.stage.title)
        self.initiator_entry.insert(0, self.task.initiator)
        self.dri_combo.set(self.task.dri)
        self.co_entry.insert(0, self.task.co_executors)
        self.controller_combo.set(self.task.controller)
        self.status_combo.set(self.task.status)
        self.priority_combo.set(self.task.priority)
        if self.task.planned_start_date:
            self.start_entry.insert(0, self.task.planned_start_date.strftime("%d.%m.%Y"))
        if self.task.due_date:
            self.due_entry.insert(0, self.task.due_date.strftime("%d.%m.%Y"))
        if self.task.control_date:
            self.control_entry.insert(0, self.task.control_date.strftime("%d.%m.%Y"))
        self.dep_enabled_var.set(self.task.depends_on_enabled)
        self._toggle_dependency_ui()
        if self.task.dependency_task:
            dep_label = self.dep_map.get(self.task.dependency_task.id)
            if dep_label:
                self.dep_task_combo.set(dep_label)
        self.description_text.insert("1.0", self.task.description)
        self.expected_text.insert("1.0", self.task.expected_result)
        self.next_step_text.insert("1.0", self.task.next_step)
        self.waiting_entry.insert(0, self.task.waiting_for)
        self.blocker_text.insert("1.0", self.task.blocker_note)
        self._preview_quality()

    @staticmethod
    def _parse_date(value: str):
        value = value.strip()
        if not value:
            return None
        try:
            return datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("Дата должна быть в формате дд.мм.гггг")

    def _build_preview_task(self):
        class PreviewTask:
            pass
        t = PreviewTask()
        t.next_step = self.next_step_text.get("1.0", "end").strip()
        t.due_date = self._parse_date(self.due_entry.get()) if self.due_entry.get().strip() else None
        t.control_date = self._parse_date(self.control_entry.get()) if self.control_entry.get().strip() else None
        t.status = self.status_combo.get().strip()
        t.waiting_for = self.waiting_entry.get().strip()
        t.dri = self.dri_combo.get().strip()
        t.depends_on_enabled = self.dep_enabled_var.get()
        t.depends_on_task_id = self._resolve_dep_task_id()
        return t

    def _preview_quality(self):
        try:
            task = self._build_preview_task()
            warnings = TaskService.get_quality_warnings(task)
        except Exception as exc:
            warnings = [str(exc)]

        self.quality_box.configure(state="normal")
        self.quality_box.delete("1.0", "end")
        if warnings:
            self.quality_box.insert("1.0", "\n".join(f"• {w}" for w in warnings))
        else:
            self.quality_box.insert("1.0", "Критичных замечаний нет.")
        self.quality_box.configure(state="disabled")

    def _refresh_history(self):
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        if not self.task:
            return
        for event in self.task.history:
            self.history_tree.insert(
                "",
                "end",
                values=(
                    event.created_at.strftime("%d.%m.%Y %H:%M"),
                    event.event_type,
                    event.old_value,
                    event.new_value,
                    event.comment,
                    event.author,
                ),
            )

    def _quick_complete(self):
        if not self.task:
            return
        TaskService.quick_complete(self.session, self.task.id, author="user")
        self.on_saved()
        self.destroy()

    def _save(self):
        title = self.title_entry.get().strip()
        project_id = self._resolve_project_id()
        dri = self.dri_combo.get().strip()

        if not title:
            messagebox.showerror("Ошибка", "Укажите название задачи.")
            return
        if not project_id:
            messagebox.showerror("Ошибка", "Укажите проект.")
            return
        if not dri:
            messagebox.showerror("Ошибка", "Укажите DRI.")
            return

        depends_on_enabled = self.dep_enabled_var.get()
        depends_on_task_id = self._resolve_dep_task_id() if depends_on_enabled else None

        try:
            data = {
                "project_id": project_id,
                "stage_id": self._resolve_stage_id(),
                "title": title,
                "description": self.description_text.get("1.0", "end").strip(),
                "initiator": self.initiator_entry.get().strip(),
                "dri": dri,
                "co_executors": self.co_entry.get().strip(),
                "controller": self.controller_combo.get().strip(),
                "status": self.status_combo.get().strip(),
                "priority": self.priority_combo.get().strip(),
                "planned_start_date": self._parse_date(self.start_entry.get()),
                "due_date": self._parse_date(self.due_entry.get()),
                "control_date": self._parse_date(self.control_entry.get()),
                "depends_on_enabled": depends_on_enabled,
                "depends_on_task_id": depends_on_task_id,
                "next_step": self.next_step_text.get("1.0", "end").strip(),
                "expected_result": self.expected_text.get("1.0", "end").strip(),
                "waiting_for": self.waiting_entry.get().strip(),
                "blocker_note": self.blocker_text.get("1.0", "end").strip(),
            }
            if self.task:
                TaskService.update_task(self.session, self.task.id, data, author="user")
            else:
                TaskService.create_task(self.session, data, author="user")
        except Exception as exc:
            messagebox.showerror("Ошибка", str(exc))
            return

        self.on_saved()
        self.destroy()
