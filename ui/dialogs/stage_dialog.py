from datetime import datetime

import customtkinter as ctk
from tkinter import messagebox

from models.project import Stage
from services.reference_service import ReferenceService
from ui.dialogs.date_picker_dialog import DatePickerDialog, parse_date_safe


class StageDialog(ctk.CTkToplevel):
    def __init__(self, master, session, on_saved, project_id: int, stage: Stage | None = None):
        super().__init__(master)
        self.session = session
        self.on_saved = on_saved
        self.project_id = project_id
        self.stage = stage

        self.title("Этап")
        self.geometry("700x520")
        self.minsize(640, 420)
        self.grab_set()

        self.responsibles = ReferenceService.get_responsibles(self.session)
        self._build_ui()
        self._bind_date_button()

        if self.stage:
            self.title_entry.insert(0, self.stage.title)
            self.dri_combo.set(self.stage.dri)
            self.status_combo.set(self.stage.status)
            self.order_entry.delete(0, "end")
            self.order_entry.insert(0, str(self.stage.sort_order))
            if self.stage.target_date:
                self.target_entry.insert(0, self.stage.target_date.strftime("%d.%m.%Y"))
            self.notes_text.insert("1.0", self.stage.notes)

    def _build_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.form = ctk.CTkScrollableFrame(self)
        self.form.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        self.form.grid_columnconfigure(1, weight=1)

        row = 0
        ctk.CTkLabel(self.form, text="Название").grid(row=row, column=0, sticky="w", padx=12, pady=8)
        self.title_entry = ctk.CTkEntry(self.form)
        self.title_entry.grid(row=row, column=1, sticky="ew", padx=12, pady=8)
        row += 1

        ctk.CTkLabel(self.form, text="DRI").grid(row=row, column=0, sticky="w", padx=12, pady=8)
        self.dri_combo = ctk.CTkComboBox(self.form, values=self.responsibles or [""])
        self.dri_combo.grid(row=row, column=1, sticky="ew", padx=12, pady=8)
        row += 1

        ctk.CTkLabel(self.form, text="Статус").grid(row=row, column=0, sticky="w", padx=12, pady=8)
        self.status_combo = ctk.CTkComboBox(self.form, values=["Не начат", "В работе", "На паузе", "Завершён"])
        self.status_combo.grid(row=row, column=1, sticky="ew", padx=12, pady=8)
        self.status_combo.set("Не начат")
        row += 1

        ctk.CTkLabel(self.form, text="Порядок").grid(row=row, column=0, sticky="w", padx=12, pady=8)
        self.order_entry = ctk.CTkEntry(self.form)
        self.order_entry.grid(row=row, column=1, sticky="ew", padx=12, pady=8)
        self.order_entry.insert(0, "0")
        row += 1

        ctk.CTkLabel(self.form, text="Срок (дд.мм.гггг)").grid(row=row, column=0, sticky="w", padx=12, pady=8)
        frame = ctk.CTkFrame(self.form, fg_color="transparent")
        frame.grid(row=row, column=1, sticky="ew", padx=12, pady=8)
        frame.grid_columnconfigure(0, weight=1)
        self.target_entry = ctk.CTkEntry(frame)
        self.target_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.target_button = ctk.CTkButton(frame, text="📅", width=46)
        self.target_button.grid(row=0, column=1)
        row += 1

        ctk.CTkLabel(self.form, text="Заметки").grid(row=row, column=0, sticky="nw", padx=12, pady=8)
        self.notes_text = ctk.CTkTextbox(self.form, height=160)
        self.notes_text.grid(row=row, column=1, sticky="nsew", padx=12, pady=8)
        row += 1

        buttons = ctk.CTkFrame(self.form, fg_color="transparent")
        buttons.grid(row=row, column=0, columnspan=2, sticky="e", padx=12, pady=12)
        ctk.CTkButton(buttons, text="Сохранить", command=self._save).pack(side="right", padx=(8, 0))
        ctk.CTkButton(buttons, text="Отмена", command=self.destroy).pack(side="right")

    def _bind_date_button(self):
        def _open():
            try:
                initial = parse_date_safe(self.target_entry.get())
            except Exception:
                initial = None

            def _set(picked):
                self.target_entry.delete(0, "end")
                if picked:
                    self.target_entry.insert(0, picked.strftime("%d.%m.%Y"))

            DatePickerDialog(self, initial_date=initial, on_select=_set)

        self.target_button.configure(command=_open)

    @staticmethod
    def _parse_date(value: str):
        value = value.strip()
        if not value:
            return None
        try:
            return datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("Дата должна быть в формате дд.мм.гггг")

    def _save(self):
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showerror("Ошибка", "Укажите название этапа.")
            return

        try:
            sort_order = int(self.order_entry.get().strip() or "0")
            target_date = self._parse_date(self.target_entry.get())
        except Exception as exc:
            messagebox.showerror("Ошибка", str(exc))
            return

        if self.stage:
            self.stage.title = title
            self.stage.dri = self.dri_combo.get().strip()
            self.stage.status = self.status_combo.get().strip()
            self.stage.sort_order = sort_order
            self.stage.target_date = target_date
            self.stage.notes = self.notes_text.get("1.0", "end").strip()
        else:
            self.session.add(
                Stage(
                    project_id=self.project_id,
                    title=title,
                    dri=self.dri_combo.get().strip(),
                    status=self.status_combo.get().strip(),
                    sort_order=sort_order,
                    target_date=target_date,
                    notes=self.notes_text.get("1.0", "end").strip(),
                )
            )
        self.session.commit()
        self.on_saved()
        self.destroy()
