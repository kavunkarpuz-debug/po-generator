"""
Extracts field values from a supplier quotation using Claude API.
Field names are driven by po_fields.json (dynamic, AI-determined).
"""

import re
import json
import anthropic
from core.utils import read_file_text, read_pdf_as_images


def _build_extraction_prompt(fields: list[dict], document_text: str) -> str:
    field_lines = "\n".join(
        f'- "{f["name"]}": {f["description"]}'  for f in fields
    )
    return (
        f"Extract the following fields from this supplier quotation document.\n\n"
        f"Return ONLY a valid JSON object with these exact keys:\n{field_lines}\n\n"
        f"Use null for any field that cannot be determined.\n\n"
        f"DOCUMENT CONTENT:\n{document_text}"
    )


def _build_vision_prompt(fields: list[dict]) -> str:
    field_lines = "\n".join(
        f'- "{f["name"]}": {f["description"]}'  for f in fields
    )
    return (
        f"Extract the following fields from this supplier quotation document image.\n\n"
        f"Return ONLY a valid JSON object with these exact keys:\n{field_lines}\n\n"
        f"Use null for any field that cannot be determined."
    )


def parse_extraction_response(response_text: str, fields: list[dict]) -> dict:
    """Parse Claude's JSON response. Returns dict with all field names as keys."""
    # Strip markdown code block if present
    json_match = re.search(r"\{[\s\S]*\}", response_text)
    if not json_match:
        raise ValueError(f"No JSON object found in response: {response_text[:300]}")
    data = json.loads(json_match.group())

    # Ensure every field is present, defaulting missing ones to None
    for field in fields:
        if field["name"] not in data:
            data[field["name"]] = None
    return data


def extract_values(
    quotation_path: str,
    fields: list[dict],
    api_key: str,
    model: str,
) -> dict:
    """
    Read quotation, call Claude API, return extracted values dict.
    Missing/unfound values are None.
    """
    client = anthropic.Anthropic(api_key=api_key)

    text = read_file_text(quotation_path)

    if text and len(text.strip()) > 50:
        prompt = _build_extraction_prompt(fields, text)
        message = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
    else:
        # Vision fallback for image-only PDFs
        images = read_pdf_as_images(quotation_path)
        content = images + [{"type": "text", "text": _build_vision_prompt(fields)}]
        message = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": content}],
        )

    return parse_extraction_response(message.content[0].text, fields)
