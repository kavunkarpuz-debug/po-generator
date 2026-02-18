"""
Main screen: user uploads quotation -> AI extracts values -> ReviewScreen -> PDF.
"""

import os
import json
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from core.config import load_config, DEFAULT_TEMPLATE_PATH, DEFAULT_FIELDS_PATH
from core.quotation_extractor import extract_values
from core.pdf_generator import generate_pdf, get_po_number_and_date, build_output_path
from gui.review_screen import ReviewScreen


class GenerateScreen:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("PO Generator")
        self.root.resizable(False, False)
        self._config = load_config()
        with open(DEFAULT_FIELDS_PATH, "r", encoding="utf-8") as f:
            self._fields = json.load(f)["fields"]
        with open(DEFAULT_TEMPLATE_PATH, "r", encoding="utf-8") as f:
            self._template_html = f.read()
        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 12, "pady": 8}
        frame = ttk.Frame(self.root, padding=24)
        frame.grid(row=0, column=0, sticky="nsew")

        ttk.Label(frame, text="PO Generator", font=("Segoe UI", 13, "bold")).grid(
            row=0, column=0, columnspan=3, pady=(0, 16), sticky="w"
        )

        ttk.Label(frame, text="Teklif dosyasi (PDF/DOCX/XLSX):").grid(
            row=1, column=0, sticky="w", **pad
        )
        self._file_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self._file_var, width=48).grid(row=1, column=1, **pad)
        ttk.Button(frame, text="Sec", command=self._browse).grid(row=1, column=2, **pad)

        self._status_var = tk.StringVar(value="")
        ttk.Label(frame, textvariable=self._status_var, foreground="gray").grid(
            row=2, column=0, columnspan=3, sticky="w", padx=12
        )

        self._btn = ttk.Button(frame, text="Analiz Et", command=self._start_extraction)
        self._btn.grid(row=3, column=0, columnspan=3, pady=16)

    def _browse(self):
        path = filedialog.askopenfilename(
            title="Teklif dosyasi secin",
            filetypes=[
                ("Desteklenen dosyalar", "*.pdf *.docx *.xlsx *.xls"),
                ("PDF", "*.pdf"),
                ("Word", "*.docx"),
                ("Excel", "*.xlsx *.xls"),
            ],
        )
        if path:
            self._file_var.set(path)

    def _start_extraction(self):
        path = self._file_var.get().strip()
        if not path:
            messagebox.showerror("Hata", "Lutfen bir teklif dosyasi secin.")
            return
        self._btn.config(state="disabled")
        self._status_var.set("Teklif analiz ediliyor...")
        threading.Thread(
            target=self._run_extraction, args=(path,), daemon=True
        ).start()

    def _run_extraction(self, path):
        try:
            values = extract_values(
                path,
                self._fields,
                self._config["api_key"],
                self._config["model"],
            )
            self.root.after(0, self._open_review, path, values)
        except Exception as exc:
            self.root.after(0, self._on_error, str(exc))

    def _open_review(self, quotation_path, values):
        self._btn.config(state="normal")
        self._status_var.set("")

        # po_number is auto-generated at PDF creation time — pre-fill a placeholder
        # so the field shows ✅ in the review screen and doesn't block the button.
        if not values.get("po_number"):
            values["po_number"] = "(otomatik oluşturulacak)"

        review_win = tk.Toplevel(self.root)
        ReviewScreen(
            review_win,
            self._fields,
            values,
            on_confirm_callback=lambda final: self._generate_pdf(
                final, os.path.dirname(quotation_path), review_win
            ),
        )

    def _generate_pdf(self, final_values, output_dir, review_win):
        try:
            po_number, date_str, date_dotted = get_po_number_and_date(output_dir)
            final_values["po_number"] = f"{po_number}_{date_str}"
            for key in ("issue_date", "date", "po_date"):
                if key not in final_values or not final_values.get(key):
                    final_values[key] = date_dotted

            subject = final_values.get("subject", "PO")
            output_path = build_output_path(subject, po_number, date_str, output_dir)
            generate_pdf(self._template_html, final_values, output_path)
            review_win.destroy()
            messagebox.showinfo(
                "Tamamlandi",
                "PO olusturuldu:\n" + os.path.basename(output_path)
            )
        except Exception as exc:
            messagebox.showerror("Hata", "PDF olusturulamadi:\n" + str(exc))

    def _on_error(self, message):
        self._btn.config(state="normal")
        self._status_var.set("Hata olustu.")
        messagebox.showerror("Hata", "Teklif analiz edilemedi:\n" + message)
