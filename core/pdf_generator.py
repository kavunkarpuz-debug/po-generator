"""
Renders a Jinja2 HTML template with given values and produces a PDF via Edge headless.
Requires Microsoft Edge (always installed on Windows 10/11) — no extra dependencies.
"""

import os
import subprocess
import tempfile
import datetime
from jinja2 import Environment, Undefined


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
    filename = f"{po_number}_{date_str} PO for {subject}.pdf"
    return os.path.join(output_dir, filename)


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

    tmp_fd, tmp_html = tempfile.mkstemp(suffix=".html")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            f.write(rendered_html)

        edge = _find_edge()
        file_url = "file:///" + tmp_html.replace("\\", "/")

        subprocess.run(
            [
                edge,
                "--headless=old",       # legacy mode: --print-to-pdf-no-header works correctly
                "--disable-gpu",
                "--run-all-compositor-stages-before-draw",
                "--print-to-pdf-no-header",
                "--paper-width=8.27",   # A4 width in inches
                "--paper-height=11.69", # A4 height in inches
                f"--print-to-pdf={output_path}",
                file_url,
            ],
            check=True,
            capture_output=True,
        )
    finally:
        try:
            os.unlink(tmp_html)
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
