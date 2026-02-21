# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) or other LLMs when working with code in this repository.

## Running the Application

```bash
# Run the GUI application (main.py for console, main.pyw for no-console)
python main.py
```

**Prerequisites:**
- API keys (Anthropic, OpenAI, or Google Gemini) must be set in the `.env` file or via the Setup Screen.
- Microsoft Edge must be installed (used for headless PDF generation via `core/pdf_generator.py`).

**Install dependencies:**
```bash
pip install anthropic openai google-generativeai python-dotenv pdfplumber pillow python-docx openpyxl jinja2 pypdf
```

## Architecture (V2)

The application uses a **Modular Desktop Automation** approach:

1. **Configuration Manager (`core/config.py`):** Loads/saves settings from `.env`. Automatically detects if first-run setup is required.

2. **Template Analyzer (`core/template_analyzer.py`):** Uses LLM Vision to analyze a 1-page example PO PDF. It generates a high-fidelity HTML/CSS template (`po_template.html`) using **HTML TABLES** for layout stability and a dynamic field manifest (`po_fields.json`).

3. **Quotation Extractor (`core/quotation_extractor.py`):** Uses LLM API to extract dynamic data from any supplier quotation (PDF/DOCX/XLSX) based on the current field manifest. Supports vision fallback for image-only PDFs.

4. **PDF Generator (`core/pdf_generator.py`):** Renders the Jinja2 HTML template with extracted values and produces a PDF using **Microsoft Edge headless** mode. Automatically strips `min-height` and forces zero margins to prevent blank page overflows.

5. **PDF Merger (`core/pdf_generator.py`):** Appends the original quotation (if PDF) to the generated PO cover letter.

6. **GUI Layer (`gui/`):** Tkinter-based workflow: Setup Screen -> Generate Screen -> Review Screen (for manual edits).

## Development Guidelines

- **HTML Templates:** Always prefer HTML tables for layout. Avoid Flexbox/Grid to prevent shifting during Edge's headless print-to-pdf.
- **Single Page Integrity:** Injected CSS `@page { margin: 0; }` and programmatic `min-height` replacement with `max-height` are essential for preventing blank page spillovers.
- **LLM Independence:** Use `core/llm_provider.py` for all AI calls to maintain multi-provider support.
- **No Console Mode:** When using `pythonw`, ensure stdout/stderr are redirected to avoid crashes during library operations (e.g., `docx2pdf` or `tqdm`).

## Runtime Files

| File | Purpose |
|---|---|
| `.env` | API keys, model selection, setup state (TEMPLATE_READY=True). |
| `po_template.html` | The AI-generated high-fidelity HTML layout. |
| `po_fields.json` | Manifest of dynamic fields detected in the PO. |
