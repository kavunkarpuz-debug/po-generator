# PO Generator v2 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a self-configuring desktop PO generator that learns any company's PO format from one example PDF, then converts supplier quotations into correctly formatted PO PDFs via a GUI — no terminal required.

**Architecture:** tkinter GUI → core services → Claude API. First run: Claude Vision analyzes example PO → saves `po_template.html` (Jinja2) + `po_fields.json`. Every run: Claude API extracts values from quotation using field manifest → review screen → weasyprint renders HTML → PDF.

**Tech Stack:** Python 3.9+, tkinter (GUI), anthropic SDK, pdfplumber, pillow, python-docx, openpyxl, jinja2, weasyprint, pytest + unittest.mock (tests)

---

## Task 1: Project Scaffolding

**Files:**
- Create: `core/__init__.py`
- Create: `gui/__init__.py`
- Create: `tests/__init__.py`
- Create: `requirements.txt`
- Modify: `.gitignore`

**Step 1: Create package directories and empty `__init__.py` files**

```bash
mkdir core gui tests
type nul > core/__init__.py
type nul > gui/__init__.py
type nul > tests/__init__.py
```

**Step 2: Create `requirements.txt`**

```
anthropic
pdfplumber
pillow
python-docx
openpyxl
jinja2
weasyprint
pytest
```

**Step 3: Install dependencies**

```bash
pip install -r requirements.txt
```

If `weasyprint` fails on Windows, run: `pip install weasyprint` separately — newer versions (60+) bundle required native libs automatically.

**Step 4: Add generated files to `.gitignore`**

Append these lines to the existing `.gitignore`:

```
# v2 runtime files
config.json
po_template.html
po_fields.json
```

**Step 5: Commit**

```bash
git add core/__init__.py gui/__init__.py tests/__init__.py requirements.txt .gitignore
git commit -m "feat: scaffold v2 package structure and dependencies"
```

---

## Task 2: core/utils.py — Shared Utilities

**Files:**
- Create: `core/utils.py`
- Create: `tests/test_utils.py`

**Step 1: Write the failing tests**

```python
# tests/test_utils.py
import os
import pytest
from core.utils import get_next_po_number, read_file_text


def test_get_next_po_number_empty_list():
    assert get_next_po_number([]) == "001"


def test_get_next_po_number_finds_max():
    files = [
        "548_03012026 PO for Eckel Jaw Sets.pdf",
        "549_17022026 PO for Drill Pipe Equipment.pdf",
    ]
    assert get_next_po_number(files) == "550"


def test_get_next_po_number_ignores_non_numeric():
    files = ["some_file.pdf", "001_date PO for x.pdf"]
    assert get_next_po_number(files) == "002"


def test_get_next_po_number_pads_to_three_digits():
    files = ["009_01012026 PO for x.pdf"]
    assert get_next_po_number(files) == "010"
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_utils.py -v
```

Expected: `ImportError` or `ModuleNotFoundError` — `core.utils` doesn't exist yet.

**Step 3: Create `core/utils.py`**

```python
"""Shared utilities: file reading and PO numbering."""

import re
import io
import base64
import pdfplumber
from docx import Document
from openpyxl import load_workbook


def get_next_po_number(po_files: list[str]) -> str:
    """Return next 3-digit PO number based on existing PO filenames."""
    numbers = []
    for fname in po_files:
        match = re.match(r"(\d{3})", fname)
        if match:
            numbers.append(int(match.group(1)))
    return "001" if not numbers else f"{max(numbers) + 1:03d}"


def read_pdf_text(path: str) -> str:
    """Extract text from PDF using pdfplumber."""
    parts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                parts.append(text)
    return "\n".join(parts)


def read_pdf_as_images(path: str) -> list[dict]:
    """Convert each PDF page to a base64 PNG dict for Claude Vision."""
    images = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            buf = io.BytesIO()
            page.to_image(resolution=200).original.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
            images.append({
                "type": "image",
                "source": {"type": "base64", "media_type": "image/png", "data": b64},
            })
    return images


def read_docx_text(path: str) -> str:
    """Extract text from a Word document."""
    doc = Document(path)
    parts = []
    for para in doc.paragraphs:
        if para.text.strip():
            parts.append(para.text)
    for table in doc.tables:
        for row in table.rows:
            row_text = "\t".join(cell.text for cell in row.cells)
            if row_text.strip():
                parts.append(row_text)
    return "\n".join(parts)


def read_excel_text(path: str) -> str:
    """Extract text from an Excel workbook."""
    wb = load_workbook(path, data_only=True)
    parts = []
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        parts.append(f"--- Sheet: {sheet_name} ---")
        for row in ws.iter_rows(values_only=True):
            row_str = "\t".join(str(c) if c is not None else "" for c in row)
            if row_str.strip():
                parts.append(row_str)
    return "\n".join(parts)


def read_file_text(path: str) -> str:
    """Read quotation file text regardless of format."""
    ext = path.rsplit(".", 1)[-1].lower()
    if ext == "pdf":
        return read_pdf_text(path)
    elif ext == "docx":
        return read_docx_text(path)
    elif ext in ("xlsx", "xls"):
        return read_excel_text(path)
    raise ValueError(f"Unsupported file type: .{ext}")
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_utils.py -v
```

Expected: 4 PASSED

**Step 5: Commit**

```bash
git add core/utils.py tests/test_utils.py
git commit -m "feat: add shared utilities (file reading, PO numbering)"
```

---

## Task 3: core/config.py — Config Management

**Files:**
- Create: `core/config.py`
- Create: `tests/test_config.py`

**Step 1: Write the failing tests**

```python
# tests/test_config.py
import json
import pytest
from pathlib import Path
from core.config import load_config, save_config, is_setup_complete


def test_load_config_returns_empty_dict_when_missing(tmp_path):
    result = load_config(config_path=str(tmp_path / "config.json"))
    assert result == {}


def test_save_and_load_roundtrip(tmp_path):
    path = str(tmp_path / "config.json")
    data = {"api_key": "sk-test", "model": "claude-sonnet-4-6", "template_ready": False}
    save_config(data, config_path=path)
    loaded = load_config(config_path=path)
    assert loaded == data


def test_is_setup_complete_false_when_no_file(tmp_path):
    assert not is_setup_complete(
        config_path=str(tmp_path / "config.json"),
        template_path=str(tmp_path / "po_template.html"),
        fields_path=str(tmp_path / "po_fields.json"),
    )


def test_is_setup_complete_true_when_all_exist(tmp_path):
    cfg = tmp_path / "config.json"
    tpl = tmp_path / "po_template.html"
    fld = tmp_path / "po_fields.json"
    cfg.write_text(json.dumps({"template_ready": True}))
    tpl.write_text("<html></html>")
    fld.write_text(json.dumps({"fields": []}))
    assert is_setup_complete(
        config_path=str(cfg),
        template_path=str(tpl),
        fields_path=str(fld),
    )
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_config.py -v
```

Expected: `ImportError` — `core.config` doesn't exist yet.

**Step 3: Create `core/config.py`**

```python
"""Config file loading and saving."""

import os
import json

# Default paths — resolved relative to this file's parent (project root)
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CONFIG_PATH   = os.path.join(_ROOT, "config.json")
DEFAULT_TEMPLATE_PATH = os.path.join(_ROOT, "po_template.html")
DEFAULT_FIELDS_PATH   = os.path.join(_ROOT, "po_fields.json")


def load_config(config_path: str = DEFAULT_CONFIG_PATH) -> dict:
    """Return config dict, or empty dict if file doesn't exist."""
    if not os.path.exists(config_path):
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(data: dict, config_path: str = DEFAULT_CONFIG_PATH) -> None:
    """Write config dict to JSON file."""
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def is_setup_complete(
    config_path: str = DEFAULT_CONFIG_PATH,
    template_path: str = DEFAULT_TEMPLATE_PATH,
    fields_path: str = DEFAULT_FIELDS_PATH,
) -> bool:
    """Return True only if all three runtime files exist."""
    return (
        os.path.exists(config_path)
        and os.path.exists(template_path)
        and os.path.exists(fields_path)
    )
```

**Step 4: Run tests**

```bash
pytest tests/test_config.py -v
```

Expected: 4 PASSED

**Step 5: Commit**

```bash
git add core/config.py tests/test_config.py
git commit -m "feat: add config load/save and setup detection"
```

---

## Task 4: core/template_analyzer.py — Example PO → Template

**Files:**
- Create: `core/template_analyzer.py`
- Create: `tests/test_template_analyzer.py`

**Step 1: Write the failing tests**

```python
# tests/test_template_analyzer.py
import pytest
from core.template_analyzer import parse_analyzer_response


VALID_RESPONSE = """
<html_template>
<!DOCTYPE html>
<html>
<body>
<p>Supplier: {{ vendor_name }}</p>
<p>Date: {{ issue_date }}</p>
</body>
</html>
</html_template>
<field_manifest>
{
  "fields": [
    {"name": "vendor_name", "description": "Supplier company name"},
    {"name": "issue_date",  "description": "Issue date of the PO"}
  ]
}
</field_manifest>
"""


def test_parse_extracts_html():
    html, fields = parse_analyzer_response(VALID_RESPONSE)
    assert "{{ vendor_name }}" in html
    assert "{{ issue_date }}" in html


def test_parse_extracts_fields():
    html, fields = parse_analyzer_response(VALID_RESPONSE)
    names = [f["name"] for f in fields]
    assert "vendor_name" in names
    assert "issue_date" in names


def test_parse_raises_on_missing_html_template():
    with pytest.raises(ValueError, match="html_template"):
        parse_analyzer_response("<field_manifest>{}</field_manifest>")


def test_parse_raises_on_missing_field_manifest():
    with pytest.raises(ValueError, match="field_manifest"):
        parse_analyzer_response("<html_template><html></html></html_template>")
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_template_analyzer.py -v
```

Expected: `ImportError`

**Step 3: Create `core/template_analyzer.py`**

```python
"""
Analyzes an example PO PDF via Claude Vision and produces:
  - po_template.html  (Jinja2 HTML template)
  - po_fields.json    (field manifest)
"""

import re
import json
import anthropic
from core.utils import read_pdf_as_images
from core.config import DEFAULT_TEMPLATE_PATH, DEFAULT_FIELDS_PATH

ANALYZER_PROMPT = """\
You are analyzing a Purchase Order document to create a reusable template.

Look at this PO and do two things:

1. Identify every field that changes per order (PO number, date, supplier name,
   contact person, subject/description, delivery time, payment terms, delivery
   terms, total price, etc.). Give each a short snake_case name.

2. Generate an HTML/CSS template that visually matches this PO layout.
   Use {{ field_name }} Jinja2 placeholders wherever those fields appear.
   The HTML should be self-contained (inline CSS), A4 page size, print-ready.

Return your answer in EXACTLY this format — no other text outside the tags:

<html_template>
[complete HTML here]
</html_template>
<field_manifest>
{
  "fields": [
    {"name": "field_name", "description": "where/what this field is"},
    ...
  ]
}
</field_manifest>
"""


def parse_analyzer_response(response_text: str) -> tuple[str, list[dict]]:
    """Parse Claude's structured response into (html_str, fields_list)."""
    html_match = re.search(
        r"<html_template>([\s\S]*?)</html_template>", response_text
    )
    if not html_match:
        raise ValueError("Response missing <html_template> block")

    manifest_match = re.search(
        r"<field_manifest>([\s\S]*?)</field_manifest>", response_text
    )
    if not manifest_match:
        raise ValueError("Response missing <field_manifest> block")

    html = html_match.group(1).strip()
    manifest = json.loads(manifest_match.group(1).strip())
    return html, manifest["fields"]


def analyze_example_po(
    pdf_path: str,
    api_key: str,
    model: str,
    template_path: str = DEFAULT_TEMPLATE_PATH,
    fields_path: str = DEFAULT_FIELDS_PATH,
) -> list[dict]:
    """
    Send example PO pages to Claude Vision, save template and field manifest.
    Returns the list of field dicts from po_fields.json.
    """
    client = anthropic.Anthropic(api_key=api_key)
    images = read_pdf_as_images(pdf_path)

    content = images + [{"type": "text", "text": ANALYZER_PROMPT}]
    message = client.messages.create(
        model=model,
        max_tokens=4096,
        messages=[{"role": "user", "content": content}],
    )
    response_text = message.content[0].text
    html, fields = parse_analyzer_response(response_text)

    with open(template_path, "w", encoding="utf-8") as f:
        f.write(html)
    with open(fields_path, "w", encoding="utf-8") as f:
        json.dump({"fields": fields}, f, indent=2, ensure_ascii=False)

    return fields
```

**Step 4: Run tests**

```bash
pytest tests/test_template_analyzer.py -v
```

Expected: 4 PASSED (no API call needed — testing the pure parser only)

**Step 5: Commit**

```bash
git add core/template_analyzer.py tests/test_template_analyzer.py
git commit -m "feat: add template analyzer (Claude Vision → Jinja2 template + field manifest)"
```

---

## Task 5: core/quotation_extractor.py — Quotation → Values Dict

**Files:**
- Create: `core/quotation_extractor.py`
- Create: `tests/test_quotation_extractor.py`

**Step 1: Write the failing tests**

```python
# tests/test_quotation_extractor.py
import pytest
from core.quotation_extractor import parse_extraction_response


FIELDS = [
    {"name": "vendor_name",    "description": "Supplier company name"},
    {"name": "delivery_term",  "description": "Shipping terms"},
    {"name": "total_price",    "description": "Grand total with currency"},
]


def test_parse_found_values():
    response = '{"vendor_name": "Acme Co.", "delivery_term": "FOB", "total_price": "USD 5,000"}'
    result = parse_extraction_response(response, FIELDS)
    assert result["vendor_name"] == "Acme Co."
    assert result["delivery_term"] == "FOB"


def test_parse_missing_field_becomes_none():
    response = '{"vendor_name": "Acme Co.", "delivery_term": null, "total_price": "USD 5,000"}'
    result = parse_extraction_response(response, FIELDS)
    assert result["delivery_term"] is None


def test_parse_extracts_json_from_markdown_block():
    response = '```json\n{"vendor_name": "Acme", "delivery_term": null, "total_price": "100"}\n```'
    result = parse_extraction_response(response, FIELDS)
    assert result["vendor_name"] == "Acme"


def test_parse_adds_missing_keys_as_none():
    # Claude omits a key entirely — should still appear as None
    response = '{"vendor_name": "Acme", "total_price": "USD 100"}'
    result = parse_extraction_response(response, FIELDS)
    assert "delivery_term" in result
    assert result["delivery_term"] is None
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_quotation_extractor.py -v
```

Expected: `ImportError`

**Step 3: Create `core/quotation_extractor.py`**

```python
"""
Extracts field values from a supplier quotation using Claude API.
Field names are driven by po_fields.json (dynamic, AI-determined).
"""

import re
import json
import anthropic
from core.utils import read_file_text, read_pdf_as_images


def _build_extraction_prompt(fields: list[dict], document_text: str) -> str:
    field_lines = "\n".join(
        f'- "{f["name"]}": {f["description"]}' for f in fields
    )
    return (
        f"Extract the following fields from this supplier quotation document.\n\n"
        f"Return ONLY a valid JSON object with these exact keys:\n{field_lines}\n\n"
        f"Use null for any field that cannot be determined.\n\n"
        f"DOCUMENT CONTENT:\n{document_text}"
    )


def _build_vision_prompt(fields: list[dict]) -> str:
    field_lines = "\n".join(
        f'- "{f["name"]}": {f["description"]}' for f in fields
    )
    return (
        f"Extract the following fields from this supplier quotation document image.\n\n"
        f"Return ONLY a valid JSON object with these exact keys:\n{field_lines}\n\n"
        f"Use null for any field that cannot be determined."
    )


def parse_extraction_response(response_text: str, fields: list[dict]) -> dict:
    """Parse Claude's JSON response. Returns dict with all field names as keys."""
    # Strip markdown code block if present
    json_match = re.search(r"\{[\s\S]*\}", response_text)
    if not json_match:
        raise ValueError(f"No JSON object found in response: {response_text[:300]}")
    data = json.loads(json_match.group())

    # Ensure every field is present, defaulting missing ones to None
    for field in fields:
        if field["name"] not in data:
            data[field["name"]] = None
    return data


def extract_values(
    quotation_path: str,
    fields: list[dict],
    api_key: str,
    model: str,
) -> dict:
    """
    Read quotation, call Claude API, return extracted values dict.
    Missing/unfound values are None.
    """
    client = anthropic.Anthropic(api_key=api_key)

    text = read_file_text(quotation_path)

    if text and len(text.strip()) > 50:
        prompt = _build_extraction_prompt(fields, text)
        message = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
    else:
        # Vision fallback for image-only PDFs
        images = read_pdf_as_images(quotation_path)
        content = images + [{"type": "text", "text": _build_vision_prompt(fields)}]
        message = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": content}],
        )

    return parse_extraction_response(message.content[0].text, fields)
```

**Step 4: Run tests**

```bash
pytest tests/test_quotation_extractor.py -v
```

Expected: 4 PASSED

**Step 5: Commit**

```bash
git add core/quotation_extractor.py tests/test_quotation_extractor.py
git commit -m "feat: add quotation extractor (dynamic field extraction via Claude API)"
```

---

## Task 6: core/pdf_generator.py — HTML Template → PDF

**Files:**
- Create: `core/pdf_generator.py`
- Create: `tests/test_pdf_generator.py`

**Step 1: Write the failing tests**

```python
# tests/test_pdf_generator.py
import os
import pytest
from core.pdf_generator import fill_template, build_output_path


def test_fill_template_substitutes_values():
    html = "<html><body><p>{{ vendor_name }}</p><p>{{ issue_date }}</p></body></html>"
    values = {"vendor_name": "Acme Co.", "issue_date": "18.02.2026"}
    result = fill_template(html, values)
    assert "Acme Co." in result
    assert "18.02.2026" in result


def test_fill_template_missing_value_renders_empty():
    html = "<html><body>{{ vendor_name }} / {{ missing }}</body></html>"
    values = {"vendor_name": "Acme"}
    result = fill_template(html, values)
    assert "Acme" in result
    # Jinja2 undefined renders as empty string by default


def test_build_output_path_format(tmp_path):
    path = build_output_path(
        subject="Drill Pipe Equipment",
        po_number="550",
        date_str="18022026",
        output_dir=str(tmp_path),
    )
    assert path.endswith(".pdf")
    assert "550" in path
    assert "Drill Pipe Equipment" in path
    assert "18022026" in path
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_pdf_generator.py -v
```

Expected: `ImportError`

**Step 3: Create `core/pdf_generator.py`**

```python
"""
Renders a Jinja2 HTML template with given values and produces a PDF via weasyprint.
"""

import os
import datetime
from jinja2 import Environment, Undefined
from weasyprint import HTML


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
```

**Step 4: Run tests**

```bash
pytest tests/test_pdf_generator.py -v
```

Expected: 3 PASSED

**Step 5: Run all tests to make sure nothing is broken**

```bash
pytest tests/ -v
```

Expected: all PASSED

**Step 6: Commit**

```bash
git add core/pdf_generator.py tests/test_pdf_generator.py
git commit -m "feat: add PDF generator (Jinja2 template fill + weasyprint render)"
```

---

## Task 7: gui/setup_screen.py — First-Run Wizard

**Files:**
- Create: `gui/setup_screen.py`

No automated tests for tkinter screens. Manual smoke test described in step 4.

**Step 1: Create `gui/setup_screen.py`**

```python
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
        messagebox.showerror("Hata", f"Şablon oluşturulamadı:\n{message}")
```

**Step 2: Smoke test (manual)**

```python
# Run this in a Python shell to verify the window renders without errors:
import tkinter as tk
from gui.setup_screen import SetupScreen
root = tk.Tk()
app = SetupScreen(root, on_complete_callback=lambda: print("Setup complete"))
root.mainloop()
```

Expected: Window opens with all fields, "Şablonu Oluştur" button visible.

**Step 3: Commit**

```bash
git add gui/setup_screen.py
git commit -m "feat: add setup screen GUI (first-run wizard)"
```

---

## Task 8: gui/review_screen.py — Data Review & Manual Entry

**Files:**
- Create: `gui/review_screen.py`

**Step 1: Create `gui/review_screen.py`**

```python
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
```

**Step 2: Smoke test (manual)**

```python
import tkinter as tk
from gui.review_screen import ReviewScreen

fields = [
    {"name": "vendor_name",   "description": "Supplier"},
    {"name": "delivery_term", "description": "Delivery terms"},
    {"name": "total_price",   "description": "Total"},
]
values = {"vendor_name": "Acme Co.", "delivery_term": None, "total_price": "USD 5,000"}

root = tk.Tk()
ReviewScreen(root, fields, values, on_confirm_callback=lambda v: print("Confirmed:", v))
root.mainloop()
```

Expected: Window shows ✅ vendor_name (filled), ⚠️ delivery_term (empty, blocks button), ✅ total_price. Button activates after delivery_term is filled.

**Step 3: Commit**

```bash
git add gui/review_screen.py
git commit -m "feat: add review screen with missing-field validation and inline editing"
```

---

## Task 9: gui/generate_screen.py — Main Quotation Screen

**Files:**
- Create: `gui/generate_screen.py`

**Step 1: Create `gui/generate_screen.py`**

```python
"""
Main screen: user uploads quotation → AI extracts values → ReviewScreen → PDF.
"""

import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from core.config import load_config, DEFAULT_TEMPLATE_PATH, DEFAULT_FIELDS_PATH
from core.quotation_extractor import extract_values
from core.pdf_generator import generate_pdf, get_po_number_and_date, build_output_path
from gui.review_screen import ReviewScreen
import json


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

        ttk.Label(frame, text="Teklif dosyası (PDF/DOCX/XLSX):").grid(
            row=1, column=0, sticky="w", **pad
        )
        self._file_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self._file_var, width=48).grid(row=1, column=1, **pad)
        ttk.Button(frame, text="Seç", command=self._browse).grid(row=1, column=2, **pad)

        self._status_var = tk.StringVar(value="")
        ttk.Label(frame, textvariable=self._status_var, foreground="gray").grid(
            row=2, column=0, columnspan=3, sticky="w", padx=12
        )

        self._btn = ttk.Button(frame, text="Analiz Et", command=self._start_extraction)
        self._btn.grid(row=3, column=0, columnspan=3, pady=16)

    def _browse(self):
        path = filedialog.askopenfilename(
            title="Teklif dosyası seçin",
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
            messagebox.showerror("Hata", "Lütfen bir teklif dosyası seçin.")
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
            # Add date under whatever key the template uses for dates
            # (also inject common date key aliases for robustness)
            for key in ("issue_date", "date", "po_date"):
                if key not in final_values or not final_values.get(key):
                    final_values[key] = date_dotted

            subject = final_values.get("subject", "PO")
            output_path = build_output_path(subject, po_number, date_str, output_dir)
            generate_pdf(self._template_html, final_values, output_path)
            review_win.destroy()
            messagebox.showinfo(
                "Tamamlandı",
                f"PO oluşturuldu:\n{os.path.basename(output_path)}"
            )
        except Exception as exc:
            messagebox.showerror("Hata", f"PDF oluşturulamadı:\n{exc}")

    def _on_error(self, message):
        self._btn.config(state="normal")
        self._status_var.set("Hata oluştu.")
        messagebox.showerror("Hata", f"Teklif analiz edilemedi:\n{message}")
```

**Step 2: Smoke test (manual — requires config.json + template files from a real setup run)**

```python
import tkinter as tk
from gui.generate_screen import GenerateScreen
root = tk.Tk()
app = GenerateScreen(root)
root.mainloop()
```

Expected: Window opens, file picker works, "Analiz Et" button visible.

**Step 3: Commit**

```bash
git add gui/generate_screen.py
git commit -m "feat: add generate screen (quotation upload → extraction → review → PDF)"
```

---

## Task 10: main.py + Launcher

**Files:**
- Create: `main.py`
- Create: `main.pyw`

**Step 1: Create `main.py`**

```python
"""
Entry point for PO Generator v2.
- No config.json → SetupScreen (first-run wizard)
- Config + template exist → GenerateScreen (normal use)
"""

import tkinter as tk
from core.config import is_setup_complete
from gui.setup_screen import SetupScreen
from gui.generate_screen import GenerateScreen


def launch_generate(root: tk.Tk):
    """Replace window contents with GenerateScreen after setup."""
    for widget in root.winfo_children():
        widget.destroy()
    root.title("PO Generator")
    GenerateScreen(root)


def main():
    root = tk.Tk()
    root.withdraw()  # hide until screen is ready

    if is_setup_complete():
        root.deiconify()
        GenerateScreen(root)
    else:
        root.deiconify()
        SetupScreen(root, on_complete_callback=lambda: launch_generate(root))

    root.mainloop()


if __name__ == "__main__":
    main()
```

**Step 2: Create `main.pyw`**

`main.pyw` is identical to `main.py`. The `.pyw` extension tells Windows to run with `pythonw.exe` — no console window.

```
# main.pyw — identical content to main.py
```

Copy content from main.py exactly. The only difference is the file extension.

**Step 3: Create desktop shortcut (manual, one-time)**

In Windows Explorer:
1. Right-click `main.pyw` → "Send to" → "Desktop (create shortcut)"
2. Right-click the shortcut → Properties → Change Icon → browse for a `.ico` file if desired

Or run this once in PowerShell:

```powershell
$WScript = New-Object -ComObject WScript.Shell
$Shortcut = $WScript.CreateShortcut("$env:USERPROFILE\Desktop\PO Generator.lnk")
$Shortcut.TargetPath = "pythonw.exe"
$Shortcut.Arguments  = "main.pyw"
$Shortcut.WorkingDirectory = (Get-Location).Path
$Shortcut.Save()
```

**Step 4: End-to-end smoke test**

1. Delete `config.json`, `po_template.html`, `po_fields.json` if they exist
2. Double-click `main.pyw` (or run `pythonw main.py`)
3. Setup screen appears → fill in a real example PO PDF, API key, model → click "Şablonu Oluştur"
4. After success, GenerateScreen appears
5. Upload a supplier quotation → click "Analiz Et"
6. Review screen shows extracted data → fill any missing fields → click "PO Oluştur"
7. Verify PDF appears in the same folder as the quotation

**Step 5: Run full test suite one final time**

```bash
pytest tests/ -v
```

Expected: all PASSED

**Step 6: Final commit**

```bash
git add main.py main.pyw
git commit -m "feat: add main entry point and no-console launcher (main.pyw)"
```

---

## Summary of Files Created

| File | Purpose |
|---|---|
| `core/utils.py` | File reading, PO numbering |
| `core/config.py` | Config load/save/check |
| `core/template_analyzer.py` | Claude Vision → HTML template + field manifest |
| `core/quotation_extractor.py` | Claude API → values dict |
| `core/pdf_generator.py` | Jinja2 fill + weasyprint → PDF |
| `gui/setup_screen.py` | First-run wizard |
| `gui/review_screen.py` | Data review + manual entry |
| `gui/generate_screen.py` | Main quotation screen |
| `main.py` | Entry point |
| `main.pyw` | No-console launcher |
| `requirements.txt` | Dependencies |
| `tests/test_utils.py` | PO numbering tests |
| `tests/test_config.py` | Config roundtrip tests |
| `tests/test_template_analyzer.py` | Response parser tests |
| `tests/test_quotation_extractor.py` | Extraction parser tests |
| `tests/test_pdf_generator.py` | Template fill tests |
