from copy import deepcopy
from tkinter import messagebox, ttk

import customtkinter as ctk

from models.project import Project
from models.task import Task
from ui.dialogs.project_dialog import ProjectDialog
from ui.dialogs.task_dialog import TaskDialog


class DatabaseEditorTab:
    def __init__(self, parent, session, app):
        self.parent = parent
        self.session = session
        self.app = app
        self.project_tree = None
        self.task_tree = None
        self._build_ui()

    def _build_ui(self):
        top = ctk.CTkFrame(self.parent, fg_color="transparent")
        top.pack(fill="x", padx=10, pady=10)
        ctk.CTkButton(top, text="Добавить проект", command=self._add_project).pack(side="left")
        ctk.CTkButton(top, text="Редактировать проект", command=self._edit_project).pack(side="left", padx=8)
        ctk.CTkButton(top, text="Дублировать проект", command=self._duplicate_project).pack(side="left", padx=8)
        ctk.CTkButton(top, text="Удалить проект", command=self._delete_project).pack(side="left", padx=8)

        ctk.CTkButton(top, text="Добавить задачу", command=self._add_task).pack(side="left", padx=(24, 8))
        ctk.CTkButton(top, text="Редактировать задачу", command=self._edit_task).pack(side="left", padx=8)
        ctk.CTkButton(top, text="Дублировать задачу", command=self._duplicate_task).pack(side="left", padx=8)
        ctk.CTkButton(top, text="Удалить задачу", command=self._delete_task).pack(side="left", padx=8)
        ctk.CTkButton(top, text="На главную", command=lambda: self.app.tabview.set("Главная")).pack(side="right")

        paned = ctk.CTkFrame(self.parent)
        paned.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        left = ctk.CTkFrame(paned)
        left.pack(side="left", fill="both", expand=True, padx=(0, 5))
        right = ctk.CTkFrame(paned)
        right.pack(side="left", fill="both", expand=True, padx=(5, 0))

        ctk.CTkLabel(left, text="Projects", font=("Segoe UI", 15, "bold")).pack(anchor="w", padx=8, pady=8)
        self.project_tree = ttk.Treeview(left, columns=("id", "title", "status"), show="headings")
        for col, title, width in [("id", "ID", 60), ("title", "Название", 320), ("status", "Статус", 140)]:
            self.project_tree.heading(col, text=title)
            self.project_tree.column(col, width=width)
        self.project_tree.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.project_tree.bind("<Double-1>", lambda _e: self._edit_project())

        ctk.CTkLabel(right, text="Tasks", font=("Segoe UI", 15, "bold")).pack(anchor="w", padx=8, pady=8)
        self.task_tree = ttk.Treeview(right, columns=("id", "title", "status", "dri"), show="headings")
        for col, title, width in [("id", "ID", 60), ("title", "Задача", 320), ("status", "Статус", 120), ("dri", "DRI", 160)]:
            self.task_tree.heading(col, text=title)
            self.task_tree.column(col, width=width)
        self.task_tree.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.task_tree.bind("<Double-1>", lambda _e: self._edit_task())

    def _selected_project_id(self):
        selection = self.project_tree.selection()
        if not selection:
            return None
        return int(selection[0])

    def _selected_task_id(self):
        selection = self.task_tree.selection()
        if not selection:
            return None
        return int(selection[0])

    def _add_project(self):
        ProjectDialog(self.app, self.session, self.app.refresh_all)

    def _edit_project(self):
        project_id = self._selected_project_id()
        if not project_id:
            return
        project = self.session.get(Project, project_id)
        if project:
            ProjectDialog(self.app, self.session, self.app.refresh_all, project=project)

    def _duplicate_project(self):
        project_id = self._selected_project_id()
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
            status=project.status,
            priority=project.priority,
            notes=project.notes,
        )
        self.session.add(clone)
        self.session.commit()
        self.app.refresh_all()

    def _delete_project(self):
        project_id = self._selected_project_id()
        if not project_id:
            return
        project = self.session.get(Project, project_id)
        if not project:
            return
        if not messagebox.askyesno("Подтверждение", f"Удалить проект '{project.title}'?"):
            return
        self.session.delete(project)
        self.session.commit()
        self.app.refresh_all()

    def _add_task(self):
        TaskDialog(self.app, self.session, self.app.refresh_all)

    def _edit_task(self):
        task_id = self._selected_task_id()
        if not task_id:
            return
        task = self.session.get(Task, task_id)
        if task:
            TaskDialog(self.app, self.session, self.app.refresh_all, task=task)

    def _duplicate_task(self):
        task_id = self._selected_task_id()
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
            due_date=task.due_date,
            control_date=task.control_date,
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
        task_id = self._selected_task_id()
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

    def refresh(self):
        for item in self.project_tree.get_children():
            self.project_tree.delete(item)
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)

        for project in self.session.query(Project).order_by(Project.id.desc()).all():
            self.project_tree.insert("", "end", iid=str(project.id), values=(project.id, project.title, project.status))

        for task in self.session.query(Task).order_by(Task.id.desc()).limit(500).all():
            self.task_tree.insert("", "end", iid=str(task.id), values=(task.id, task.title, task.status, task.dri))
