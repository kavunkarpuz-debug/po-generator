"""
Analyzes an example PO PDF via Claude Vision and produces:
  - po_template.html  (Jinja2 HTML template)
  - po_fields.json    (field manifest)
"""

import re
import io
import json
import base64
import anthropic
import pdfplumber
from core.utils import read_pdf_as_images
from core.config import DEFAULT_TEMPLATE_PATH, DEFAULT_FIELDS_PATH

ANALYZER_PROMPT = """You are analyzing a Purchase Order document to create a reusable template.

This PO belongs to a specific BUYER company. Distinguish between two kinds of information:

── STATIC (hardcode directly in the HTML — NO placeholders) ──────────────────
Everything that belongs to the buyer company itself and never changes:
  • Buyer company name, head office address, branch/regional office address
  • Phone, fax, e-mail, trade registry numbers, tax office & ID
  • Sender's full name, job title, mobile number, office address, office phone, website
  • Any fixed legal text or branding text

── COMPANY LOGO (graphical image) ───────────────────────────────────────────
If the company has a GRAPHICAL logo or emblem (a real image, not just styled text):
  • In the HTML, write exactly: <img src="{{ __logo__ }}" style="width:NNpx;">
    where NN is an appropriate pixel width for that logo's size in the layout.
  • In the field_manifest, add ONE special entry:
    {"name": "__logo_bbox__", "description": "x1,y1,x2,y2"}
    where x1,y1,x2,y2 are the logo's bounding box as decimal fractions (0.0–1.0)
    of the PAGE width and height (not the visible content area).
    Example: if the logo occupies the centre third of the page width and the top 13%
    of the page height, write "0.33,0.0,0.67,0.13".
  • Use the __logo__ placeholder EVERY place the same graphical logo appears
    (e.g. once in the header, once in the signature area).
If the company has NO distinct graphical logo, omit __logo__ and __logo_bbox__ entirely.

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


def _embed_logo(html: str, fields: list[dict], pdf_path: str) -> tuple[str, list[dict]]:
    """
    If Claude identified a logo, extract it from the PDF and embed as base64.
    Returns updated (html, fields) with __logo_bbox__ removed from fields.
    """
    logo_field = next((f for f in fields if f["name"] == "__logo_bbox__"), None)
    if not logo_field:
        return html, fields

    # Remove the special bbox field from the user-visible list
    fields = [f for f in fields if f["name"] != "__logo_bbox__"]

    if "{{ __logo__ }}" not in html:
        return html, fields

    try:
        parts = [float(v.strip()) for v in logo_field["description"].split(",")]
        x1_pct, y1_pct, x2_pct, y2_pct = parts

        with pdfplumber.open(pdf_path) as pdf:
            page_img = pdf.pages[0].to_image(resolution=200).original

        w, h = page_img.size
        crop = page_img.crop((
            int(w * x1_pct), int(h * y1_pct),
            int(w * x2_pct), int(h * y2_pct),
        ))

        buf = io.BytesIO()
        crop.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()

        html = html.replace("{{ __logo__ }}", f"data:image/png;base64,{b64}")
    except Exception as exc:
        # Logo extraction failed — remove broken placeholder gracefully
        html = html.replace('src="{{ __logo__ }}"', 'src=""')

    return html, fields


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

    # Automatically extract and embed any graphical logo Claude identified
    html, fields = _embed_logo(html, fields, pdf_path)

    with open(template_path, "w", encoding="utf-8") as f:
        f.write(html)
    with open(fields_path, "w", encoding="utf-8") as f:
        json.dump({"fields": fields}, f, indent=2, ensure_ascii=False)

    return fields
