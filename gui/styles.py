"""UI Styling, color palettes, and ttk widget themes."""

import tkinter as tk
from tkinter import ttk

# Modern Dark / Slate Color Palette
COLORS = {
    "bg_main": "#1e1e2e",
    "bg_card": "#2a2b3d",
    "bg_input": "#181825",
    "fg_text": "#cdd6f4",
    "fg_muted": "#a6adc8",
    "accent_primary": "#89b4fa",
    "accent_success": "#a6e3a1",
    "accent_danger": "#f38ba8",
    "accent_warning": "#f9e2af",
    "border": "#45475a",
}

FONTS = {
    "title": ("Segoe UI", 16, "bold"),
    "subtitle": ("Segoe UI", 12, "bold"),
    "body": ("Segoe UI", 10),
    "body_bold": ("Segoe UI", 10, "bold"),
    "code": ("Consolas", 9),
    "small": ("Segoe UI", 8),
}

def apply_app_styles(root: tk.Tk) -> ttk.Style:
    """Configures ttk styles for consistent modern look and feel."""
    style = ttk.Style(root)
    style.theme_use("clam")

    # Frame backgrounds
    style.configure("Main.TFrame", background=COLORS["bg_main"])
    style.configure("Card.TFrame", background=COLORS["bg_card"], relief="solid", borderwidth=1)

    # Labels
    style.configure("TLabel", background=COLORS["bg_main"], foreground=COLORS["fg_text"], font=FONTS["body"])
    style.configure("Card.TLabel", background=COLORS["bg_card"], foreground=COLORS["fg_text"], font=FONTS["body"])
    style.configure("CardTitle.TLabel", background=COLORS["bg_card"], foreground=COLORS["accent_primary"], font=FONTS["subtitle"])
    style.configure("Muted.TLabel", background=COLORS["bg_card"], foreground=COLORS["fg_muted"], font=FONTS["small"])

    # Buttons
    style.configure(
        "Primary.TButton",
        background=COLORS["accent_primary"],
        foreground="#11111b",
        font=FONTS["body_bold"],
        padding=6,
    )
    style.map(
        "Primary.TButton",
        background=[("active", "#74c7ec"), ("disabled", "#585b70")]
    )

    style.configure(
        "Action.TButton",
        background=COLORS["accent_success"],
        foreground="#11111b",
        font=FONTS["body_bold"],
        padding=8,
    )

    # Notebook Tabs
    style.configure("TNotebook", background=COLORS["bg_main"], tabmargins=[2, 5, 2, 0])
    style.configure(
        "TNotebook.Tab",
        background=COLORS["bg_card"],
        foreground=COLORS["fg_text"],
        padding=[12, 6],
        font=FONTS["body_bold"]
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", COLORS["accent_primary"])],
        foreground=[("selected", "#11111b")]
    )

    return style
