from tkinter import messagebox, ttk

import customtkinter as ctk

from models.reference import Responsible
from services.reference_service import ReferenceService


class DictionariesTab:
    def __init__(self, parent, session, app):
        self.parent = parent
        self.session = session
        self.app = app
        self.tree = None
        self.name_entry = None
        self._build_ui()

    def _build_ui(self):
        top = ctk.CTkFrame(self.parent)
        top.pack(fill="x", padx=10, pady=10)

        self.name_entry = ctk.CTkEntry(top, placeholder_text="ФИО ответственного", width=360)
        self.name_entry.pack(side="left", padx=(8, 16), pady=8)
        ctk.CTkButton(top, text="Добавить", width=160, command=self._add).pack(side="left", padx=(0, 8), pady=8)
        ctk.CTkButton(top, text="Удалить", width=160, command=self._delete_selected).pack(side="left", padx=(0, 8), pady=8)
        ctk.CTkButton(top, text="На главную", command=lambda: self.app.tabview.set("Главная")).pack(side="right", padx=8, pady=8)

        table = ctk.CTkFrame(self.parent)
        table.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.tree = ttk.Treeview(table, columns=("name", "active"), show="headings")
        self.tree.heading("name", text="Ответственный")
        self.tree.heading("active", text="Активен")
        self.tree.column("name", width=420)
        self.tree.column("active", width=120)
        self.tree.pack(fill="both", expand=True, padx=6, pady=6)

    def _add(self):
        full_name = self.name_entry.get().strip()
        if not full_name:
            messagebox.showerror("Ошибка", "Укажите ФИО.")
            return
        ReferenceService.add_responsible(self.session, full_name)
        self.name_entry.delete(0, "end")
        self.app.refresh_all()

    def _delete_selected(self):
        selection = self.tree.selection()
        if not selection:
            return
        row_id = int(selection[0])
        row = self.session.get(Responsible, row_id)
        if not row:
            return
        if not messagebox.askyesno("Подтверждение", f"Удалить '{row.full_name}'?"):
            return
        self.session.delete(row)
        self.session.commit()
        self.app.refresh_all()

    def refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        rows = self.session.query(Responsible).order_by(Responsible.full_name).all()
        for row in rows:
            self.tree.insert("", "end", iid=str(row.id), values=(row.full_name, "Да" if row.is_active else "Нет"))
