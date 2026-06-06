"""
Cliente da API do LLM.

Encapsula a chamada à API para que o resto do código não precise
saber qual provedor está sendo usado.

Suporta Anthropic (Claude) e DeepSeek.
"""

from __future__ import annotations
from dataclasses import dataclass
import time

from config import (
    ANTHROPIC_API_KEY,
    LLM_MODEL,
    MAX_TOKENS_PER_RESPONSE,
    DEEPSEEK_API_KEY,
)
USE_DEEPSEEK = bool(DEEPSEEK_API_KEY)


@dataclass
class LLMResponse:
    text: str
    tool_calls: list[dict]
    raw_response: object
    input_tokens: int
    output_tokens: int
    stop_reason: str
    latency_seconds: float


class LLMClient:

    def __init__(self):
        if USE_DEEPSEEK:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=DEEPSEEK_API_KEY,
                base_url="https://api.deepseek.com",
            )
            self.model = "deepseek-chat"
            self.provider = "deepseek"
        else:
            from anthropic import Anthropic
            if not ANTHROPIC_API_KEY:
                raise RuntimeError(
                    "Nenhuma API key configurada. "
                    "Defina ANTHROPIC_API_KEY ou DEEPSEEK_API_KEY no .env."
                )
            self.client = Anthropic(api_key=ANTHROPIC_API_KEY)
            self.model = LLM_MODEL
            self.provider = "anthropic"

    def chat(self, messages, tools, system="") -> LLMResponse:
        if self.provider == "deepseek":
            return self._chat_deepseek(messages, tools, system)
        return self._chat_anthropic(messages, tools, system)

    def _chat_anthropic(self, messages, tools, system) -> LLMResponse:
        kwargs = {
            "model": self.model,
            "max_tokens": MAX_TOKENS_PER_RESPONSE,
            "messages": messages,
            "tools": tools,
        }
        if system:
            kwargs["system"] = system

        inicio = time.perf_counter()
        resp = self.client.messages.create(**kwargs)
        latencia = time.perf_counter() - inicio

        texto = ""
        tool_calls = []
        for bloco in resp.content:
            if bloco.type == "text":
                texto += bloco.text
            elif bloco.type == "tool_use":
                tool_calls.append({
                    "id": bloco.id,
                    "name": bloco.name,
                    "input": bloco.input,
                })

        return LLMResponse(
            text=texto,
            tool_calls=tool_calls,
            raw_response=resp,
            input_tokens=resp.usage.input_tokens,
            output_tokens=resp.usage.output_tokens,
            stop_reason=resp.stop_reason,
            latency_seconds=latencia,
        )

    def _chat_deepseek(self, messages, tools, system) -> LLMResponse:
        if system:
            messages = [{"role": "system", "content": system}] + messages

        # Converte formato Anthropic de tools para OpenAI
        tools_openai = [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["input_schema"],
                }
            }
            for t in tools
        ]

        inicio = time.perf_counter()
        resp = self.client.chat.completions.create(
            model=self.model,
            max_tokens=MAX_TOKENS_PER_RESPONSE,
            messages=messages,
            tools=tools_openai if tools_openai else None,
        )
        latencia = time.perf_counter() - inicio

        msg = resp.choices[0].message
        texto = msg.content or ""
        tool_calls = []

        if msg.tool_calls:
            import json
            for tc in msg.tool_calls:
                tool_calls.append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "input": json.loads(tc.function.arguments),
                })

        stop_reason = "tool_use" if tool_calls else "end_turn"

        return LLMResponse(
            text=texto,
            tool_calls=tool_calls,
            raw_response=resp,
            input_tokens=resp.usage.prompt_tokens,
            output_tokens=resp.usage.completion_tokens,
            stop_reason=stop_reason,
            latency_seconds=latencia,
        )