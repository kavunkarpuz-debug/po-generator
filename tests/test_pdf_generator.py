# tests/test_pdf_generator.py
import pytest
import os
from core.pdf_generator import fill_template, build_output_path


def test_fill_template_substitutes_values():
    html = "<html><body><p>{{ supplier_company }}</p></body></html>"
    values = {"supplier_company": "Acme Co."}
    result = fill_template(html, values)
    assert "Acme Co." in result


def test_build_output_path_format(tmp_path):
    path = build_output_path(
        subject="Drill Pipe",
        po_number="550",
        date_str="21022026",
        output_dir=str(tmp_path),
    )
    assert path.endswith(".pdf")
    assert "550" in path
    assert "Drill Pipe" in path
    assert "21022026" in path


def test_build_output_path_truncates_long_subject(tmp_path):
    long_subject = "A" * 100
    path = build_output_path(
        subject=long_subject,
        po_number="551",
        date_str="21022026",
        output_dir=str(tmp_path),
    )
    # Ensure filename doesn't exceed reasonable limits
    filename = os.path.basename(path)
    assert len(filename) < 100
