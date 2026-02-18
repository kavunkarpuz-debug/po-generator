"""
Renders a Jinja2 HTML template with given values and produces a PDF via weasyprint.
"""

import os
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


def generate_pdf(
    template_html: str,
    values: dict,
    output_path: str,
) -> None:
    """Fill template and write PDF to output_path."""
    from weasyprint import HTML  # lazy import: requires native GTK libs at runtime
    rendered_html = fill_template(template_html, values)
    HTML(string=rendered_html).write_pdf(output_path)


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
