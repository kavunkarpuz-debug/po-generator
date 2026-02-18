"""Config file loading and saving."""

import os
import json

# Default paths — resolved relative to this file's parent (project root)
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CONFIG_PATH   = os.path.join(_ROOT, "config.json")
DEFAULT_TEMPLATE_PATH = os.path.join(_ROOT, "po_template.html")
DEFAULT_FIELDS_PATH   = os.path.join(_ROOT, "po_fields.json")


def load_config(config_path: str = DEFAULT_CONFIG_PATH) -> dict:
    """Return config dict, or empty dict if file doesn't exist."""
    if not os.path.exists(config_path):
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(data: dict, config_path: str = DEFAULT_CONFIG_PATH) -> None:
    """Write config dict to JSON file."""
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def is_setup_complete(
    config_path: str = DEFAULT_CONFIG_PATH,
    template_path: str = DEFAULT_TEMPLATE_PATH,
    fields_path: str = DEFAULT_FIELDS_PATH,
) -> bool:
    """Return True only if all three runtime files exist."""
    return (
        os.path.exists(config_path)
        and os.path.exists(template_path)
        and os.path.exists(fields_path)
    )
