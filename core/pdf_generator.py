"""
Renders a Jinja2 HTML template with given values and produces a PDF via Edge headless.
Requires Microsoft Edge (always installed on Windows 10/11) — no extra dependencies.
"""

import os
import shutil
import subprocess
import tempfile
import datetime
from jinja2 import Environment, Undefined
from pypdf import PdfReader, PdfWriter


def fill_template(template_html: str, values: dict) -> str:
    """Render Jinja2 template string with values. Undefined vars render as empty."""
    env = Environment(undefined=Undefined)
    return env.from_string(template_html).render(**values)


def build_output_path(
    subject: str,
    po_number: str,
    date_str: str,
    output_dir: str,
) -> str:
    """Return full path for the output PDF: NNN_DDMMYYYY PO for {subject}.pdf"""
    # Truncate subject so the full path stays well under Windows MAX_PATH (260)
    subject_safe = subject[:60] if len(subject) > 60 else subject
    filename = f"{po_number}_{date_str} PO for {subject_safe}.pdf"
    return os.path.join(output_dir, filename)


def merge_pdfs(po_pdf_path: str, quotation_path: str, output_path: str) -> bool:
    """
    Append the original quotation to the end of the PO.
    Only works if quotation is a PDF. Returns True if merged, False otherwise.
    """
    if not quotation_path.lower().endswith(".pdf"):
        return False

    try:
        writer = PdfWriter()
        
        # Keep files open while writing
        with open(po_pdf_path, "rb") as f1, open(quotation_path, "rb") as f2:
            reader1 = PdfReader(f1)
            for page in reader1.pages:
                writer.add_page(page)
            
            reader2 = PdfReader(f2)
            for page in reader2.pages:
                writer.add_page(page)
            
            # Save merged to a temp file first, then overwrite
            tmp_merged = tempfile.mktemp(suffix=".pdf")
            with open(tmp_merged, "wb") as out_f:
                writer.write(out_f)
        
        shutil.move(tmp_merged, output_path)
        return True
    except Exception as exc:
        print(f"PDF birleştirme hatası: {exc}")
        # Re-raise so the GUI shows the error
        raise exc


def _find_edge() -> str:
    """Return path to msedge.exe; raise RuntimeError if not found."""
    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    raise RuntimeError(
        "Microsoft Edge bulunamadı. Edge'in yüklü olduğundan emin olun."
    )


def generate_pdf(
    template_html: str,
    values: dict,
    output_path: str,
) -> None:
    """Fill template and write PDF to output_path using Edge headless."""
    rendered_html = fill_template(template_html, values)
    
    # Force single page and prevent overflow spillovers
    # 1. Remove min-height constraints which often cause a blank 2nd page on A4
    rendered_html = rendered_html.replace("min-height:", "max-height:")
    
    # 2. Inject CSS to force no headers/footers and zero margins
    css_injection = " @page { margin: 0; } body { margin: 0; padding: 0; } "
    if "<style>" in rendered_html:
        rendered_html = rendered_html.replace("<style>", f"<style>{css_injection}")
    else:
        rendered_html = rendered_html.replace("</head>", f"<style>{css_injection}</style></head>")

    tmp_html_fd, tmp_html = tempfile.mkstemp(suffix=".html")
    tmp_pdf = tempfile.mktemp(suffix=".pdf")
    try:
        with os.fdopen(tmp_html_fd, "w", encoding="utf-8") as f:
            f.write(rendered_html)

        edge = _find_edge()
        file_url = "file:///" + tmp_html.replace("\\", "/")

        # Use newer headless mode and explicit no-header flag
        subprocess.run(
            [
                edge,
                "--headless",
                "--disable-gpu",
                "--no-pdf-header-footer",
                f"--print-to-pdf={tmp_pdf}",
                file_url,
            ],
            check=True,
            capture_output=True,
        )

        if not os.path.exists(tmp_pdf):
            raise RuntimeError(
                "Edge PDF oluşturamadı — geçici dosya bulunamadı."
            )

        # Move from ASCII temp path to the actual (possibly non-ASCII) destination
        shutil.move(tmp_pdf, output_path)

    finally:
        for p in (tmp_html, tmp_pdf):
            try:
                os.unlink(p)
            except OSError:
                pass


def get_po_number_and_date(output_dir: str) -> tuple[str, str, str]:
    """
    Scan output_dir for existing PO files, return (po_number, date_ddmmyyyy, date_dotted).
    """
    from core.utils import get_next_po_number
    existing = [
        f for f in os.listdir(output_dir)
        if "po" in f.lower() and f.lower().endswith(".pdf")
    ]
    po_number = get_next_po_number(existing)
    today = datetime.date.today()
    return po_number, today.strftime("%d%m%Y"), today.strftime("%d.%m.%Y")
