from datetime import datetime

import customtkinter as ctk
from tkinter import messagebox

from services.project_service import ProjectService
from services.reference_service import ReferenceService
from ui.dialogs.date_picker_dialog import DatePickerDialog, parse_date_safe


class ProjectDialog(ctk.CTkToplevel):
    def __init__(self, master, session, on_saved, project=None):
        super().__init__(master)
        self.session = session
        self.on_saved = on_saved
        self.project = project
        self.create_default_stages_var = ctk.BooleanVar(value=project is None)

        self.title("Проект")
        self.geometry("860x760")
        self.minsize(760, 620)
        self.grab_set()

        self.responsibles = ReferenceService.get_responsibles(self.session)
        self._build_ui()
        self._bind_date_buttons()
        self._fill_if_edit()

    def _build_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.form = ctk.CTkScrollableFrame(self)
        self.form.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        self.form.grid_columnconfigure(1, weight=1)

        row = 0
        self._add_label("Название", row)
        self.title_entry = ctk.CTkEntry(self.form)
        self.title_entry.grid(row=row, column=1, sticky="ew", padx=12, pady=6)
        row += 1

        self._add_label("Инициатор", row)
        self.initiator_entry = ctk.CTkEntry(self.form)
        self.initiator_entry.grid(row=row, column=1, sticky="ew", padx=12, pady=6)
        row += 1

        self._add_label("DRI", row)
        self.dri_combo = ctk.CTkComboBox(self.form, values=self.responsibles or [""])
        self.dri_combo.grid(row=row, column=1, sticky="ew", padx=12, pady=6)
        row += 1

        self._add_label("Статус", row)
        self.status_combo = ctk.CTkComboBox(self.form, values=ProjectService.PROJECT_STATUSES)
        self.status_combo.grid(row=row, column=1, sticky="ew", padx=12, pady=6)
        self.status_combo.set("Инициирован")
        row += 1

        self._add_label("Приоритет", row)
        self.priority_combo = ctk.CTkComboBox(self.form, values=ProjectService.PROJECT_PRIORITIES)
        self.priority_combo.grid(row=row, column=1, sticky="ew", padx=12, pady=6)
        self.priority_combo.set("Средний")
        row += 1

        self._add_label("Дата начала (дд.мм.гггг)", row)
        self.start_date_entry, self.start_date_button = self._create_date_row(row)
        row += 1

        self._add_label("Целевая дата (дд.мм.гггг)", row)
        self.target_date_entry, self.target_date_button = self._create_date_row(row)
        row += 1

        self._add_label("Исходная целевая дата", row)
        self.original_target_entry = ctk.CTkEntry(self.form)
        self.original_target_entry.grid(row=row, column=1, sticky="ew", padx=12, pady=6)
        self.original_target_entry.configure(state="disabled")
        row += 1

        if not self.project:
            self._add_label("Структура этапов", row)
            self.default_stages_checkbox = ctk.CTkCheckBox(
                self.form,
                text="Создать стандартную структуру этапов проекта",
                variable=self.create_default_stages_var,
            )
            self.default_stages_checkbox.grid(row=row, column=1, sticky="w", padx=12, pady=6)
            row += 1

        self._add_label("Описание", row)
        self.description_text = ctk.CTkTextbox(self.form, height=140)
        self.description_text.grid(row=row, column=1, sticky="nsew", padx=12, pady=6)
        row += 1

        self._add_label("Заметки", row)
        self.notes_text = ctk.CTkTextbox(self.form, height=140)
        self.notes_text.grid(row=row, column=1, sticky="nsew", padx=12, pady=6)
        row += 1

        button_frame = ctk.CTkFrame(self.form, fg_color="transparent")
        button_frame.grid(row=row, column=0, columnspan=2, sticky="e", padx=12, pady=12)
        ctk.CTkButton(button_frame, text="Сохранить", width=140, command=self._save).pack(side="right", padx=(8, 0))
        ctk.CTkButton(button_frame, text="Отмена", width=140, command=self.destroy).pack(side="right")

    def _create_date_row(self, row: int):
        frame = ctk.CTkFrame(self.form, fg_color="transparent")
        frame.grid(row=row, column=1, sticky="ew", padx=12, pady=6)
        frame.grid_columnconfigure(0, weight=1)

        entry = ctk.CTkEntry(frame)
        entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        button = ctk.CTkButton(frame, text="📅", width=46)
        button.grid(row=0, column=1)
        return entry, button

    def _bind_date_buttons(self):
        self.start_date_button.configure(command=self._bind_date_button(self.start_date_entry))
        self.target_date_button.configure(command=self._bind_date_button(self.target_date_entry))

    def _bind_date_button(self, entry_widget):
        def _open():
            try:
                initial = parse_date_safe(entry_widget.get())
            except Exception:
                initial = None

            def _set(picked):
                entry_widget.delete(0, "end")
                if picked:
                    entry_widget.insert(0, picked.strftime("%d.%m.%Y"))

            DatePickerDialog(self, initial_date=initial, on_select=_set)

        return _open

    def _add_label(self, text: str, row: int) -> None:
        ctk.CTkLabel(self.form, text=text, anchor="w").grid(row=row, column=0, sticky="w", padx=12, pady=6)

    def _set_original_target(self, value: str):
        self.original_target_entry.configure(state="normal")
        self.original_target_entry.delete(0, "end")
        if value:
            self.original_target_entry.insert(0, value)
        self.original_target_entry.configure(state="disabled")

    def _fill_if_edit(self):
        if not self.project:
            return
        self.title_entry.insert(0, self.project.title)
        self.initiator_entry.insert(0, self.project.initiator)
        self.dri_combo.set(self.project.dri)
        self.status_combo.set(self.project.status)
        self.priority_combo.set(self.project.priority)
        if self.project.start_date:
            self.start_date_entry.insert(0, self.project.start_date.strftime("%d.%m.%Y"))
        if self.project.target_date:
            self.target_date_entry.insert(0, self.project.target_date.strftime("%d.%m.%Y"))
        if self.project.original_target_date:
            self._set_original_target(self.project.original_target_date.strftime("%d.%m.%Y"))
        self.description_text.insert("1.0", self.project.description)
        self.notes_text.insert("1.0", self.project.notes)

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
            messagebox.showerror("Ошибка", "Укажите название проекта.")
            return

        try:
            target_date = self._parse_date(self.target_date_entry.get())
            original_target = None
            if self.project and self.project.original_target_date:
                original_target = self.project.original_target_date
            elif target_date:
                original_target = target_date

            data = {
                "title": title,
                "initiator": self.initiator_entry.get().strip(),
                "dri": self.dri_combo.get().strip(),
                "status": self.status_combo.get().strip(),
                "priority": self.priority_combo.get().strip(),
                "start_date": self._parse_date(self.start_date_entry.get()),
                "target_date": target_date,
                "original_target_date": original_target,
                "description": self.description_text.get("1.0", "end").strip(),
                "notes": self.notes_text.get("1.0", "end").strip(),
            }
            if self.project:
                ProjectService.update_project(self.session, self.project.id, data)
            else:
                ProjectService.create_project(
                    self.session,
                    data,
                    create_default_stages=self.create_default_stages_var.get(),
                )
        except Exception as exc:
            messagebox.showerror("Ошибка", str(exc))
            return

        self.on_saved()
        self.destroy()
