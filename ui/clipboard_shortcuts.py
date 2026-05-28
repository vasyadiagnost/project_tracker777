"""Context-menu clipboard support for Tkinter/customtkinter text widgets.

Adds only the right-click menu for copy/paste/cut/select-all.
No keyboard bindings are installed, so normal typing in any keyboard layout
is not intercepted by the app.
"""

from __future__ import annotations

import tkinter as tk

try:
    import customtkinter as ctk
except Exception:  # pragma: no cover
    ctk = None  # type: ignore[assignment]


_TEXT_WIDGET_CLASSES = (tk.Entry, tk.Text)


def _is_custom_text_widget(widget: tk.Widget) -> bool:
    if ctk is None:
        return False
    return isinstance(widget, (ctk.CTkEntry, ctk.CTkTextbox))


def _is_text_widget(widget: tk.Widget) -> bool:
    return isinstance(widget, _TEXT_WIDGET_CLASSES) or _is_custom_text_widget(widget)


def _inner_text_widget(widget: tk.Widget) -> tk.Widget:
    """Return the real Tk widget behind CTkEntry/CTkTextbox when possible."""
    for attr_name in ("_entry", "_textbox"):
        inner = getattr(widget, attr_name, None)
        if inner is not None:
            return inner
    return widget


def _select_all(widget: tk.Widget) -> None:
    try:
        if isinstance(widget, tk.Text):
            widget.tag_add("sel", "1.0", "end-1c")
            widget.mark_set("insert", "1.0")
        else:
            widget.select_range(0, "end")  # type: ignore[attr-defined]
            widget.icursor("end")  # type: ignore[attr-defined]
    except tk.TclError:
        pass


def _run_action(widget: tk.Widget, virtual_event: str) -> None:
    try:
        if virtual_event == "<<SelectAll>>":
            _select_all(widget)
        else:
            widget.event_generate(virtual_event)
    except tk.TclError:
        pass


def add_clipboard_shortcuts(root: tk.Misc) -> None:
    """Install only right-click clipboard context menu for the whole app."""

    def show_context_menu(event: tk.Event) -> str | None:
        widget = event.widget
        if widget is None:
            return None

        target = _inner_text_widget(widget) if _is_text_widget(widget) else widget
        if not isinstance(target, _TEXT_WIDGET_CLASSES):
            return None

        try:
            target.focus_set()
        except tk.TclError:
            pass

        menu = tk.Menu(target, tearoff=0)
        menu.add_command(label="Вырезать", command=lambda: _run_action(target, "<<Cut>>"))
        menu.add_command(label="Копировать", command=lambda: _run_action(target, "<<Copy>>"))
        menu.add_command(label="Вставить", command=lambda: _run_action(target, "<<Paste>>"))
        menu.add_separator()
        menu.add_command(label="Выделить всё", command=lambda: _run_action(target, "<<SelectAll>>"))

        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
        return "break"

    root.bind_all("<Button-3>", show_context_menu, add="+")
    root.bind_all("<Control-Button-1>", show_context_menu, add="+")  # macOS fallback
