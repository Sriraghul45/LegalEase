from __future__ import annotations

import os
import random
import time
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")


class GeminiConfigurationError(RuntimeError):
    """Raised when Gemini cannot be configured."""


class GeminiGenerationError(RuntimeError):
    """Raised when Gemini fails to generate a document."""


class GeminiDocumentGenerator:
    """Generate structured legal-document drafts with the Gemini API."""

    _retry_waits = (2, 4, 8)

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "").strip()
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()
        self.fallback_model = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-3.5-flash").strip()
        if not self.api_key:
            raise GeminiConfigurationError(
                "GEMINI_API_KEY is missing. Add it to the .env file or environment."
            )
        try:
            self.client = genai.Client(api_key=self.api_key)
        except Exception as exc:  # SDK may raise different exception types by version.
            raise GeminiConfigurationError(f"Unable to initialize Gemini client: {exc}") from exc

    @staticmethod
    def _is_retryable_unavailable_error(exc: Exception) -> bool:
        message = str(exc).lower()
        status_code = getattr(exc, "status_code", None)
        code = getattr(exc, "code", None)
        code_text = str(code).lower() if code is not None else ""

        if status_code in {400, 401, 403} or code in {400, 401, 403}:
            return False

        return (
            status_code == 503
            or code == 503
            or "503" in message
            or "service unavailable" in message
            or "unavailable" in message
            or "high demand" in message
            or "resource exhausted" in message
            or "temporarily busy" in message
            or code_text in {"503", "unavailable", "resource_exhausted"}
        )

    def _generate_with_model(self, model_name: str, prompt: str) -> str:
        for attempt in range(1, 5):
            try:
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.25,
                        max_output_tokens=6000,
                    ),
                )
                text = (response.text or "").strip()
                if not text:
                    raise GeminiGenerationError("Gemini returned an empty response.")
                return text
            except Exception as exc:
                if not self._is_retryable_unavailable_error(exc):
                    raise GeminiGenerationError(f"Gemini generation failed: {exc}") from exc

                if attempt == 4:
                    raise GeminiGenerationError(
                        f"Gemini is temporarily busy on model {model_name}. Please try again in a moment."
                    ) from exc

                wait_seconds = self._retry_waits[attempt - 1] + random.uniform(0, 0.5)
                time.sleep(wait_seconds)

        raise GeminiGenerationError(
            "Gemini is temporarily busy. Please try again in a moment."
        )

    @staticmethod
    def _build_prompt(
        document_type: str,
        parties: str,
        terms: str,
        effective_date: str,
    ) -> str:
        return f"""You are a careful legal-document drafting assistant.

Create a professional DRAFT of the requested legal document using only the supplied facts.
Do not invent names, addresses, amounts, dates, governing laws, obligations, or other material facts.
If an important fact is missing, use a clear placeholder such as [MISSING INFORMATION].
Do not claim that the document is legally valid, legally sound, or guaranteed enforceable.
Use neutral, jurisdiction-aware language and clearly label the result as a draft.

DOCUMENT TYPE:
{document_type}

PARTIES:
{parties}

TERMS / CONDITIONS:
{terms}

EFFECTIVE DATE:
{effective_date}

OUTPUT FORMAT:
- Start with a clear title.
- Include a short "DRAFT — FOR REVIEW" notice.
- Use numbered sections with descriptive headings.
- Include the supplied parties and effective date accurately.
- Include a Terms / Key Conditions section.
- Include signature blocks when appropriate.
- Do not add commentary outside the document.
"""

    def generate_document(
        self,
        document_type: str,
        parties: str,
        terms: str,
        effective_date: str,
    ) -> str:
        prompt = self._build_prompt(document_type, parties, terms, effective_date)
        models_to_try = [self.model]
        if self.fallback_model and self.fallback_model != self.model:
            models_to_try.append(self.fallback_model)

        last_error: Optional[GeminiGenerationError] = None

        for model_name in models_to_try:
            try:
                return self._generate_with_model(model_name, prompt)
            except GeminiGenerationError as exc:
                last_error = exc
                continue

        if last_error is not None:
            raise last_error

        raise GeminiGenerationError("Gemini is temporarily busy. Please try again in a moment.")
