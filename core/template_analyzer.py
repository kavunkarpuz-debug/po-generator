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

This PO belongs to a specific BUYER company. Distinguish between two kinds of information:

── STATIC (hardcode directly in the HTML — NO placeholders) ──────────────────
Everything that belongs to the buyer company itself and never changes:
  • Buyer company name, head office address, branch/regional office address
  • Phone, fax, e-mail, trade registry numbers, tax office & ID
  • Sender's full name, job title, mobile number, office address, office phone, website
  • Any fixed legal text, logos, or branding

── DYNAMIC (use {{ snake_case_name }} Jinja2 placeholders) ──────────────────
Only information that comes from the supplier's quotation or changes per order:
  • po_date         — date of this purchase order
  • po_number       — purchase order reference number
  • supplier_company — name of the vendor/supplier (TO field)
  • supplier_contact — attention/contact person at the supplier (ATTN field)
  • subject          — description of the items being ordered
  • delivery_time    — lead time (e.g. 90 to 120 Days)
  • payment_term     — payment terms (e.g. Net 30 Days)
  • delivery_term    — incoterm (e.g. EXW Odessa Texas)
  • total_price      — total quoted price (number only, no currency symbol)

Keep the dynamic field list as short as possible — roughly these 9 fields.

Generate an HTML/CSS template that visually matches the PO layout with all static
values hardcoded and only the 9 dynamic placeholders above.
The HTML must be self-contained (inline CSS), A4 size, print-ready, concise —
no HTML comments, no extra whitespace, minimal CSS.

Return your answer in EXACTLY this format — no other text outside the tags:

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
        max_tokens=16000,
        messages=[{"role": "user", "content": content}],
    )
    response_text = message.content[0].text
    if message.stop_reason == "max_tokens":
        raise RuntimeError(
            f"Claude response was truncated (max_tokens hit). "
            f"Response length: {len(response_text)} chars. "
            f"Try using claude-sonnet-4-6 which produces more concise output."
        )
    html, fields = parse_analyzer_response(response_text)

    with open(template_path, "w", encoding="utf-8") as f:
        f.write(html)
    with open(fields_path, "w", encoding="utf-8") as f:
        json.dump({"fields": fields}, f, indent=2, ensure_ascii=False)

    return fields
