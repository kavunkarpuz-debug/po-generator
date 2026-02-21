"""Config file loading and saving via .env (environment variables)."""

import os
from dotenv import load_dotenv, set_key

# Default paths
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_ENV_PATH           = os.path.join(_ROOT, ".env")
DEFAULT_TEMPLATE_PATH      = os.path.join(_ROOT, "po_template.html")
DEFAULT_DOCX_TEMPLATE_PATH = os.path.join(_ROOT, "po_template.docx")
DEFAULT_FIELDS_PATH        = os.path.join(_ROOT, "po_fields.json")

# Load existing environment variables from .env
if os.path.exists(DEFAULT_ENV_PATH):
    load_dotenv(DEFAULT_ENV_PATH)


def load_config() -> dict:
    """Return config dict from environment variables."""
    # Refresh from .env file to pick up changes made by save_config()
    if os.path.exists(DEFAULT_ENV_PATH):
        load_dotenv(DEFAULT_ENV_PATH, override=True)

    return {
        "provider": os.getenv("LLM_PROVIDER"),
        "api_key": os.getenv("LLM_API_KEY"),
        "model": os.getenv("LLM_MODEL"),
        "template_ready": os.getenv("TEMPLATE_READY") == "True",
        "use_docx": os.getenv("USE_DOCX") == "True"
    }


def save_config(data: dict) -> None:
    """Write config data to .env file."""
    if not os.path.exists(DEFAULT_ENV_PATH):
        open(DEFAULT_ENV_PATH, 'w').close() # Create file if not exists
    
    # Map friendly keys to ENV variable names
    mapping = {
        "provider": "LLM_PROVIDER",
        "api_key": "LLM_API_KEY",
        "model": "LLM_MODEL",
        "template_ready": "TEMPLATE_READY",
        "use_docx": "USE_DOCX"
    }
    
    for key, env_name in mapping.items():
        if key in data:
            # We convert to string as .env only stores strings
            val = str(data[key])
            set_key(DEFAULT_ENV_PATH, env_name, val)


def is_setup_complete(
    fields_path: str = DEFAULT_FIELDS_PATH,
) -> bool:
    """Return True if required env vars AND template/fields files exist."""
    conf = load_config()
    
    # Check for basic LLM config
    if not (conf["api_key"] and conf["model"] and conf["template_ready"]):
        return False
        
    # Check for actual template files
    has_template = (
        os.path.exists(DEFAULT_TEMPLATE_PATH) or 
        os.path.exists(DEFAULT_DOCX_TEMPLATE_PATH)
    )
    
    return has_template and os.path.exists(fields_path)
