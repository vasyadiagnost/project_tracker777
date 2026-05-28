import customtkinter as ctk
from tkinter import ttk

FONT = ("Segoe UI", 13)
FONT_BOLD = ("Segoe UI", 13, "bold")
TITLE_FONT = ("Segoe UI", 18, "bold")


def configure_theme() -> None:
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")


def configure_ttk_treeview_style() -> None:
    style = ttk.Style()
    try:
        style.theme_use("default")
    except Exception:
        pass

    style.configure(
        "Treeview",
        font=("Segoe UI", 10),
        rowheight=30,
        borderwidth=1,
        relief="flat",
    )
    style.configure(
        "Treeview.Heading",
        font=("Segoe UI", 10, "bold"),
        padding=(8, 8),
    )
    style.map(
        "Treeview",
        background=[("selected", "#DCEBFF")],
        foreground=[("selected", "#111111")],
    )
