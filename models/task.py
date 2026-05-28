from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.db import Base


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    stage_id: Mapped[int | None] = mapped_column(ForeignKey("stages.id", ondelete="SET NULL"), nullable=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)

    initiator: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    dri: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    co_executors: Mapped[str] = mapped_column(Text, default="", nullable=False)
    controller: Mapped[str] = mapped_column(String(255), default="", nullable=False)

    status: Mapped[str] = mapped_column(String(50), default="Новая", nullable=False)
    priority: Mapped[str] = mapped_column(String(50), default="Средний", nullable=False)

    planned_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    control_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    depends_on_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    depends_on_task_id: Mapped[int | None] = mapped_column(ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True)

    next_step: Mapped[str] = mapped_column(Text, default="", nullable=False)
    expected_result: Mapped[str] = mapped_column(Text, default="", nullable=False)
    waiting_for: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    blocker_note: Mapped[str] = mapped_column(Text, default="", nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    project: Mapped["Project"] = relationship("Project", back_populates="tasks")
    stage: Mapped["Stage | None"] = relationship("Stage", back_populates="tasks")
    dependency_task: Mapped["Task | None"] = relationship("Task", remote_side=[id], foreign_keys=[depends_on_task_id])
    history: Mapped[list["TaskHistory"]] = relationship(
        "TaskHistory",
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="TaskHistory.created_at.desc()",
    )


class TaskHistory(Base):
    __tablename__ = "task_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)

    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    old_value: Mapped[str] = mapped_column(Text, default="", nullable=False)
    new_value: Mapped[str] = mapped_column(Text, default="", nullable=False)

    comment: Mapped[str] = mapped_column(Text, default="", nullable=False)
    author: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)

    task: Mapped["Task"] = relationship("Task", back_populates="history")
