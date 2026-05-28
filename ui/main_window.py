import customtkinter as ctk

from database import SessionLocal, init_db
from services.reference_service import ReferenceService
from services.settings_service import SettingsService
from ui.styles import configure_theme, configure_ttk_treeview_style
from ui.clipboard_shortcuts import add_clipboard_shortcuts
from ui.tabs.dashboard_tab import DashboardTab
from ui.tabs.dictionaries_tab import DictionariesTab
from ui.tabs.projects_tab import ProjectsTab
from ui.tabs.reports_tab import ReportsTab
from ui.tabs.settings_tab import SettingsTab
from ui.tabs.tasks_tab import TasksTab


class MainWindow(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        configure_theme()
        configure_ttk_treeview_style()
        init_db()

        self.title("Project Tracker Desktop")
        self.geometry("1480x860")
        self.minsize(1280, 760)

        self.session = SessionLocal()
        ReferenceService.ensure_defaults(self.session)
        SettingsService.ensure_defaults(self.session)

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        add_clipboard_shortcuts(self)

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=12, pady=12)

        for tab_name in ["Главная", "Проекты", "Задачи", "Сводки", "Справочники", "Настройки"]:
            self.tabview.add(tab_name)

        self.dashboard_tab = DashboardTab(self.tabview.tab("Главная"), self.session, self)
        self.projects_tab = ProjectsTab(self.tabview.tab("Проекты"), self.session, self)
        self.tasks_tab = TasksTab(self.tabview.tab("Задачи"), self.session, self)
        self.reports_tab = ReportsTab(self.tabview.tab("Сводки"), self.session, self)
        self.dictionaries_tab = DictionariesTab(self.tabview.tab("Справочники"), self.session, self)
        self.settings_tab = SettingsTab(self.tabview.tab("Настройки"), self.session, self)

        self.refresh_all()

    def refresh_all(self) -> None:
        self.dashboard_tab.refresh()
        self.projects_tab.refresh()
        self.tasks_tab.refresh()
        self.reports_tab.refresh()
        self.dictionaries_tab.refresh()
        self.settings_tab.refresh()

    def open_task(self, task_id: int) -> None:
        self.tabview.set("Задачи")
        self.tasks_tab.refresh()
        self.tasks_tab.edit_task_by_id(task_id)

    def open_project(self, project_id: int) -> None:
        self.tabview.set("Проекты")
        self.projects_tab.refresh()
        self.projects_tab.select_project(project_id)
        self.projects_tab.edit_project(project_id)

    def on_close(self) -> None:
        self.session.close()
        self.destroy()
