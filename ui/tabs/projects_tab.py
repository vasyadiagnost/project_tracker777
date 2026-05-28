from tkinter import messagebox, ttk

import customtkinter as ctk

from models.project import Project, Stage
from models.task import Task
from services.project_service import ProjectService
from services.task_service import TaskService
from ui.dialogs.project_dialog import ProjectDialog
from ui.dialogs.stage_dialog import StageDialog
from ui.dialogs.task_dialog import TaskDialog


class ProjectsTab:
    def __init__(self, parent, session, app):
        self.parent = parent
        self.session = session
        self.app = app

        self.tree = None
        self.stage_tree = None
        self.task_tree = None

        self.current_project_id: int | None = None
        self.current_stage_id: int | None = None
        self.current_task_id: int | None = None

        self._build_ui()

    def _build_ui(self):
        top = ctk.CTkFrame(self.parent, fg_color="transparent")
        top.pack(fill="x", padx=10, pady=10)

        left_actions = ctk.CTkFrame(top, fg_color="transparent")
        left_actions.pack(side="left", fill="x", expand=True)

        for idx, (text, cmd, width) in enumerate([
            ("Добавить проект", self._add_project, 150),
            ("Редактировать проект", self._edit_selected_project, 170),
            ("Дублировать проект", self._duplicate_project, 160),
            ("Удалить проект", self._delete_selected_project, 145),
            ("Типовые этапы", self._add_default_stages_to_project, 145),
        ]):
            ctk.CTkButton(left_actions, text=text, width=width, command=cmd).grid(
                row=0, column=idx, padx=(0, 8), pady=4
            )

        ctk.CTkButton(
            top,
            text="На главную",
            width=140,
            command=lambda: self.app.tabview.set("Главная"),
        ).pack(side="right")

        body = ctk.CTkFrame(self.parent)
        body.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        body.grid_rowconfigure(0, weight=3)
        body.grid_rowconfigure(1, weight=2)
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)

        projects_wrap = ctk.CTkFrame(body)
        projects_wrap.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=4, pady=(0, 6))

        ctk.CTkLabel(projects_wrap, text="Проекты", font=("Segoe UI", 15, "bold")).pack(
            anchor="w", padx=10, pady=(10, 4)
        )

        columns = (
            "health",
            "title",
            "next_action",
            "dri",
            "target",
            "original_target",
            "delay",
            "status",
            "active",
            "overdue",
            "blockers",
        )
        self.tree = ttk.Treeview(projects_wrap, columns=columns, show="headings", height=10)

        headings = {
            "health": "●",
            "title": "Проект",
            "next_action": "Следующее действие",
            "dri": "DRI",
            "target": "Срок",
            "original_target": "Базовый срок",
            "delay": "Сдвиг",
            "status": "Статус",
            "active": "Активные",
            "overdue": "Просрочено",
            "blockers": "Блокеры",
        }
        widths = {
            "health": 42,
            "title": 210,
            "next_action": 180,
            "dri": 120,
            "target": 96,
            "original_target": 105,
            "delay": 80,
            "status": 115,
            "active": 85,
            "overdue": 90,
            "blockers": 80,
        }

        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="w")

        self.tree.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.tree.bind("<<TreeviewSelect>>", self._on_project_select)
        self.tree.bind("<Double-1>", lambda _e: self._edit_selected_project())

        stages_wrap = ctk.CTkFrame(body)
        stages_wrap.grid(row=1, column=0, sticky="nsew", padx=(4, 4), pady=(0, 0))

        stages_actions = ctk.CTkFrame(stages_wrap, fg_color="transparent")
        stages_actions.pack(fill="x", padx=8, pady=(8, 4))
        ctk.CTkLabel(
            stages_actions,
            text="Этапы выбранного проекта",
            font=("Segoe UI", 15, "bold"),
        ).pack(side="left")

        actions_right = ctk.CTkFrame(stages_actions, fg_color="transparent")
        actions_right.pack(side="right")
        ctk.CTkButton(actions_right, text="Удалить этап", width=126, command=self._delete_stage).pack(
            side="left", padx=(0, 6)
        )
        ctk.CTkButton(actions_right, text="Редактировать этап", width=145, command=self._edit_stage).pack(
            side="left", padx=(0, 6)
        )
        ctk.CTkButton(actions_right, text="Добавить этап", width=126, command=self._add_stage).pack(
            side="left"
        )

        stage_cols = ("title", "dri", "target", "status", "order")
        self.stage_tree = ttk.Treeview(stages_wrap, columns=stage_cols, show="headings", height=9)

        stage_headers = {
            "title": "Этап",
            "dri": "DRI",
            "target": "Срок",
            "status": "Статус",
            "order": "Порядок",
        }
        stage_widths = {"title": 240, "dri": 140, "target": 100, "status": 110, "order": 80}

        for col in stage_cols:
            self.stage_tree.heading(col, text=stage_headers[col])
            self.stage_tree.column(col, width=stage_widths[col], anchor="w")

        self.stage_tree.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.stage_tree.bind("<<TreeviewSelect>>", self._on_stage_select)
        self.stage_tree.bind("<Double-1>", lambda _e: self._edit_stage())

        tasks_wrap = ctk.CTkFrame(body)
        tasks_wrap.grid(row=1, column=1, sticky="nsew", padx=(4, 4), pady=(0, 0))

        tasks_actions = ctk.CTkFrame(tasks_wrap, fg_color="transparent")
        tasks_actions.pack(fill="x", padx=8, pady=(8, 4))
        ctk.CTkLabel(
            tasks_actions,
            text="Задачи выбранного проекта",
            font=("Segoe UI", 15, "bold"),
        ).pack(side="left")

        task_btns = ctk.CTkFrame(tasks_actions, fg_color="transparent")
        task_btns.pack(side="right")
        ctk.CTkButton(task_btns, text="Удалить задачу", width=120, command=self._delete_task).pack(
            side="left", padx=(0, 6)
        )
        ctk.CTkButton(task_btns, text="Дублировать задачу", width=145, command=self._duplicate_task).pack(
            side="left", padx=(0, 6)
        )
        ctk.CTkButton(task_btns, text="Редактировать задачу", width=155, command=self._edit_task).pack(
            side="left", padx=(0, 6)
        )
        ctk.CTkButton(task_btns, text="Добавить задачу", width=126, command=self._add_task).pack(
            side="left"
        )

        task_cols = ("title", "stage", "status", "dri", "due")
        self.task_tree = ttk.Treeview(tasks_wrap, columns=task_cols, show="headings", height=9)

        task_headers = {
            "title": "Задача",
            "stage": "Этап",
            "status": "Статус",
            "dri": "DRI",
            "due": "Срок/контроль",
        }
        task_widths = {"title": 260, "stage": 120, "status": 110, "dri": 130, "due": 110}

        for col in task_cols:
            self.task_tree.heading(col, text=task_headers[col])
            self.task_tree.column(col, width=task_widths[col], anchor="w")

        self.task_tree.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.task_tree.bind("<<TreeviewSelect>>", self._on_task_select)
        self.task_tree.bind("<Double-1>", lambda _e: self._edit_task())

    def _health_icon(self, health: str) -> str:
        return {"red": "🔴", "yellow": "🟡", "green": "🟢", "empty": "⚪"}.get(health, "⚪")

    def _delay_badge(self, delay_days: int, schedule_status: str) -> str:
        if delay_days <= 0:
            return "🟢 0"
        if schedule_status == "warning":
            return f"🟡 +{delay_days}"
        return f"🔴 +{delay_days}"

    def _selected_from_tree(self, tree, fallback_id: int | None = None) -> int | None:
        selection = tree.selection()
        if selection:
            return int(selection[0])
        focused = tree.focus()
        if focused:
            return int(focused)
        return fallback_id

    def _on_project_select(self, _event=None):
        self.current_project_id = self._selected_from_tree(self.tree)
        self.current_stage_id = None
        self.current_task_id = None
        self._refresh_details()

    def _on_stage_select(self, _event=None):
        self.current_stage_id = self._selected_from_tree(self.stage_tree)
        self.current_task_id = None
        self._refresh_task_list()

    def _on_task_select(self, _event=None):
        self.current_task_id = self._selected_from_tree(self.task_tree)

    def select_project(self, project_id: int) -> None:
        iid = str(project_id)
        if self.tree.exists(iid):
            self.tree.selection_set(iid)
            self.tree.focus(iid)
            self.tree.see(iid)
            self.current_project_id = project_id
            self.current_stage_id = None
            self.current_task_id = None
            self._refresh_details()

    def edit_project(self, project_id: int | None = None):
        if project_id:
            self.select_project(project_id)
        self._edit_selected_project()

    def edit_task_by_id(self, task_id: int):
        iid = str(task_id)
        if self.task_tree.exists(iid):
            self.task_tree.selection_set(iid)
            self.task_tree.focus(iid)
            self.task_tree.see(iid)
            self.current_task_id = task_id
        task = TaskService.get_task(self.session, task_id)
        if task:
            TaskDialog(self.app, self.session, self.app.refresh_all, task=task)

    def _add_project(self):
        ProjectDialog(self.app, self.session, self.app.refresh_all)

    def _edit_selected_project(self):
        project_id = self._selected_from_tree(self.tree, self.current_project_id)
        self.current_project_id = project_id
        if not project_id:
            return
        project = self.session.get(Project, project_id)
        if project:
            ProjectDialog(self.app, self.session, self.app.refresh_all, project=project)

    def _duplicate_project(self):
        project_id = self._selected_from_tree(self.tree, self.current_project_id)
        self.current_project_id = project_id
        if not project_id:
            return
        project = self.session.get(Project, project_id)
        if not project:
            return

        clone = Project(
            title=f"{project.title} (копия)",
            description=project.description,
            initiator=project.initiator,
            dri=project.dri,
            start_date=project.start_date,
            target_date=project.target_date,
            original_target_date=project.original_target_date or project.target_date,
            status=project.status,
            priority=project.priority,
            notes=project.notes,
        )
        self.session.add(clone)
        self.session.commit()
        self.app.refresh_all()

    def _delete_selected_project(self):
        project_id = self._selected_from_tree(self.tree, self.current_project_id)
        self.current_project_id = project_id
        if not project_id:
            return

        project = self.session.get(Project, project_id)
        if not project:
            return

        if not messagebox.askyesno("Подтверждение", f"Удалить проект '{project.title}'?"):
            return

        try:
            self.session.delete(project)
            self.session.commit()
        except Exception as exc:
            self.session.rollback()
            messagebox.showerror("Ошибка", f"Не удалось удалить проект.\n\n{exc}")
            return

        self.current_project_id = None
        self.current_stage_id = None
        self.current_task_id = None
        self.app.refresh_all()

    def _add_default_stages_to_project(self):
        project_id = self._selected_from_tree(self.tree, self.current_project_id)
        self.current_project_id = project_id
        if not project_id:
            messagebox.showerror("Ошибка", "Сначала выбери проект.")
            return

        try:
            created_count = ProjectService.create_default_stages(self.session, project_id)
        except Exception as exc:
            self.session.rollback()
            messagebox.showerror("Ошибка", f"Не удалось добавить типовые этапы.\n\n{exc}")
            return

        if created_count == 0:
            messagebox.showinfo("Типовые этапы", "Типовые этапы уже добавлены в этот проект.")
        else:
            messagebox.showinfo("Типовые этапы", f"Добавлено этапов: {created_count}.")

        self.app.refresh_all()
        self.select_project(project_id)

    def _add_stage(self):
        project_id = self.current_project_id
        if not project_id:
            messagebox.showerror("Ошибка", "Сначала выбери проект.")
            return
        StageDialog(self.app, self.session, self.app.refresh_all, project_id=project_id)

    def _edit_stage(self):
        stage_id = self._selected_from_tree(self.stage_tree, self.current_stage_id)
        self.current_stage_id = stage_id
        if not stage_id:
            return
        stage = self.session.get(Stage, stage_id)
        if stage:
            StageDialog(self.app, self.session, self.app.refresh_all, project_id=stage.project_id, stage=stage)

    def _delete_stage(self):
        stage_id = self._selected_from_tree(self.stage_tree, self.current_stage_id)
        self.current_stage_id = stage_id
        if not stage_id:
            return
        stage = self.session.get(Stage, stage_id)
        if not stage:
            return
        if not messagebox.askyesno("Подтверждение", f"Удалить этап '{stage.title}'?"):
            return
        self.session.delete(stage)
        self.session.commit()
        self.app.refresh_all()

    def _add_task(self):
        project_id = self.current_project_id
        if not project_id:
            messagebox.showerror("Ошибка", "Сначала выбери проект.")
            return
        TaskDialog(self.app, self.session, self.app.refresh_all, preset_project_id=project_id)

    def _edit_task(self):
        task_id = self._selected_from_tree(self.task_tree, self.current_task_id)
        self.current_task_id = task_id
        if not task_id:
            return
        self.edit_task_by_id(task_id)

    def _duplicate_task(self):
        task_id = self._selected_from_tree(self.task_tree, self.current_task_id)
        self.current_task_id = task_id
        if not task_id:
            return
        task = self.session.get(Task, task_id)
        if not task:
            return

        clone = Task(
            project_id=task.project_id,
            stage_id=task.stage_id,
            title=f"{task.title} (копия)",
            description=task.description,
            initiator=task.initiator,
            dri=task.dri,
            co_executors=task.co_executors,
            controller=task.controller,
            status=task.status,
            priority=task.priority,
            planned_start_date=task.planned_start_date,
            due_date=task.due_date,
            control_date=task.control_date,
            depends_on_enabled=task.depends_on_enabled,
            depends_on_task_id=task.depends_on_task_id,
            next_step=task.next_step,
            expected_result=task.expected_result,
            waiting_for=task.waiting_for,
            blocker_note=task.blocker_note,
            is_archived=task.is_archived,
        )
        self.session.add(clone)
        self.session.commit()
        self.app.refresh_all()

    def _delete_task(self):
        task_id = self._selected_from_tree(self.task_tree, self.current_task_id)
        self.current_task_id = task_id
        if not task_id:
            return
        task = self.session.get(Task, task_id)
        if not task:
            return
        if not messagebox.askyesno("Подтверждение", f"Удалить задачу '{task.title}'?"):
            return
        self.session.delete(task)
        self.session.commit()
        self.app.refresh_all()

    def _refresh_task_list(self):
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)
        self.current_task_id = None

        project_id = self.current_project_id
        if not project_id:
            return

        query = self.session.query(Task).filter(Task.project_id == project_id)

        if self.current_stage_id:
            query = query.filter(Task.stage_id == self.current_stage_id)

        tasks = query.order_by(Task.id.desc()).all()

        for task in tasks:
            due = ""
            if task.due_date:
                due = task.due_date.strftime("%d.%m.%Y")
            elif task.control_date:
                due = task.control_date.strftime("%d.%m.%Y")

            self.task_tree.insert(
                "",
                "end",
                iid=str(task.id),
                values=(
                    task.title,
                    task.stage.title if task.stage else "",
                    task.status,
                    task.dri,
                    due,
                ),
            )

    def _refresh_details(self):
        for item in self.stage_tree.get_children():
            self.stage_tree.delete(item)

        self.current_stage_id = None
        self.current_task_id = None

        project_id = self.current_project_id
        if not project_id:
            self._refresh_task_list()
            return

        project = self.session.get(Project, project_id)
        if not project:
            self._refresh_task_list()
            return

        stages = sorted(project.stages, key=lambda x: (x.sort_order, x.title.lower()))
        for stage in stages:
            target = stage.target_date.strftime("%d.%m.%Y") if stage.target_date else ""
            self.stage_tree.insert(
                "",
                "end",
                iid=str(stage.id),
                values=(stage.title, stage.dri, target, stage.status, stage.sort_order),
            )

        self._refresh_task_list()

    def refresh(self):
        selected_before = self.current_project_id

        for item in self.tree.get_children():
            self.tree.delete(item)

        rows = ProjectService.list_projects(self.session)
        for row in rows:
            target = row["target_date"].strftime("%d.%m.%Y") if row["target_date"] else ""
            original_target = row["original_target_date"].strftime("%d.%m.%Y") if row["original_target_date"] else ""

            self.tree.insert(
                "",
                "end",
                iid=str(row["id"]),
                values=(
                    self._health_icon(row["health"]),
                    row["title"],
                    row["next_action"],
                    row["dri"],
                    target,
                    original_target,
                    self._delay_badge(row["delay_days"], row["schedule_status"]),
                    row["status"],
                    row["active_tasks"],
                    row["overdue_tasks"],
                    row["blockers"],
                ),
            )

        if selected_before and self.tree.exists(str(selected_before)):
            self.select_project(selected_before)
        else:
            self.current_project_id = None
            self.current_stage_id = None
            self.current_task_id = None
            self._refresh_details()
