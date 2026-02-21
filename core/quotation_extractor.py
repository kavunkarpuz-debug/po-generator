"""
Extracts field values from a supplier quotation using LLMProvider.
"""

import re
import json
from core.llm_provider import LLMProvider
from core.utils import read_file_text, read_pdf_as_images_base64


def _build_extraction_prompt(fields: list[dict], document_text: str = "") -> str:
    field_lines = "\n".join(
        f'- "{f["name"]}": {f["description"]}'  for f in fields
    )
    prompt = (
        f"Extract the following fields from this supplier quotation document.\n\n"
        f"Return ONLY a valid JSON object with these exact keys:\n{field_lines}\n\n"
        f"Use null for any field that cannot be determined.\n\n"
    )
    if document_text:
        prompt += f"DOCUMENT CONTENT:\n{document_text}"
    return prompt


def parse_extraction_response(response_text: str, fields: list[dict]) -> dict:
    """Parse JSON response. Returns dict with all field names as keys."""
    json_match = re.search(r"\{[\s\S]*\}", response_text)
    if not json_match:
        raise ValueError(f"No JSON object found in response.")
    data = json.loads(json_match.group())

    for field in fields:
        if field["name"] not in data:
            data[field["name"]] = None
    return data


def extract_values(
    quotation_path: str,
    fields: list[dict],
    config: dict,
) -> dict:
    """
    Read quotation, call LLM, return extracted values dict.
    """
    provider = LLMProvider(
        provider=config.get("provider", "anthropic"),
        api_key=config["api_key"],
        model=config["model"]
    )

    text = read_file_text(quotation_path)

    if text and len(text.strip()) > 50:
        prompt = _build_extraction_prompt(fields, text)
        response = provider.generate_text(prompt)
    else:
        # Vision fallback
        images = read_pdf_as_images_base64(quotation_path)
        prompt = _build_extraction_prompt(fields)
        response = provider.generate_with_vision(prompt, images)

    return parse_extraction_response(response, fields)
