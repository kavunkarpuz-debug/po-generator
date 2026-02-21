"""
First-run setup wizard. Supports multiple LLM providers (Claude, OpenAI, Gemini).
Allows selecting predefined models or manual entry.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading

from core.template_analyzer import analyze_example_po_to_html
from core.config import save_config

PROVIDERS = {
    "Anthropic": ["claude-3-5-sonnet-20241022", "claude-3-7-sonnet-20250219", "claude-3-opus-20240229"],
    "OpenAI": ["gpt-4o", "gpt-4o-mini", "o1-preview"],
    "Google (Gemini)": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.0-flash-exp"]
}


class SetupScreen:
    def __init__(self, root: tk.Tk, on_complete_callback):
        self.root = root
        self.on_complete = on_complete_callback
        self.root.title("PO Generator — Evrensel Şablon Kurulumu")
        self.root.resizable(False, False)
        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 12, "pady": 6}
        frame = ttk.Frame(self.root, padding=20)
        frame.grid(row=0, column=0, sticky="nsew")

        ttk.Label(frame, text="PO Generator — Evrensel Şablon Kurulumu", font=("Segoe UI", 13, "bold")).grid(
            row=0, column=0, columnspan=3, pady=(0, 16), sticky="w"
        )

        # 1. Example PO
        ttk.Label(frame, text="1. Örnek PO (PDF):").grid(row=1, column=0, sticky="w", **pad)
        self._po_path_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self._po_path_var, width=45).grid(row=1, column=1, **pad)
        ttk.Button(frame, text="Seç", command=self._browse_po).grid(row=1, column=2, **pad)

        # 2. Provider
        ttk.Label(frame, text="2. Servis Sağlayıcı:").grid(row=2, column=0, sticky="w", **pad)
        self._provider_var = tk.StringVar(value="Anthropic")
        self._provider_combo = ttk.Combobox(frame, textvariable=self._provider_var, values=list(PROVIDERS.keys()), state="readonly", width=42)
        self._provider_combo.grid(row=2, column=1, columnspan=2, sticky="w", **pad)
        self._provider_combo.bind("<<ComboboxSelected>>", self._on_provider_change)

        # 3. Model
        ttk.Label(frame, text="3. Model:").grid(row=3, column=0, sticky="w", **pad)
        self._model_var = tk.StringVar()
        self._model_combo = ttk.Combobox(frame, textvariable=self._model_var, width=42)
        self._model_combo.grid(row=3, column=1, columnspan=2, sticky="w", **pad)
        ttk.Label(frame, text="(Yüksek sadakat için Anthropic/Sonnet önerilir)", foreground="gray", font=("Segoe UI", 8)).grid(row=4, column=1, sticky="w", padx=12)

        # 4. API Key
        ttk.Label(frame, text="4. API Key:").grid(row=5, column=0, sticky="w", **pad)
        self._api_key_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self._api_key_var, width=45, show="*").grid(
            row=5, column=1, columnspan=2, sticky="ew", **pad
        )

        # Status
        self._status_var = tk.StringVar(value="")
        ttk.Label(frame, textvariable=self._status_var, foreground="gray").grid(
            row=6, column=0, columnspan=3, sticky="w", padx=12
        )

        self._btn = ttk.Button(frame, text="Evrensel Şablonu Oluştur", command=self._start_analysis)
        self._btn.grid(row=7, column=0, columnspan=3, pady=16)

        self._on_provider_change()

    def _on_provider_change(self, event=None):
        provider = self._provider_var.get()
        models = PROVIDERS.get(provider, [])
        self._model_combo["values"] = models
        if models:
            self._model_var.set(models[0])

    def _browse_po(self):
        path = filedialog.askopenfilename(title="Örnek PO seçin", filetypes=[("PDF files", "*.pdf")])
        if path: self._po_path_var.set(path)

    def _start_analysis(self):
        config = {
            "provider": self._provider_var.get().split(" ")[0].lower(),
            "model": self._model_var.get().strip(),
            "api_key": self._api_key_var.get().strip(),
            "template_ready": True,
            "use_docx": False # Switch back to High-Fidelity HTML
        }

        if not self._po_path_var.get() or not config["api_key"] or not config["model"]:
            messagebox.showerror("Hata", "Lütfen tüm alanları doldurun.")
            return

        self._btn.config(state="disabled")
        self._status_var.set("Şablon oluşturuluyor, lütfen bekleyin...")
        threading.Thread(target=self._run_analysis, args=(self._po_path_var.get(), config), daemon=True).start()

    def _run_analysis(self, po_path, config):
        try:
            analyze_example_po_to_html(po_path, config)
            save_config(config)
            self.root.after(0, self._on_success)
        except Exception as exc:
            self.root.after(0, self._on_error, str(exc))

    def _on_success(self):
        messagebox.showinfo("Başarılı", "Şablon oluşturuldu ve ayarlar kaydedildi.")
        self.on_complete()

    def _on_error(self, msg):
        self._btn.config(state="normal")
        self._status_var.set("Hata oluştu.")
        messagebox.showerror("Hata", msg)
