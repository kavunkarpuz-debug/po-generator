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
    # Claude omits a key entirely -- should still appear as None
    response = '{"vendor_name": "Acme", "total_price": "USD 100"}'
    result = parse_extraction_response(response, FIELDS)
    assert "delivery_term" in result
    assert result["delivery_term"] is None
