"""
Review screen: shows extracted values, flags missing ones, lets user edit all fields.
'PO Oluştur' button stays disabled until all missing (None) fields are filled.
"""

import tkinter as tk
from tkinter import ttk, messagebox


class ReviewScreen:
    def __init__(self, root: tk.Tk, fields: list[dict], values: dict, on_confirm_callback):
        """
        fields: list of {"name": ..., "description": ...} from po_fields.json
        values: dict from quotation_extractor — None means not found
        on_confirm_callback: called with final_values dict when user clicks PO Oluştur
        """
        self.root = root
        self.fields = fields
        self.values = values
        self.on_confirm = on_confirm_callback
        self._entries: dict[str, tk.StringVar] = {}
        self._missing_names: set[str] = set()
        self.root.title("Veri Kontrolü — PO Oluşturmadan Önce")
        self._build_ui()

    def _build_ui(self):
        outer = ttk.Frame(self.root, padding=20)
        outer.grid(row=0, column=0, sticky="nsew")

        ttk.Label(outer, text="Veri Kontrolü", font=("Segoe UI", 12, "bold")).grid(
            row=0, column=0, columnspan=3, pady=(0, 12), sticky="w"
        )
        ttk.Label(
            outer,
            text="Tüm alanlar düzenlenebilir. ⚠️ ile işaretli alanlar teklifte bulunamadı.",
            foreground="gray",
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 10))

        for i, field in enumerate(self.fields, start=2):
            name  = field["name"]
            value = self.values.get(name)
            is_missing = value is None

            if is_missing:
                self._missing_names.add(name)
                icon  = "⚠️"
                color = "#cc6600"
            else:
                icon  = "✅"
                color = "#006600"

            ttk.Label(outer, text=f"{icon} {name}", foreground=color, width=22).grid(
                row=i, column=0, sticky="w", padx=(0, 8), pady=3
            )

            var = tk.StringVar(value="" if is_missing else str(value))
            self._entries[name] = var

            entry = ttk.Entry(outer, textvariable=var, width=45)
            entry.grid(row=i, column=1, sticky="ew", pady=3)
            var.trace_add("write", lambda *_: self._validate())

        # Buttons
        btn_row = len(self.fields) + 2
        ttk.Button(outer, text="İptal", command=self.root.destroy).grid(
            row=btn_row, column=0, pady=16, sticky="w"
        )
        self._confirm_btn = ttk.Button(
            outer, text="PO Oluştur", command=self._confirm, state="disabled"
        )
        self._confirm_btn.grid(row=btn_row, column=1, pady=16, sticky="e")

        self._validate()

    def _validate(self):
        """Enable confirm button only when all previously-missing fields are filled."""
        all_filled = all(
            self._entries[name].get().strip()
            for name in self._missing_names
        )
        self._confirm_btn.config(state="normal" if all_filled else "disabled")

    def _confirm(self):
        final_values = {name: var.get().strip() for name, var in self._entries.items()}
        self.on_confirm(final_values)
