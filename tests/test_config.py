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
