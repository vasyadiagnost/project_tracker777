from sqlalchemy import select
from sqlalchemy.orm import Session

from models.reference import Priority, Responsible


class ReferenceService:
    DEFAULT_PRIORITIES = ["Низкий", "Средний", "Высокий", "Критичный"]

    @staticmethod
    def ensure_defaults(session: Session) -> None:
        existing_priorities = set(session.execute(select(Priority.title)).scalars().all())
        created = False
        for index, title in enumerate(ReferenceService.DEFAULT_PRIORITIES, start=1):
            if title not in existing_priorities:
                session.add(Priority(title=title, sort_order=index))
                created = True
        if created:
            session.commit()

    @staticmethod
    def get_priorities(session: Session) -> list[str]:
        ReferenceService.ensure_defaults(session)
        return session.execute(select(Priority.title).order_by(Priority.sort_order)).scalars().all()

    @staticmethod
    def get_responsibles(session: Session) -> list[str]:
        return session.execute(
            select(Responsible.full_name).where(Responsible.is_active.is_(True)).order_by(Responsible.full_name)
        ).scalars().all()

    @staticmethod
    def add_responsible(session: Session, full_name: str) -> None:
        full_name = full_name.strip()
        if not full_name:
            return
        exists = session.execute(select(Responsible).where(Responsible.full_name == full_name)).scalar_one_or_none()
        if exists:
            return
        session.add(Responsible(full_name=full_name))
        session.commit()
