"""
Analyzes an example PO PDF via Claude Vision and produces:
  - po_template.html  (Jinja2 HTML template)
  - po_fields.json    (field manifest)
"""

import re
import json
import anthropic
from core.utils import read_pdf_as_images
from core.config import DEFAULT_TEMPLATE_PATH, DEFAULT_FIELDS_PATH

ANALYZER_PROMPT = """You are analyzing a Purchase Order document to create a reusable template.

Look at this PO and do two things:

1. Identify every field that changes per order (PO number, date, supplier name,
   contact person, subject/description, delivery time, payment terms, delivery
   terms, total price, etc.). Give each a short snake_case name.

2. Generate an HTML/CSS template that visually matches this PO layout.
   Use {{ field_name }} Jinja2 placeholders wherever those fields appear.
   The HTML should be self-contained (inline CSS), A4 page size, print-ready.

Return your answer in EXACTLY this format -- no other text outside the tags:

<html_template>
[complete HTML here]
</html_template>
<field_manifest>
{
  "fields": [
    {"name": "field_name", "description": "where/what this field is"},
    ...
  ]
}
</field_manifest>
"""


def parse_analyzer_response(response_text: str) -> tuple[str, list[dict]]:
    """Parse Claude's structured response into (html_str, fields_list).

    Tries multiple tag-name variations for robustness against response format drift.
    """
    html_match = re.search(
        r"<html_template>([\s\S]*?)</html_template>", response_text
    )
    if not html_match:
        raise ValueError(
            "Response missing <html_template> block.\n"
            f"Response preview: {response_text[:300]}"
        )

    # Try primary tag, then common Claude alternatives
    manifest_match = (
        re.search(r"<field_manifest>([\s\S]*?)</field_manifest>", response_text)
        or re.search(r"<field_list>([\s\S]*?)</field_list>", response_text)
        or re.search(r"<fields>([\s\S]*?)</fields>", response_text)
        or re.search(r"<manifest>([\s\S]*?)</manifest>", response_text)
    )

    if manifest_match:
        manifest_json = manifest_match.group(1).strip()
    else:
        # Last resort: find a bare JSON object containing a "fields" array
        bare_json = re.search(r'\{\s*"fields"\s*:\s*\[[\s\S]*?\]\s*\}', response_text)
        if not bare_json:
            raise ValueError(
                "Response missing <field_manifest> block.\n"
                f"Response preview: {response_text[:300]}"
            )
        manifest_json = bare_json.group()

    html = html_match.group(1).strip()
    manifest = json.loads(manifest_json)
    return html, manifest["fields"]


def analyze_example_po(
    pdf_path: str,
    api_key: str,
    model: str,
    template_path: str = DEFAULT_TEMPLATE_PATH,
    fields_path: str = DEFAULT_FIELDS_PATH,
) -> list[dict]:
    """
    Send example PO pages to Claude Vision, save template and field manifest.
    Returns the list of field dicts from po_fields.json.
    """
    client = anthropic.Anthropic(api_key=api_key)
    images = read_pdf_as_images(pdf_path)

    content = images + [{"type": "text", "text": ANALYZER_PROMPT}]
    message = client.messages.create(
        model=model,
        max_tokens=8192,
        messages=[{"role": "user", "content": content}],
    )
    response_text = message.content[0].text
    html, fields = parse_analyzer_response(response_text)

    with open(template_path, "w", encoding="utf-8") as f:
        f.write(html)
    with open(fields_path, "w", encoding="utf-8") as f:
        json.dump({"fields": fields}, f, indent=2, ensure_ascii=False)

    return fields
