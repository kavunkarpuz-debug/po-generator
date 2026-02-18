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
