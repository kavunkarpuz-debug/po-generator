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
