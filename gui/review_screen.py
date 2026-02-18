"""
Review screen: shows extracted values, flags missing ones, lets user edit all fields.
'PO Oluştur' button stays disabled until all missing (None) fields are filled.
Scrollable so it works even with many fields.
"""

import tkinter as tk
from tkinter import ttk


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
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # ── Outer container ──────────────────────────────────────────────
        outer = ttk.Frame(self.root)
        outer.grid(row=0, column=0, sticky="nsew")
        outer.grid_rowconfigure(1, weight=1)
        outer.grid_columnconfigure(0, weight=1)

        # Header (fixed, not scrolled)
        header = ttk.Frame(outer, padding=(20, 16, 20, 0))
        header.grid(row=0, column=0, sticky="ew")
        ttk.Label(header, text="Veri Kontrolü", font=("Segoe UI", 12, "bold")).pack(
            anchor="w"
        )
        ttk.Label(
            header,
            text="Tüm alanlar düzenlenebilir. ⚠️ ile işaretli alanlar teklifte bulunamadı.",
            foreground="gray",
        ).pack(anchor="w", pady=(4, 0))

        # ── Scrollable middle section ─────────────────────────────────────
        scroll_frame = ttk.Frame(outer)
        scroll_frame.grid(row=1, column=0, sticky="nsew", padx=4)
        scroll_frame.grid_rowconfigure(0, weight=1)
        scroll_frame.grid_columnconfigure(0, weight=1)

        canvas = tk.Canvas(scroll_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(scroll_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.grid(row=0, column=1, sticky="ns")
        canvas.grid(row=0, column=0, sticky="nsew")

        inner = ttk.Frame(canvas, padding=(20, 8, 20, 8))
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_inner_resize(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _on_canvas_resize(event):
            canvas.itemconfig(win_id, width=event.width)

        inner.bind("<Configure>", _on_inner_resize)
        canvas.bind("<Configure>", _on_canvas_resize)

        # Mouse-wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind("<Enter>", lambda _: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda _: canvas.unbind_all("<MouseWheel>"))

        # ── Field rows ────────────────────────────────────────────────────
        for i, field in enumerate(self.fields):
            name = field["name"]
            value = self.values.get(name)
            is_missing = value is None

            if is_missing:
                self._missing_names.add(name)
                icon = "⚠️"
                color = "#cc6600"
            else:
                icon = "✅"
                color = "#006600"

            ttk.Label(inner, text=f"{icon} {name}", foreground=color, width=24).grid(
                row=i, column=0, sticky="w", padx=(0, 8), pady=2
            )

            var = tk.StringVar(value="" if is_missing else str(value))
            self._entries[name] = var

            ttk.Entry(inner, textvariable=var, width=44).grid(
                row=i, column=1, sticky="ew", pady=2
            )
            var.trace_add("write", lambda *_: self._validate())

        # ── Button bar (fixed, not scrolled) ─────────────────────────────
        btn_bar = ttk.Frame(outer, padding=(20, 8, 20, 16))
        btn_bar.grid(row=2, column=0, sticky="ew")
        ttk.Button(btn_bar, text="İptal", command=self.root.destroy).pack(side="left")
        self._confirm_btn = ttk.Button(
            btn_bar, text="PO Oluştur", command=self._confirm, state="disabled"
        )
        self._confirm_btn.pack(side="right")

        # ── Window height: max 80% of screen ─────────────────────────────
        self.root.update_idletasks()
        screen_h = self.root.winfo_screenheight()
        win_h = min(self.root.winfo_reqheight(), int(screen_h * 0.82))
        self.root.geometry(f"680x{win_h}")

        self._validate()

    def _validate(self):
        all_filled = all(
            self._entries[name].get().strip() for name in self._missing_names
        )
        self._confirm_btn.config(state="normal" if all_filled else "disabled")

    def _confirm(self):
        final_values = {name: var.get().strip() for name, var in self._entries.items()}
        self.on_confirm(final_values)
