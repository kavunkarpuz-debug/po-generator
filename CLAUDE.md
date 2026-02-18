# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Script

```bash
# Run from the repository root (requires quotation file to be present)
python po_generator.py
```

**Prerequisites:**
- `ANTHROPIC_API_KEY` environment variable must be set
- Microsoft Word must be installed (used by `docx2pdf` via COM automation for PDF conversion)
- `PO_TEMPLATE.docx` must exist in the same directory

**Install dependencies:**
```bash
pip install anthropic python-docx pypdf pdfplumber openpyxl docx2pdf
```

## Architecture

Single-script automation (`po_generator.py`) that runs a 7-step pipeline:

1. **File detection** — Scans the working directory. Files with "PO" in their name are treated as existing POs; all other valid files (PDF/DOCX/XLSX) are treated as the quotation. Exactly one quotation file must be present.

2. **PO numbering** — Reads 3-digit numeric prefixes from existing PO filenames and increments the highest by 1 (e.g., `548_...` → `549`).

3. **Data extraction via Claude API** — Extracts 7 fields from the quotation: `supplier_company`, `supplier_contact`, `subject`, `delivery_time`, `payment_term`, `delivery_term`, `total_price`. Uses text mode first; falls back to Vision API if PDF text extraction yields fewer than 50 characters. Uses model `claude-sonnet-4-20250514`.

4. **Template filling** — Replaces `{{PLACEHOLDER}}` tokens in `PO_TEMPLATE.docx`. The replacement logic handles placeholders split across multiple Word runs (the "slow path" in `replace_placeholder_in_runs`).

5. **PDF generation** — Converts the filled `.docx` to PDF via `docx2pdf` (requires MS Word).

6. **PDF merging** — Appends the quotation (converted to PDF if needed) after the PO cover letter using `pypdf`.

7. **Output** — Two files named `{NNN}_{DDMMYYYY} PO for {subject}.docx/.pdf`.

## Template Placeholders

| Placeholder | Value |
|---|---|
| `{{DATE}}` | Today in DD.MM.YYYY |
| `{{SUPPLIER}}` | Supplier company name |
| `{{ATTN}}` | Supplier contact person |
| `{{PO_NO}}` | `{NNN}_{DDMMYYYY}` |
| `{{SUBJECT}}` | 3-5 word item description |
| `{{DELIVERY_TIME}}` | Delivery period |
| `{{PAYMENT_TERM}}` | Payment terms |
| `{{DELIVERY_TERM}}` | Shipping/delivery terms |
| `{{TOTAL_PRICE}}` | Grand total with currency |

## Key Constraints

- Only one quotation file may exist in the directory at a time (script exits with error otherwise)
- Excel-to-PDF conversion uses `win32com` (Excel COM automation); failure is non-fatal — the merged PDF will contain only the PO cover letter
- Claude API extraction retries once on failure, then falls back to manual `input()` prompts
- Temp files prefixed with `_temp_` are cleaned up automatically after the run
