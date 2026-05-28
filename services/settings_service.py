from sqlalchemy import select
from sqlalchemy.orm import Session

from models.app_setting import AppSetting


class SettingsService:
    DEFAULTS: dict[str, str] = {
        "risk_days": "3",
        "dashboard_show_overdue": "1",
        "dashboard_show_today": "1",
        "dashboard_show_3days": "1",
        "dashboard_show_blockers": "1",
        "dashboard_show_waiting": "1",
        "dashboard_show_no_next_step": "1",
        "dashboard_show_on_review": "1",
        "dashboard_show_no_control": "1",
        "dashboard_show_all_active": "0",
        "dashboard_show_completed": "0",
        "summary_box_width": "480",
        "summary_limit_items": "5",
        "default_active_only_tasks": "1",
        "report_template_prefix": "СВОДКА",
    }

    @staticmethod
    def ensure_defaults(session: Session) -> None:
        existing = {
            row.key: row
            for row in session.execute(select(AppSetting)).scalars().all()
        }
        created = False
        for key, value in SettingsService.DEFAULTS.items():
            if key not in existing:
                session.add(AppSetting(key=key, value=value))
                created = True
        if created:
            session.commit()

    @staticmethod
    def get_all(session: Session) -> dict[str, str]:
        SettingsService.ensure_defaults(session)
        return {
            row.key: row.value
            for row in session.execute(select(AppSetting)).scalars().all()
        }

    @staticmethod
    def get(session: Session, key: str, default: str = "") -> str:
        SettingsService.ensure_defaults(session)
        row = session.execute(select(AppSetting).where(AppSetting.key == key)).scalar_one_or_none()
        if row is None:
            return default
        return row.value

    @staticmethod
    def get_int(session: Session, key: str, default: int = 0) -> int:
        value = SettingsService.get(session, key, str(default))
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def get_bool(session: Session, key: str, default: bool = False) -> bool:
        value = SettingsService.get(session, key, "1" if default else "0")
        return str(value).strip() in {"1", "true", "True", "yes", "YES"}

    @staticmethod
    def set(session: Session, key: str, value: str) -> None:
        SettingsService.ensure_defaults(session)
        row = session.execute(select(AppSetting).where(AppSetting.key == key)).scalar_one_or_none()
        if row is None:
            row = AppSetting(key=key, value=value)
            session.add(row)
        else:
            row.value = value
        session.commit()

    @staticmethod
    def set_many(session: Session, values: dict[str, str]) -> None:
        SettingsService.ensure_defaults(session)
        existing = {
            row.key: row
            for row in session.execute(select(AppSetting)).scalars().all()
        }
        for key, value in values.items():
            if key in existing:
                existing[key].value = value
            else:
                session.add(AppSetting(key=key, value=value))
        session.commit()
