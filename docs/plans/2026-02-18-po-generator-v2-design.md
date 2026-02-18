# PO Generator v2 — Design Document

**Date:** 2026-02-18
**Status:** Approved

## Problem

The current `po_generator.py` uses a single fixed Word template with hardcoded placeholders. This makes it impossible to distribute to other companies whose PO formats differ completely in layout, field names, and structure.

## Goal

A self-configuring PO generator that:
1. Learns any company's PO format from a single example PDF (one-time setup)
2. Processes incoming supplier quotations (any format) and produces a correctly formatted PO PDF
3. Runs as a normal desktop application — no terminal, no command line

## Architecture

```
po_generator/
├── main.py                    ← Entry point: checks config → routes to setup or generate
├── config.json                ← API key, model selection (gitignored)
├── po_template.html           ← Jinja2 HTML template (AI-generated, gitignored)
├── po_fields.json             ← Field manifest (AI-determined variable list, gitignored)
├── gui/
│   ├── setup_screen.py        ← First-run wizard
│   ├── review_screen.py       ← Data review + manual entry before PDF generation
│   └── generate_screen.py     ← Main quotation upload screen
└── core/
    ├── template_analyzer.py   ← Claude Vision: example PO → HTML template + field manifest
    ├── quotation_extractor.py ← Claude API: quotation file → extracted values dict
    └── pdf_generator.py       ← Jinja2 fill HTML template → weasyprint → PDF output
```

## Data Structures

### config.json
```json
{
  "api_key": "sk-ant-...",
  "model": "claude-sonnet-4-6",
  "template_ready": true
}
```

### po_fields.json (AI-generated, fully dynamic)
```json
{
  "fields": [
    {"name": "po_number",      "description": "PO reference number, top right"},
    {"name": "issue_date",     "description": "Issue date of the PO"},
    {"name": "vendor_name",    "description": "Supplier company name"},
    {"name": "vendor_contact", "description": "Contact person at supplier"},
    {"name": "subject",        "description": "Brief description of goods/services"},
    {"name": "delivery_time",  "description": "Delivery period or deadline"},
    {"name": "payment_term",   "description": "Payment terms"},
    {"name": "delivery_term",  "description": "Shipping/Incoterms"},
    {"name": "total_price",    "description": "Grand total including currency"}
  ]
}
```
Field names and descriptions are entirely determined by AI from the example PO. The list above is illustrative only.

### po_template.html (AI-generated)
A Jinja2 HTML template with `{{ field_name }}` placeholders matching the names in `po_fields.json`. Visually replicates the layout of the example PO.

## Workflows

### Setup (runs once)

```
User provides:
  - Example PO (PDF)
  - API key
  - Model selection

→ main.py detects no config.json → opens setup_screen.py
→ User fills form, clicks "Şablonu Oluştur"
→ template_analyzer.py:
    - Converts each PDF page to PNG (pdfplumber + Pillow)
    - Sends images to Claude Vision with prompt:
      "Analyze this PO document. Identify all variable fields
       (fields that change per order). Generate:
       1. An HTML/CSS template that visually matches this PO,
          using {{ field_name }} Jinja2 placeholders
       2. A JSON field manifest listing each placeholder with
          its name and description"
    - Parses response → saves po_template.html + po_fields.json
→ Saves config.json
→ Transitions to generate_screen.py
```

### Generation (every use)

```
→ main.py detects config.json with template_ready: true → opens generate_screen.py
→ User uploads quotation file (PDF / DOCX / XLSX), clicks "Analiz Et"
→ quotation_extractor.py:
    - Reads quotation content (text mode; Vision fallback for image-only PDFs)
    - Sends to Claude API with po_fields.json as context:
      "Extract values for these fields from the quotation: [field list]
       Return JSON. Use null for fields not found."
    - Returns dict: {"vendor_name": "Acme Co.", "delivery_term": null, ...}
→ review_screen.py opens:
    - All fields shown as editable text inputs
    - Fields with null value marked with ⚠️ warning label
    - "PO Oluştur" button disabled until all ⚠️ fields are filled
→ User fills missing fields, optionally corrects others, clicks "PO Oluştur"
→ pdf_generator.py:
    - Auto-generates po_number (NNN_DDMMYYYY, incremented from existing files)
    - Renders po_template.html with Jinja2 using final field values
    - Converts HTML → PDF via weasyprint
    - Saves to same folder as quotation: NNN_DDMMYYYY PO for {subject}.pdf
→ Success dialog shown
```

## AI Calls Summary

| Step | When | Input | Output |
|---|---|---|---|
| `template_analyzer` | Setup (once) | Example PO pages as images | `po_template.html` + `po_fields.json` |
| `quotation_extractor` | Every generation | Quotation text + field manifest | Values dict (JSON) |

No agents, no tool use, no multi-step loops. Both are single API calls.

## Review Screen Behavior

- Every extracted field is editable (AI may make mistakes)
- Missing fields (null) shown with ⚠️ label and empty input box
- "PO Oluştur" button is disabled while any ⚠️ field remains empty
- User can leave a field empty only if they explicitly clear a ✅ field (no null enforcement on already-found fields)

## Launcher

- **Development:** `pythonw main.py` via desktop shortcut (no console window)
- **Distribution:** PyInstaller → single `.exe` with embedded icon

## Dependencies

```
anthropic
pdfplumber
pillow
python-docx
openpyxl
jinja2
weasyprint
```

No `docx2pdf` — eliminates the Microsoft Word requirement entirely.

## Out of Scope (v2)

- Line items / multi-row tables in PO (total price only)
- Outlook / email integration
- Approval workflow
- Template editing UI
