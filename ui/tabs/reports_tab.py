from tkinter import filedialog, messagebox

import customtkinter as ctk

from exports import ReportExporter
from services.dashboard_service import DashboardService
from services.report_service import ReportService
from services.task_service import TaskService


class ReportsTab:
    def __init__(self, parent, session, app):
        self.parent = parent
        self.session = session
        self.app = app
        self.textbox = None
        self.project_combo = None
        self.dri_combo = None
        self.current_title = "СВОДКА"
        self.current_rows: list[dict] = []
        self._build_ui()

    def _build_ui(self):
        top = ctk.CTkFrame(self.parent)
        top.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(top, text="Красная зона", command=self._build_red_zone).pack(side="left")
        ctk.CTkButton(top, text="3 дня", command=self._build_three_days).pack(side="left", padx=8)
        ctk.CTkButton(top, text="Ожидаем ответ", command=self._build_waiting).pack(side="left", padx=8)

        project_wrap = ctk.CTkFrame(top, fg_color="transparent")
        project_wrap.pack(side="left", padx=(24, 8))
        ctk.CTkLabel(project_wrap, text="Название проекта").pack(anchor="w")
        self.project_combo = ctk.CTkComboBox(project_wrap, values=[""], width=180)
        self.project_combo.pack(anchor="w")
        ctk.CTkButton(top, text="По проекту", command=self._build_project_report).pack(side="left", padx=8)

        dri_wrap = ctk.CTkFrame(top, fg_color="transparent")
        dri_wrap.pack(side="left", padx=(24, 8))
        ctk.CTkLabel(dri_wrap, text="DRI / ответственный").pack(anchor="w")
        self.dri_combo = ctk.CTkComboBox(dri_wrap, values=[""], width=180)
        self.dri_combo.pack(anchor="w")
        ctk.CTkButton(top, text="По DRI", command=self._build_dri_report).pack(side="left", padx=8)

        ctk.CTkButton(top, text="На главную", command=lambda: self.app.tabview.set("Главная")).pack(side="right")

        export_bar = ctk.CTkFrame(self.parent, fg_color="transparent")
        export_bar.pack(fill="x", padx=10, pady=(0, 6))
        ctk.CTkButton(export_bar, text="Копировать", command=self._copy_text).pack(side="left")
        ctk.CTkButton(export_bar, text="Экспорт TXT", command=self._export_txt).pack(side="left", padx=8)
        ctk.CTkButton(export_bar, text="Экспорт XLSX", command=self._export_xlsx).pack(side="left", padx=8)
        ctk.CTkButton(export_bar, text="Экспорт PDF", command=self._export_pdf).pack(side="left", padx=8)

        self.textbox = ctk.CTkTextbox(self.parent)
        self.textbox.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _set_text(self, title: str, rows: list[dict]) -> None:
        self.current_title = title
        self.current_rows = rows
        text = ReportService.rows_to_text(title, rows)
        self.textbox.delete("1.0", "end")
        self.textbox.insert("1.0", text)

    def _copy_text(self):
        text = self.textbox.get("1.0", "end").strip()
        self.app.clipboard_clear()
        self.app.clipboard_append(text)
        messagebox.showinfo("Готово", "Текст сводки скопирован.")

    def _export_txt(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if not path:
            return
        ReportExporter.export_txt(path, self.textbox.get("1.0", "end").strip())
        messagebox.showinfo("Готово", "TXT-отчёт сохранён.")

    def _export_xlsx(self):
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if not path:
            return
        ReportExporter.export_xlsx(path, self.current_title, self.current_rows)
        messagebox.showinfo("Готово", "Excel-отчёт сохранён.")

    def _export_pdf(self):
        path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if not path:
            return
        lines = self.textbox.get("1.0", "end").strip().splitlines()
        ReportExporter.export_pdf(path, self.current_title, lines)
        messagebox.showinfo("Готово", "PDF-отчёт сохранён.")

    def _build_red_zone(self):
        self._set_text("КРАСНАЯ ЗОНА", ReportService.get_red_zone_rows(self.session))

    def _build_three_days(self):
        self._set_text("ЧТО ТРЕБУЕТ ВНИМАНИЯ В БЛИЖАЙШИЕ 3 ДНЯ", ReportService.get_three_days_rows(self.session))

    def _build_waiting(self):
        self._set_text("ОЖИДАЕМ ОТВЕТ", ReportService.get_waiting_rows(self.session))

    def _build_project_report(self):
        projects_map = TaskService.get_projects_map(self.session)
        selected = self.project_combo.get().strip()
        project_id = None
        for pid, title in projects_map.items():
            if title == selected:
                project_id = pid
                break
        if not project_id:
            messagebox.showerror("Ошибка", "Выбери проект.")
            return
        self._set_text(f"СВОДКА ПО ПРОЕКТУ: {selected}", ReportService.get_project_rows(self.session, project_id))

    def _build_dri_report(self):
        dri = self.dri_combo.get().strip()
        if not dri:
            messagebox.showerror("Ошибка", "Выбери DRI.")
            return
        self._set_text(f"СВОДКА ПО DRI: {dri}", ReportService.get_dri_rows(self.session, dri))

    def refresh(self):
        counters = DashboardService.get_counters(self.session)
        projects_map = TaskService.get_projects_map(self.session)
        self.project_combo.configure(values=[""] + list(projects_map.values()))
        dri_values = sorted({row["dri"] for row in TaskService.list_tasks(self.session, only_active=False) if row["dri"]})
        self.dri_combo.configure(values=[""] + dri_values)

        self.textbox.delete("1.0", "end")
        self.textbox.insert(
            "1.0",
            "\n".join(
                [
                    "СВОДКА ПО СИСТЕМЕ",
                    "",
                    *(f"• {key}: {value}" for key, value in counters.items()),
                    "",
                    "Используй кнопки сверху для генерации отчётов.",
                ]
            ),
        )
        self.current_title = "СВОДКА ПО СИСТЕМЕ"
        self.current_rows = []
