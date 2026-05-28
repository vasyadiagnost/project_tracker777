from datetime import date, datetime
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from models.project import Project, Stage
from models.task import Task, TaskHistory


class TaskService:
    TASK_STATUSES = ["Новая", "В работе", "Ожидаем ответ", "На проверке", "Выполнена", "Отменена"]

    @staticmethod
    def is_stuck(task: Task, stale_days: int = 5) -> bool:
        if task.status not in ["В работе", "Ожидаем ответ", "На проверке"]:
            return False
        if task.updated_at is None:
            return False
        return (datetime.now().date() - task.updated_at.date()).days >= stale_days

    @staticmethod
    def build_signal(task: Task) -> str:
        today = date.today()
        signals: list[str] = []

        effective_date = task.due_date or task.control_date
        if effective_date:
            if effective_date < today and task.status not in ["Выполнена", "Отменена"]:
                signals.append("ПРОСРОЧЕНО")
            elif effective_date == today and task.status not in ["Выполнена", "Отменена"]:
                signals.append("СЕГОДНЯ")
            elif effective_date <= date.fromordinal(today.toordinal() + 3) and task.status not in ["Выполнена", "Отменена"]:
                signals.append("3 ДНЯ")

        if task.blocker_note.strip() and task.status not in ["Выполнена", "Отменена"]:
            signals.append("БЛОКЕР")
        if not task.next_step.strip() and task.status not in ["Выполнена", "Отменена"]:
            signals.append("НЕТ NEXT STEP")
        if task.status == "Ожидаем ответ" and not task.control_date and task.status not in ["Выполнена", "Отменена"]:
            signals.append("НЕТ КОНТРОЛЯ")
        if TaskService.is_stuck(task) and task.status not in ["Выполнена", "Отменена"]:
            signals.append("ЗАВИСЛА")

        return " | ".join(signals)

    @staticmethod
    def get_quality_warnings(task: Task) -> list[str]:
        warnings: list[str] = []
        if not task.next_step.strip() and task.status not in ["Выполнена", "Отменена"]:
            warnings.append("Не указан следующий шаг")
        if not task.due_date and not task.control_date and task.status not in ["Выполнена", "Отменена"]:
            warnings.append("Нет срока и нет контрольной даты")
        if task.status == "Ожидаем ответ" and not task.control_date:
            warnings.append("Для статуса 'Ожидаем ответ' нужна контрольная дата")
        if task.status == "Ожидаем ответ" and not task.waiting_for.strip():
            warnings.append("Для статуса 'Ожидаем ответ' желательно указать, от кого ждём ответ")
        if not task.dri.strip():
            warnings.append("Не указан DRI")
        if getattr(task, "depends_on_enabled", False) and not getattr(task, "depends_on_task_id", None):
            warnings.append("Включена зависимость, но не выбрано мастер-действие")
        if TaskService.is_stuck(task) and task.status not in ["Выполнена", "Отменена"]:
            warnings.append("Задача давно не обновлялась — возможна потеря контроля")
        return warnings

    @staticmethod
    def _normalize_dependency(session: Session, task: Task) -> None:
        if not task.depends_on_enabled or not task.depends_on_task_id:
            return

        master = session.get(Task, task.depends_on_task_id)
        if master is None or master.id == task.id:
            task.depends_on_enabled = False
            task.depends_on_task_id = None
            return

        if task.planned_start_date is None:
            task.planned_start_date = date.today()

        if master.completed_at:
            master_done = master.completed_at.date()
            if master_done > task.planned_start_date:
                task.planned_start_date = master_done
        else:
            if task.planned_start_date < date.today():
                task.planned_start_date = date.today()

    @staticmethod
    def _refresh_dependents(session: Session, master_task_id: int) -> None:
        dependents = session.execute(
            select(Task).where(
                Task.depends_on_enabled.is_(True),
                Task.depends_on_task_id == master_task_id,
                Task.is_archived.is_(False),
            )
        ).scalars().all()

        for dependent in dependents:
            TaskService._normalize_dependency(session, dependent)

    @staticmethod
    def list_tasks(
        session: Session,
        search_text: str = "",
        project_id: int | None = None,
        stage_id: int | None = None,
        status: str = "",
        dri: str = "",
        only_active: bool = True,
    ) -> list[dict[str, Any]]:
        stmt = (
            select(Task)
            .options(joinedload(Task.project), joinedload(Task.stage))
            .where(Task.is_archived.is_(False))
            .order_by(Task.updated_at.desc())
        )

        if search_text.strip():
            pattern = f"%{search_text.strip()}%"
            stmt = stmt.where(
                or_(
                    Task.title.ilike(pattern),
                    Task.description.ilike(pattern),
                    Task.next_step.ilike(pattern),
                    Task.waiting_for.ilike(pattern),
                )
            )
        if project_id:
            stmt = stmt.where(Task.project_id == project_id)
        if stage_id:
            stmt = stmt.where(Task.stage_id == stage_id)
        if status:
            stmt = stmt.where(Task.status == status)
        if dri:
            stmt = stmt.where(Task.dri == dri)
        if only_active:
            stmt = stmt.where(Task.status.not_in(["Выполнена", "Отменена"]))

        tasks = session.execute(stmt).scalars().all()

        return [
            {
                "id": task.id,
                "signal": TaskService.build_signal(task),
                "title": task.title,
                "project": task.project.title if task.project else "",
                "stage": task.stage.title if task.stage else "",
                "dri": task.dri,
                "controller": task.controller,
                "planned_start_date": task.planned_start_date.strftime("%d.%m.%Y") if task.planned_start_date else "",
                "due_date": task.due_date.strftime("%d.%m.%Y") if task.due_date else "",
                "control_date": task.control_date.strftime("%d.%m.%Y") if task.control_date else "",
                "status": task.status,
                "next_step": task.next_step,
                "quality": " / ".join(TaskService.get_quality_warnings(task)),
                "updated_at": task.updated_at.strftime("%d.%m.%Y %H:%M") if task.updated_at else "",
            }
            for task in tasks
        ]

    @staticmethod
    def create_task(session: Session, data: dict[str, Any], author: str = "system") -> Task:
        task = Task(**data)
        if task.status == "Выполнена" and task.completed_at is None:
            task.completed_at = datetime.now()
        session.add(task)
        session.flush()

        TaskService._normalize_dependency(session, task)

        session.add(
            TaskHistory(
                task_id=task.id,
                event_type="create",
                old_value="",
                new_value=task.status,
                comment="Задача создана",
                author=author,
            )
        )
        session.commit()
        session.refresh(task)
        return task

    @staticmethod
    def update_task(session: Session, task_id: int, data: dict[str, Any], author: str = "system") -> Task:
        task = session.get(Task, task_id)
        if task is None:
            raise ValueError("Задача не найдена.")

        old_status = task.status
        old_due = task.due_date.strftime("%d.%m.%Y") if task.due_date else ""
        old_control = task.control_date.strftime("%d.%m.%Y") if task.control_date else ""
        old_next_step = task.next_step

        for key, value in data.items():
            setattr(task, key, value)

        if task.depends_on_task_id == task.id:
            raise ValueError("Задача не может зависеть сама от себя.")

        if task.status == "Выполнена" and task.completed_at is None:
            task.completed_at = datetime.now()
        elif task.status != "Выполнена":
            task.completed_at = None

        TaskService._normalize_dependency(session, task)

        if old_status != task.status:
            session.add(
                TaskHistory(
                    task_id=task.id,
                    event_type="status_change",
                    old_value=old_status,
                    new_value=task.status,
                    comment="Изменён статус",
                    author=author,
                )
            )

        new_due = task.due_date.strftime("%d.%m.%Y") if task.due_date else ""
        if old_due != new_due:
            session.add(
                TaskHistory(
                    task_id=task.id,
                    event_type="due_date_change",
                    old_value=old_due,
                    new_value=new_due,
                    comment="Изменён срок",
                    author=author,
                )
            )

        new_control = task.control_date.strftime("%d.%m.%Y") if task.control_date else ""
        if old_control != new_control:
            session.add(
                TaskHistory(
                    task_id=task.id,
                    event_type="control_date_change",
                    old_value=old_control,
                    new_value=new_control,
                    comment="Изменена контрольная дата",
                    author=author,
                )
            )

        if old_next_step != task.next_step:
            session.add(
                TaskHistory(
                    task_id=task.id,
                    event_type="next_step_change",
                    old_value=old_next_step,
                    new_value=task.next_step,
                    comment="Изменён следующий шаг",
                    author=author,
                )
            )

        session.commit()
        TaskService._refresh_dependents(session, task.id)
        session.commit()
        session.refresh(task)
        return task

    @staticmethod
    def quick_complete(session: Session, task_id: int, author: str = "user") -> Task:
        task = session.get(Task, task_id)
        if task is None:
            raise ValueError("Задача не найдена.")
        old_status = task.status
        task.status = "Выполнена"
        task.completed_at = datetime.now()
        session.add(
            TaskHistory(
                task_id=task.id,
                event_type="status_change",
                old_value=old_status,
                new_value="Выполнена",
                comment="Быстрое завершение задачи",
                author=author,
            )
        )
        session.commit()
        TaskService._refresh_dependents(session, task.id)
        session.commit()
        session.refresh(task)
        return task

    @staticmethod
    def delete_task(session: Session, task_id: int) -> None:
        task = session.get(Task, task_id)
        if task is None:
            raise ValueError("Задача не найдена.")
        session.delete(task)
        session.commit()

    @staticmethod
    def get_task(session: Session, task_id: int) -> Task | None:
        stmt = (
            select(Task)
            .options(
                joinedload(Task.project),
                joinedload(Task.stage),
                joinedload(Task.history),
                joinedload(Task.dependency_task),
            )
            .where(Task.id == task_id)
        )
        return session.execute(stmt).unique().scalar_one_or_none()

    @staticmethod
    def get_projects_map(session: Session) -> dict[int, str]:
        return {project.id: project.title for project in session.execute(select(Project).order_by(Project.title)).scalars().all()}

    @staticmethod
    def get_stages_map(session: Session, project_id: int | None = None) -> dict[int, str]:
        stmt = select(Stage)
        if project_id:
            stmt = stmt.where(Stage.project_id == project_id)
        stages = session.execute(stmt.order_by(Stage.sort_order, Stage.title)).scalars().all()
        return {stage.id: stage.title for stage in stages}

    @staticmethod
    def get_project_tasks_map(session: Session, project_id: int | None = None, exclude_task_id: int | None = None) -> dict[int, str]:
        stmt = select(Task).where(Task.is_archived.is_(False)).order_by(Task.id.desc())
        if project_id:
            stmt = stmt.where(Task.project_id == project_id)
        if exclude_task_id:
            stmt = stmt.where(Task.id != exclude_task_id)
        tasks = session.execute(stmt).scalars().all()
        return {task.id: f"{task.id} · {task.title}" for task in tasks}
