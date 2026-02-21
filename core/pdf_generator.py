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
    """Fill template and write PDF using a multi-stage safety strategy for OneDrive."""
    import tempfile
    import time
    import logging
    import shutil
    
    rendered_html = fill_template(template_html, values)
    
    # 1. AGGRESSIVE OVERFLOW PREVENTION
    # Remove all min-height constraints that force 2nd pages
    rendered_html = rendered_html.replace("min-height:", "max-height:")
    
    # 2. INJECT CSS FOR SINGLE PAGE INTEGRITY
    css_injection = """
    <style>
        @page { size: A4; margin: 0 !important; }
        html, body { 
            margin: 0 !important; 
            padding: 0 !important; 
            overflow: hidden !important;
            height: auto !important;
            min-height: 0 !important;
            zoom: 0.98; /* Subtle shrink to guarantee fit */
        }
        .page-container, .page {
            margin: 0 auto !important;
            min-height: 0 !important;
            max-width: 100% !important;
        }
    </style>
    """
    if "</head>" in rendered_html:
        rendered_html = rendered_html.replace("</head>", f"{css_injection}</head>")
    else:
        rendered_html = css_injection + rendered_html

    # Use a unique subfolder in Temp for each run to avoid any conflicts
    import uuid
    temp_dir = os.path.join(tempfile.gettempdir(), f"po_gen_{uuid.uuid4().hex[:8]}")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
        
    tmp_html = os.path.join(temp_dir, "input.html")
    tmp_pdf = os.path.join(temp_dir, "output.pdf")
    
    try:
        with open(tmp_html, "w", encoding="utf-8") as f:
            f.write(rendered_html)

        edge = _find_edge()
        file_url = "file:///" + os.path.abspath(tmp_html).replace("\\", "/")

        # Execution with standard stable flags
        cmd = [
            edge,
            "--headless=old",
            "--no-sandbox",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={tmp_pdf}",
            file_url,
        ]
        
        subprocess.run(cmd, capture_output=True, text=True)
        
        # 2. WAIT FOR FILE: OneDrive/Edge can be slow. 
        # Wait up to 5 seconds for the file to exist AND have data inside.
        success = False
        for _ in range(10): # 10 x 0.5s = 5 seconds max
            if os.path.exists(tmp_pdf) and os.path.getsize(tmp_pdf) > 1000:
                success = True
                break
            time.sleep(0.5)

        if not success:
            raise RuntimeError("Edge PDF dosyasini olusturamadi veya dosya bos kaldi.")

        # 3. MOVE WITH RETRIES: OneDrive might lock the destination folder immediately.
        move_success = False
        for i in range(3):
            try:
                if os.path.exists(output_path):
                    os.remove(output_path)
                shutil.move(tmp_pdf, output_path)
                move_success = True
                break
            except Exception as e:
                logging.warning(f"Move attempt {i+1} failed (OneDrive lock?): {e}")
                time.sleep(1) # Wait for sync lock to release
        
        if not move_success:
            raise RuntimeError(f"PDF olusturuldu ama klasore tasinamadi: {output_path}")

    finally:
        # Cleanup
        for p in (tmp_html, tmp_pdf):
            if os.path.exists(p):
                try: os.remove(p)
                except: pass


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
