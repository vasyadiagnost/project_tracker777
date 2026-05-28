from datetime import date, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.task import Task
from services.project_service import ProjectService
from services.settings_service import SettingsService
from services.task_service import TaskService


class DashboardService:
    @staticmethod
    def get_counters(session: Session) -> dict[str, int]:
        today = date.today()
        risk_days = SettingsService.get_int(session, "risk_days", 3)
        horizon = date.fromordinal(today.toordinal() + risk_days)
        stale_days = 5
        stale_border = datetime.now().date().toordinal() - stale_days

        overdue = session.scalar(
            select(func.count(Task.id)).where(
                Task.is_archived.is_(False),
                Task.status.not_in(["Выполнена", "Отменена"]),
                (Task.due_date.is_not(None) & (Task.due_date < today))
                | (Task.control_date.is_not(None) & (Task.control_date < today)),
            )
        ) or 0

        today_count = session.scalar(
            select(func.count(Task.id)).where(
                Task.is_archived.is_(False),
                Task.status.not_in(["Выполнена", "Отменена"]),
                (Task.due_date == today) | (Task.control_date == today),
            )
        ) or 0

        horizon_count = session.scalar(
            select(func.count(Task.id)).where(
                Task.is_archived.is_(False),
                Task.status.not_in(["Выполнена", "Отменена"]),
                (
                    (Task.due_date.is_not(None) & (Task.due_date > today) & (Task.due_date <= horizon))
                    | (Task.control_date.is_not(None) & (Task.control_date > today) & (Task.control_date <= horizon))
                ),
            )
        ) or 0

        blockers = session.scalar(
            select(func.count(Task.id)).where(
                Task.is_archived.is_(False),
                Task.status.not_in(["Выполнена", "Отменена"]),
                Task.blocker_note != "",
            )
        ) or 0

        waiting = session.scalar(
            select(func.count(Task.id)).where(
                Task.is_archived.is_(False),
                Task.status == "Ожидаем ответ",
            )
        ) or 0

        no_next_step = session.scalar(
            select(func.count(Task.id)).where(
                Task.is_archived.is_(False),
                Task.status.not_in(["Выполнена", "Отменена"]),
                Task.next_step == "",
            )
        ) or 0

        on_review = session.scalar(
            select(func.count(Task.id)).where(
                Task.is_archived.is_(False),
                Task.status == "На проверке",
            )
        ) or 0

        no_control = session.scalar(
            select(func.count(Task.id)).where(
                Task.is_archived.is_(False),
                Task.status == "Ожидаем ответ",
                Task.control_date.is_(None),
            )
        ) or 0

        stuck = session.scalar(
            select(func.count(Task.id)).where(
                Task.is_archived.is_(False),
                Task.status.in_(["В работе", "Ожидаем ответ", "На проверке"]),
                func.julianday(func.current_timestamp()) - func.julianday(Task.updated_at) >= stale_days,
            )
        ) or 0

        red_projects = len(ProjectService.get_red_projects_today(session, limit=9999))

        return {
            "Просрочено": overdue,
            "Сегодня": today_count,
            "3 дня": horizon_count,
            "Блокеры": blockers,
            "Ожидаем ответ": waiting,
            "Без next step": no_next_step,
            "На проверке": on_review,
            "Без контроля": no_control,
            "Зависли": stuck,
            "Красные проекты": red_projects,
        }

    @staticmethod
    def build_morning_summary(session: Session) -> str:
        tasks = TaskService.list_tasks(session, only_active=False)
        summary_limit = SettingsService.get_int(session, "summary_limit_items", 5)

        critical = [t for t in tasks if "ПРОСРОЧЕНО" in t["signal"] or "БЛОКЕР" in t["signal"]]
        today = [t for t in tasks if "СЕГОДНЯ" in t["signal"]]
        review = [t for t in tasks if t["status"] == "На проверке"]
        weak = [t for t in tasks if "НЕТ NEXT STEP" in t["signal"] or "НЕТ КОНТРОЛЯ" in t["signal"]]
        stuck = [t for t in tasks if "ЗАВИСЛА" in t["signal"]]
        red_projects = ProjectService.get_red_projects_today(session, limit=summary_limit)

        lines = [
            "УТРЕННЯЯ СВОДКА",
            "",
            f"Критичные задачи: {len(critical)}",
            f"Сегодня: {len(today)}",
            f"На проверке: {len(review)}",
            f"Слабое ведение: {len(weak)}",
            f"Зависли: {len(stuck)}",
            f"Красные проекты: {len(red_projects)}",
            "",
        ]

        def append_block(title: str, rows: list[dict], limit: int = 5):
            lines.append(title)
            if not rows:
                lines.append("- нет")
            else:
                for row in rows[:limit]:
                    lines.append(
                        f"- [{row['signal'] or row['status']}] {row['title']} | "
                        f"{row['project']} | {row['dri']} | "
                        f"{row['control_date'] or row['due_date'] or row['updated_at']}"
                    )
            lines.append("")

        append_block("КРАСНАЯ ЗОНА ПО ЗАДАЧАМ", critical, summary_limit)
        append_block("СЕГОДНЯ", today, summary_limit)
        append_block("НА ПРОВЕРКЕ", review, summary_limit)
        append_block("СЛАБЫЕ МЕСТА", weak, summary_limit)
        append_block("ЗАВИСШИЕ ЗАДАЧИ", stuck, summary_limit)

        lines.append("КРАСНЫЕ ПРОЕКТЫ СЕГОДНЯ")
        if not red_projects:
            lines.append("- нет")
        else:
            for row in red_projects:
                lines.append(
                    f"- {row['title']} | просрочек: {row['overdue_tasks']} | "
                    f"блокеров: {row['blockers']} | действие: {row['next_action']}"
                )

        return "\n".join(lines).strip()
