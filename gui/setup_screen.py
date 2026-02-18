"""
First-run setup wizard.
Collects: example PO path, API key, model selection.
Calls template_analyzer, saves config.json, then transitions to generate screen.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading

from core.template_analyzer import analyze_example_po
from core.config import save_config, DEFAULT_CONFIG_PATH, DEFAULT_TEMPLATE_PATH, DEFAULT_FIELDS_PATH

MODELS = [
    "claude-sonnet-4-6",
    "claude-opus-4-6",
    "claude-haiku-4-5-20251001",
]


class SetupScreen:
    def __init__(self, root: tk.Tk, on_complete_callback):
        """
        on_complete_callback: called with no args when setup finishes.
        The caller (main.py) is responsible for destroying root and opening GenerateScreen.
        """
        self.root = root
        self.on_complete = on_complete_callback
        self.root.title("PO Generator — İlk Kurulum")
        self.root.resizable(False, False)
        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 12, "pady": 6}
        frame = ttk.Frame(self.root, padding=20)
        frame.grid(row=0, column=0, sticky="nsew")

        # Title
        ttk.Label(frame, text="PO Generator — İlk Kurulum", font=("Segoe UI", 13, "bold")).grid(
            row=0, column=0, columnspan=3, pady=(0, 16), sticky="w"
        )

        # 1. Example PO
        ttk.Label(frame, text="1. Örnek PO (PDF):").grid(row=1, column=0, sticky="w", **pad)
        self._po_path_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self._po_path_var, width=45).grid(row=1, column=1, **pad)
        ttk.Button(frame, text="Seç", command=self._browse_po).grid(row=1, column=2, **pad)

        # 2. API Key
        ttk.Label(frame, text="2. Anthropic API Key:").grid(row=2, column=0, sticky="w", **pad)
        self._api_key_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self._api_key_var, width=45, show="*").grid(
            row=2, column=1, columnspan=2, sticky="ew", **pad
        )

        # 3. Model
        ttk.Label(frame, text="3. Model:").grid(row=3, column=0, sticky="nw", **pad)
        self._model_var = tk.StringVar(value=MODELS[0])
        model_frame = ttk.Frame(frame)
        model_frame.grid(row=3, column=1, columnspan=2, sticky="w", **pad)
        for model in MODELS:
            ttk.Radiobutton(model_frame, text=model, variable=self._model_var, value=model).pack(
                anchor="w"
            )

        # Status label
        self._status_var = tk.StringVar(value="")
        ttk.Label(frame, textvariable=self._status_var, foreground="gray").grid(
            row=4, column=0, columnspan=3, sticky="w", padx=12
        )

        # Button
        self._btn = ttk.Button(frame, text="Şablonu Oluştur", command=self._start_analysis)
        self._btn.grid(row=5, column=0, columnspan=3, pady=16)

    def _browse_po(self):
        path = filedialog.askopenfilename(
            title="Örnek PO seçin", filetypes=[("PDF files", "*.pdf")]
        )
        if path:
            self._po_path_var.set(path)

    def _start_analysis(self):
        po_path = self._po_path_var.get().strip()
        api_key = self._api_key_var.get().strip()
        model   = self._model_var.get()

        if not po_path:
            messagebox.showerror("Hata", "Lütfen örnek PO dosyasını seçin.")
            return
        if not api_key:
            messagebox.showerror("Hata", "Lütfen API key girin.")
            return

        self._btn.config(state="disabled")
        self._status_var.set("Analiz ediliyor, lütfen bekleyin...")

        threading.Thread(
            target=self._run_analysis,
            args=(po_path, api_key, model),
            daemon=True,
        ).start()

    def _run_analysis(self, po_path, api_key, model):
        try:
            analyze_example_po(po_path, api_key, model)
            save_config({"api_key": api_key, "model": model, "template_ready": True})
            self.root.after(0, self._on_success)
        except Exception as exc:
            self.root.after(0, self._on_error, str(exc))

    def _on_success(self):
        self._status_var.set("Şablon başarıyla oluşturuldu!")
        messagebox.showinfo("Hazır", "Şablon oluşturuldu. Program hazır.")
        self.on_complete()

    def _on_error(self, message):
        self._btn.config(state="normal")
        self._status_var.set("Hata oluştu.")
        messagebox.showerror("Hata", "Şablon oluşturulamadı:\n" + message)
