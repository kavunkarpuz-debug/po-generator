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
