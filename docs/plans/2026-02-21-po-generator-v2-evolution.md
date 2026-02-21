# PO Generator v2 — Evolution Log (HTML & Multi-LLM)

**Date:** 2026-02-21
**Status:** Implemented

## Evolution from Word to HTML

During implementation, it was discovered that converting PDF to Word and then back to PDF introduced layout shifts, font issues, and inconsistent spacing, especially with complex company headers. 

### Key Shifts:
1.  **Engine Change:** Moved from `docx2pdf`/`pdf2docx` to **Microsoft Edge Headless PDF Generation**. 
    - This eliminated the need for Microsoft Word installation.
    - Achieved pixel-perfect reproduction of company layouts.
2.  **Stability:** Mandated the use of **HTML Tables** in the generated templates to prevent layout shifting during PDF rendering.
3.  **Efficiency:** Optimized `template_analyzer.py` to only process the first page of example POs, preventing quotations from leaking into the template.
4.  **Multi-LLM Provider:** Introduced `core/llm_provider.py` to support Anthropic, OpenAI, and Google Gemini models.
5.  **Spillover Prevention:** Implemented automatic `min-height` replacement with `max-height` and forced `@page` margins to prevent empty second-page spillovers.

## Known Challenges & Fixes

- **No Console Mode (`pythonw`):** Fixed a crash where libraries (like `docx2pdf`) would fail when trying to write to `sys.stdout` or `sys.stderr` when they are `None`.
- **File Access:** Corrected a `NoneType` write error by ensuring PDF file handles remain open throughout the entire `PdfWriter.write()` process.
