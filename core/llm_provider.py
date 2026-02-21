"""
Unified interface for multiple AI providers: Anthropic, OpenAI, Google Gemini.
Handles text and vision (image) requests.
"""

import os
import anthropic
import openai
import google.generativeai as genai
from typing import List, Dict, Any, Optional


class LLMProvider:
    def __init__(self, provider: str, api_key: str, model: str):
        # Safety check: if provider is None, default to anthropic
        self.provider = (provider or "anthropic").lower()
        self.api_key = api_key
        self.model = model
        self._setup_client()

    def _setup_client(self):
        if self.provider == "anthropic":
            self.client = anthropic.Anthropic(api_key=self.api_key)
        elif self.provider == "openai":
            self.client = openai.OpenAI(api_key=self.api_key)
        elif self.provider == "google":
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel(self.model)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    def generate_text(self, prompt: str, system_prompt: str = "") -> str:
        """Simple text generation."""
        if self.provider == "anthropic":
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system_prompt if system_prompt else None,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text

        elif self.provider == "openai":
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=4096
            )
            return response.choices[0].message.content

        elif self.provider == "google":
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = self.client.generate_content(full_prompt)
            return response.text

    def generate_with_vision(self, prompt: str, images_base64: List[str], system_prompt: str = "") -> str:
        """Generation with one or more images (base64 PNG/JPG)."""
        if self.provider == "anthropic":
            content = []
            for b64 in images_base64:
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": b64
                    }
                })
            content.append({"type": "text", "text": prompt})
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system_prompt if system_prompt else None,
                messages=[{"role": "user", "content": content}]
            )
            return message.content[0].text

        elif self.provider == "openai":
            content = [{"type": "text", "text": prompt}]
            for b64 in images_base64:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64}"}
                })
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": content})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=4096
            )
            return response.choices[0].message.content

        elif self.provider == "google":
            import base64
            parts = [f"{system_prompt}\n\n{prompt}" if system_prompt else prompt]
            for b64 in images_base64:
                parts.append({
                    "mime_type": "image/png",
                    "data": base64.b64decode(b64)
                })
            response = self.client.generate_content(parts)
            return response.text
