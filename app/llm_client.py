from __future__ import annotations

import base64
import json
import re
from pathlib import Path
from typing import Any

from openai import AsyncOpenAI

from .config import Settings
from .prompts import build_messages


class LLMClient:
    def __init__(self, settings: Settings):
        self.settings = settings

        if not self.settings.api_key:
            raise RuntimeError(
                'Не задан OPENAI_API_KEY. Добавь ключ в файл .env '
                'или в переменные окружения.'
            )

        client_kwargs: dict[str, Any] = {
            'api_key': self.settings.api_key,
            'timeout': self.settings.request_timeout_seconds,
        }

        if self.settings.api_base_url:
            client_kwargs['base_url'] = self.settings.api_base_url

        self.client = AsyncOpenAI(**client_kwargs)

    async def generate(
        self,
        *,
        topic: str,
        number: int,
        question_types: list[str],
        language: str = 'ru',
        difficulty: str | None = None,
        audience: str | None = None,
        extra_instructions: str | None = None,
        pdf_paths: list[Path] | None = None,
    ) -> tuple[str, dict | None]:
        messages = build_messages(
            topic=topic,
            number=number,
            question_types=question_types,
            language=language,
            difficulty=difficulty,
            audience=audience,
            extra_instructions=extra_instructions,
            pdf_paths=pdf_paths or [],
        )

        response = await self.client.chat.completions.create(
            model=self.settings.model_name,
            messages=messages,
        )

        raw_text = self._extract_text(response)
        parsed_json = self._try_parse_json(raw_text)

        return raw_text, parsed_json

    def _extract_text(self, response: Any) -> str:
        try:
            return (response.choices[0].message.content or '').strip()
        except Exception:
            return ''

    def _try_parse_json(self, text: str) -> dict | None:
        candidates = [text.strip()]

        fenced_match = re.search(
            r'```(?:json)?\s*(.*?)\s*```',
            text,
            flags=re.DOTALL | re.IGNORECASE,
        )
        if fenced_match:
            candidates.append(fenced_match.group(1).strip())

        for candidate in candidates:
            if not candidate:
                continue
            try:
                value = json.loads(candidate)
                if isinstance(value, dict):
                    return value
            except json.JSONDecodeError:
                continue

        return None

    @staticmethod
    def file_to_data_url(path: Path) -> str:
        raw = path.read_bytes()
        encoded = base64.b64encode(raw).decode('utf-8')
        return f'data:application/pdf;base64,{encoded}'