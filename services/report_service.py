from services.task_service import TaskService


class ReportService:
    @staticmethod
    def get_red_zone_rows(session):
        rows = TaskService.list_tasks(session, only_active=True)
        return [r for r in rows if "ПРОСРОЧЕНО" in r["signal"] or "БЛОКЕР" in r["signal"] or "НЕТ NEXT STEP" in r["signal"]]

    @staticmethod
    def get_three_days_rows(session):
        rows = TaskService.list_tasks(session, only_active=True)
        return [r for r in rows if "3 ДНЯ" in r["signal"]]

    @staticmethod
    def get_waiting_rows(session):
        rows = TaskService.list_tasks(session, only_active=True)
        return [r for r in rows if r["status"] == "Ожидаем ответ"]

    @staticmethod
    def get_project_rows(session, project_id: int):
        return TaskService.list_tasks(session, project_id=project_id, only_active=False)

    @staticmethod
    def get_dri_rows(session, dri: str):
        return TaskService.list_tasks(session, dri=dri, only_active=False)

    @staticmethod
    def rows_to_text(title: str, rows: list[dict]) -> str:
        lines = [title, ""]
        if not rows:
            lines.append("Данных нет.")
            return "\n".join(lines)

        for row in rows:
            lines.append(
                f"- [{row['signal']}] {row['title']} | {row['project']} | {row['stage']} | "
                f"DRI: {row['dri']} | Контроль: {row['control_date'] or row['due_date']} | "
                f"Статус: {row['status']} | Next: {row['next_step']}"
            )
        return "\n".join(lines)
