from datetime import date
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.project import Project, Stage
from models.task import Task


class ProjectService:
    PROJECT_STATUSES = ["Инициирован", "В работе", "На паузе", "Завершён", "Отменён"]
    PROJECT_PRIORITIES = ["Низкий", "Средний", "Высокий", "Критичный"]

    DEFAULT_PROJECT_STAGES = [
        {
            "title": "Инициация проекта",
            "status": "Не начат",
            "notes": "Цель, ожидаемый результат, заказчик/стейкхолдеры, первичная оценка сроков и ресурсов.",
        },
        {
            "title": "Проработка / аналитика",
            "status": "Не начат",
            "notes": "Сбор исходных данных, анализ вариантов, риски, предварительная декомпозиция.",
        },
        {
            "title": "Планирование",
            "status": "Не начат",
            "notes": "Календарный план, ответственные, зависимости задач, контрольные точки.",
        },
        {
            "title": "Реализация",
            "status": "Не начат",
            "notes": "Выполнение задач, координация исполнителей, решение текущих проблем.",
        },
        {
            "title": "Контроль и управление",
            "status": "Не начат",
            "notes": "Мониторинг сроков, качества, рисков, перепланирование и коммуникация со стейкхолдерами.",
        },
        {
            "title": "Завершение",
            "status": "Не начат",
            "notes": "Приёмка результата, закрытие задач, фиксация итогов, передача результата.",
        },
        {
            "title": "Пост-анализ",
            "status": "Не начат",
            "notes": "Что сработало, что пошло не так, какие улучшения перенести в следующие проекты.",
        },
    ]

    @staticmethod
    def _get_project_metrics(session: Session, project_id: int) -> dict[str, int]:
        today = date.today()

        active_tasks = session.scalar(
            select(func.count(Task.id)).where(
                Task.project_id == project_id,
                Task.is_archived.is_(False),
                Task.status.not_in(["Выполнена", "Отменена"]),
            )
        ) or 0

        overdue_tasks = session.scalar(
            select(func.count(Task.id)).where(
                Task.project_id == project_id,
                Task.is_archived.is_(False),
                Task.status.not_in(["Выполнена", "Отменена"]),
                (
                    (Task.due_date.is_not(None) & (Task.due_date < today))
                    | (Task.control_date.is_not(None) & (Task.control_date < today))
                ),
            )
        ) or 0

        blockers = session.scalar(
            select(func.count(Task.id)).where(
                Task.project_id == project_id,
                Task.is_archived.is_(False),
                Task.status.not_in(["Выполнена", "Отменена"]),
                Task.blocker_note != "",
            )
        ) or 0

        on_review = session.scalar(
            select(func.count(Task.id)).where(
                Task.project_id == project_id,
                Task.is_archived.is_(False),
                Task.status == "На проверке",
            )
        ) or 0

        waiting_followup = session.scalar(
            select(func.count(Task.id)).where(
                Task.project_id == project_id,
                Task.is_archived.is_(False),
                Task.status == "Ожидаем ответ",
                Task.control_date.is_not(None),
                Task.control_date <= today,
            )
        ) or 0

        no_next_step = session.scalar(
            select(func.count(Task.id)).where(
                Task.project_id == project_id,
                Task.is_archived.is_(False),
                Task.status.not_in(["Выполнена", "Отменена"]),
                Task.next_step == "",
            )
        ) or 0

        return {
            "active_tasks": active_tasks,
            "overdue_tasks": overdue_tasks,
            "blockers": blockers,
            "on_review": on_review,
            "waiting_followup": waiting_followup,
            "no_next_step": no_next_step,
        }

    @staticmethod
    def _resolve_health(metrics: dict[str, int]) -> str:
        if metrics["overdue_tasks"] > 0:
            return "red"
        if metrics["blockers"] > 0:
            return "yellow"
        if metrics["active_tasks"] > 0:
            return "green"
        return "empty"

    @staticmethod
    def _resolve_next_action(metrics: dict[str, int]) -> str:
        if metrics["overdue_tasks"] > 0:
            return "Снять просрочку"
        if metrics["blockers"] > 0:
            return "Разобрать блокер"
        if metrics["on_review"] > 0:
            return "Проверить результат"
        if metrics["waiting_followup"] > 0:
            return "Сделать follow-up"
        if metrics["no_next_step"] > 0:
            return "Уточнить next step"
        if metrics["active_tasks"] > 0:
            return "Держать в работе"
        return "Нет активных задач"

    @staticmethod
    def list_projects(session: Session) -> list[dict[str, Any]]:
        projects = session.execute(select(Project).order_by(Project.updated_at.desc())).scalars().all()
        result: list[dict[str, Any]] = []

        for project in projects:
            metrics = ProjectService._get_project_metrics(session, project.id)
            delay_days = 0
            if project.target_date and project.original_target_date:
                delay_days = (project.target_date - project.original_target_date).days

            if delay_days <= 0:
                schedule_status = "on_track"
            elif delay_days <= 3:
                schedule_status = "warning"
            else:
                schedule_status = "delay"

            result.append(
                {
                    "id": project.id,
                    "health": ProjectService._resolve_health(metrics),
                    "next_action": ProjectService._resolve_next_action(metrics),
                    "title": project.title,
                    "dri": project.dri,
                    "target_date": project.target_date,
                    "original_target_date": project.original_target_date,
                    "delay_days": delay_days,
                    "schedule_status": schedule_status,
                    "status": project.status,
                    **metrics,
                }
            )
        return result

    @staticmethod
    def get_red_projects_today(session: Session, limit: int = 5) -> list[dict[str, Any]]:
        rows = [row for row in ProjectService.list_projects(session) if row["health"] == "red"]
        rows.sort(key=lambda r: (-r["overdue_tasks"], -r["blockers"], r["title"].lower()))
        return rows[:limit]

    @staticmethod
    def create_project(session: Session, data: dict[str, Any], create_default_stages: bool = False) -> Project:
        project = Project(**data)
        if project.original_target_date is None and project.target_date is not None:
            project.original_target_date = project.target_date
        session.add(project)
        session.flush()

        if create_default_stages:
            ProjectService.create_default_stages(session, project.id, commit=False)

        session.commit()
        session.refresh(project)
        return project

    @staticmethod
    def create_default_stages(session: Session, project_id: int, commit: bool = True) -> int:
        project = session.get(Project, project_id)
        if project is None:
            raise ValueError("Проект не найден.")

        existing_titles = {stage.title.strip().lower() for stage in project.stages}
        max_order = max((stage.sort_order for stage in project.stages), default=0)
        created_count = 0

        for index, item in enumerate(ProjectService.DEFAULT_PROJECT_STAGES, start=1):
            title = item["title"].strip()
            if title.lower() in existing_titles:
                continue

            session.add(
                Stage(
                    project_id=project_id,
                    title=title,
                    sort_order=max_order + index,
                    status=item.get("status", "Не начат"),
                    notes=item.get("notes", ""),
                )
            )
            created_count += 1

        if commit:
            session.commit()

        return created_count

    @staticmethod
    def update_project(session: Session, project_id: int, data: dict[str, Any]) -> Project:
        project = session.get(Project, project_id)
        if project is None:
            raise ValueError("Проект не найден.")
        for key, value in data.items():
            setattr(project, key, value)
        if project.original_target_date is None and project.target_date is not None:
            project.original_target_date = project.target_date
        session.commit()
        session.refresh(project)
        return project

    @staticmethod
    def delete_project(session: Session, project_id: int) -> None:
        project = session.get(Project, project_id)
        if project is None:
            raise ValueError("Проект не найден.")
        session.delete(project)
        session.commit()
