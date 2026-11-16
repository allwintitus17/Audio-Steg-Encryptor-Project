"""Reusable File Picker Component with Browse Dialog."""

import os
import tkinter as tk
from tkinter import ttk, filedialog
from typing import Callable, Optional, List, Tuple

class FilePicker(ttk.Frame):
    """A composite widget providing a path entry, browse button, and file info display."""

    def __init__(
        self,
        master,
        label_text: str,
        file_types: List[Tuple[str, str]],
        is_save_dialog: bool = False,
        on_change_callback: Optional[Callable[[str], None]] = None,
        default_extension: str = "",
        **kwargs
    ):
        super().__init__(master, style="Card.TFrame", **kwargs)
        self.label_text = label_text
        self.file_types = file_types
        self.is_save_dialog = is_save_dialog
        self.on_change_callback = on_change_callback
        self.default_extension = default_extension

        self.path_var = tk.StringVar()
        self._build_ui()

    def _build_ui(self):
        # Header Label
        lbl = ttk.Label(self, text=self.label_text, style="CardTitle.TLabel")
        lbl.pack(anchor="w", padx=10, pady=(8, 2))

        # Input & Button Row
        row = ttk.Frame(self, style="Card.TFrame")
        row.pack(fill="x", padx=10, pady=(0, 6))

        self.entry = ttk.Entry(row, textvariable=self.path_var)
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 6), ipady=3)

        btn = ttk.Button(row, text="Browse...", command=self._browse, style="Primary.TButton")
        btn.pack(side="right")

        # Details / File Size label
        self.info_label = ttk.Label(self, text="No file selected", style="Muted.TLabel")
        self.info_label.pack(anchor="w", padx=10, pady=(0, 8))

    def _browse(self):
        if self.is_save_dialog:
            selected = filedialog.asksaveasfilename(
                title=f"Save As - {self.label_text}",
                filetypes=self.file_types,
                defaultextension=self.default_extension,
            )
        else:
            selected = filedialog.askopenfilename(
                title=f"Select - {self.label_text}",
                filetypes=self.file_types,
            )

        if selected:
            self.set_path(selected)

    def set_path(self, path: str):
        self.path_var.set(path)
        if os.path.exists(path):
            size = os.path.getsize(path)
            self.info_label.config(text=f"Selected: {os.path.basename(path)} ({size:,} bytes)")
        else:
            self.info_label.config(text=f"Path: {path}")

        if self.on_change_callback:
            self.on_change_callback(path)

    def get_path(self) -> str:
        return self.path_var.get().strip()
