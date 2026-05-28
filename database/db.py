import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


def get_app_dir() -> Path:
    """Return a stable writable application directory.

    In PyInstaller --onefile mode __file__ points to the temporary unpacked
    folder, so a SQLite database stored relative to __file__ disappears after
    the program closes. For frozen builds we store data next to the .exe.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


APP_DIR = get_app_dir()
DATA_DIR = APP_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "project_tracker.db"
DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    future=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def _column_names(connection, table_name: str) -> set[str]:
    rows = connection.exec_driver_sql(f"PRAGMA table_info({table_name})").fetchall()
    return {row[1] for row in rows}


def _table_exists(connection, table_name: str) -> bool:
    row = connection.exec_driver_sql(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    return row is not None


def _ensure_schema_updates() -> None:
    with engine.begin() as connection:
        if _table_exists(connection, "projects"):
            project_cols = _column_names(connection, "projects")
            if "original_target_date" not in project_cols:
                connection.exec_driver_sql("ALTER TABLE projects ADD COLUMN original_target_date DATE")
                connection.exec_driver_sql(
                    "UPDATE projects SET original_target_date = target_date WHERE original_target_date IS NULL"
                )

        if _table_exists(connection, "tasks"):
            task_cols = _column_names(connection, "tasks")
            if "planned_start_date" not in task_cols:
                connection.exec_driver_sql("ALTER TABLE tasks ADD COLUMN planned_start_date DATE")
            if "depends_on_enabled" not in task_cols:
                connection.exec_driver_sql("ALTER TABLE tasks ADD COLUMN depends_on_enabled BOOLEAN NOT NULL DEFAULT 0")
            if "depends_on_task_id" not in task_cols:
                connection.exec_driver_sql("ALTER TABLE tasks ADD COLUMN depends_on_task_id INTEGER")


def init_db() -> None:
    from models import app_setting, project, reference, task  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _ensure_schema_updates()
