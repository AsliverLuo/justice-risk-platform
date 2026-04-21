from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class LLMTextResponse:
    text: str


class BaseLLMClient(ABC):
    provider: str = "base"
    is_echo: bool = False

    @abstractmethod
    def complete_text(self, prompt: str, system_prompt: str | None = None) -> LLMTextResponse:
        raise NotImplementedError

    def complete_json(self, prompt: str, system_prompt: str | None = None) -> dict:
        raw = self.complete_text(prompt=prompt, system_prompt=system_prompt).text
        normalized = self._extract_json_block(raw)
        try:
            return json.loads(normalized)
        except json.JSONDecodeError:
            logger.warning("json decode failed, returning wrapped text")
            return {"raw_text": raw}

    @staticmethod
    def _extract_json_block(raw: str) -> str:
        if not raw:
            return "{}"
        stripped = raw.strip()
        if stripped.startswith("```"):
            stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
            stripped = re.sub(r"\s*```$", "", stripped)
        start_obj = stripped.find("{")
        end_obj = stripped.rfind("}")
        start_arr = stripped.find("[")
        end_arr = stripped.rfind("]")
        if start_obj >= 0 and end_obj > start_obj:
            return stripped[start_obj:end_obj + 1]
        if start_arr >= 0 and end_arr > start_arr:
            return stripped[start_arr:end_arr + 1]
        return stripped


class EchoLLMClient(BaseLLMClient):
    provider = "echo"
    is_echo = True
    def complete_text(self, prompt: str, system_prompt: str | None = None) -> LLMTextResponse:
        return LLMTextResponse(
            text=json.dumps(
                {
                    "mode": "echo",
                    "system_prompt": system_prompt,
                    "prompt": prompt[:1200],
                    "message": "当前为离线回退模式，请配置真实 LLM 后替换。",
                },
                ensure_ascii=False,
            )
        )


class OpenAILLMClient(BaseLLMClient):
    provider = "openai"
    is_echo = False


    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str | None = None,
        timeout_seconds: int = 45,
        force_json_object: bool = True,
        disable_thinking: bool = True,
    ) -> None:
        from openai import OpenAI  # type: ignore

        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout_seconds,
        )
        self.model = model
        self.force_json_object = force_json_object
        self.disable_thinking = disable_thinking

    def complete_text(self, prompt: str, system_prompt: str | None = None) -> LLMTextResponse:
        kwargs = {
            "model": self.model,
            "temperature": 0.1,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt or "你是法律 AI 助手，请输出准确、结构化、可审查的 JSON。",
                },
                {"role": "user", "content": prompt},
            ],
        }

        if self.force_json_object:
            kwargs["response_format"] = {"type": "json_object"}

        extra_body = {}
        if self.disable_thinking:
            extra_body["enable_thinking"] = False

        if extra_body:
            kwargs["extra_body"] = extra_body

        resp = self.client.chat.completions.create(**kwargs)
        content = resp.choices[0].message.content or ""
        return LLMTextResponse(text=content)


def build_llm_client() -> BaseLLMClient:
    if settings.llm_provider == "openai" and settings.openai_api_key:
        try:
            return OpenAILLMClient(
                api_key=settings.openai_api_key,
                model=settings.llm_model,
                base_url=settings.openai_base_url,
                timeout_seconds=settings.llm_timeout_seconds,
                force_json_object=settings.llm_force_json_object,
                disable_thinking=settings.llm_disable_thinking,
            )
        except Exception as exc:
            logger.warning("openai-compatible client init failed, fallback to echo: %s", exc)

    return EchoLLMClient()
