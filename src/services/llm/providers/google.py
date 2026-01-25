# -*- coding: utf-8 -*-
import os
import google.generativeai as genai
from typing import Any, Dict, List, Optional

from ..registry import register_provider
from ..telemetry import track_llm_call
from ..types import AsyncStreamGenerator, TutorResponse, TutorStreamChunk
from .base_provider import BaseLLMProvider
from src.logging.logger import get_logger

logger = get_logger("GoogleGemini")

@register_provider("google")
class GoogleProvider(BaseLLMProvider):
    """Google Gemini LLM Provider."""

    def __init__(self, config):
        super().__init__(config)
        genai.configure(api_key=self.api_key)
        self.model_name = self.config.model_name or "gemini-1.5-flash"

    @track_llm_call("google")
    async def complete(self, prompt: str, **kwargs) -> TutorResponse:
        model_name = kwargs.pop("model", None) or self.model_name
        kwargs.pop("stream", None)
        
        # Map parameters if needed
        generation_config = {
            "temperature": kwargs.get("temperature", 0.7),
            "max_output_tokens": kwargs.get("max_tokens", 4096),
        }

        async def _call_api():
            model = genai.GenerativeModel(model_name)
            # Gemini typically uses content list for messages
            response = await model.generate_content_async(
                prompt,
                generation_config=generation_config
            )
            
            content = response.text
            
            return TutorResponse(
                content=content,
                raw_response={"text": content}, # Minimal for now
                usage={}, # Gemini API return usage differently, can be added later
                provider="google",
                model=model_name,
                finish_reason="stop",
            )

        return await self.execute_with_retry(_call_api)

    async def stream(self, prompt: str, **kwargs) -> AsyncStreamGenerator:
        model_name = kwargs.pop("model", None) or self.model_name
        
        generation_config = {
            "temperature": kwargs.get("temperature", 0.7),
            "max_output_tokens": kwargs.get("max_tokens", 4096),
        }

        async def _create_stream():
            model = genai.GenerativeModel(model_name)
            return await model.generate_content_async(
                prompt,
                generation_config=generation_config,
                stream=True
            )

        stream_response = await self.execute_with_retry(_create_stream)
        accumulated_content = ""

        async for chunk in stream_response:
            if chunk.text:
                delta = chunk.text
                accumulated_content += delta

                yield TutorStreamChunk(
                    content=accumulated_content,
                    delta=delta,
                    provider="google",
                    model=model_name,
                    is_complete=False,
                )

        yield TutorStreamChunk(
            content=accumulated_content, delta="", provider="google", model=model_name, is_complete=True
        )
