#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
NarratorAgent - Note narration agent.
Inherits from unified BaseAgent with special TTS configuration.
"""

from datetime import datetime
import json
import os
from pathlib import Path
import re
from typing import Any, Optional
from urllib.parse import urlparse
import uuid

from src.agents.base_agent import BaseAgent
from src.services.tts import get_tts_config

# Import shared stats from edit_agent for legacy compatibility

# Define storage path (unified under user/co-writer/ directory)
USER_DIR = Path(__file__).parent.parent.parent.parent / "data" / "user" / "co-writer" / "audio"


def ensure_dirs():
    """Ensure directories exist"""
    USER_DIR.mkdir(parents=True, exist_ok=True)


class NarratorAgent(BaseAgent):
    """Note Narration Agent - Generate narration script and convert to audio"""

    def __init__(self, language: str = "en"):
        """
        Initialize NarratorAgent.

        Args:
            language: Language setting ('en' | 'zh'), default 'en'

        Note: LLM configuration (api_key, base_url, model, etc.) is loaded
        automatically from the unified config service. Use refresh_config()
        to pick up configuration changes made in Settings.
        """
        # Use "narrator" as module_name to get independent temperature/max_tokens config
        super().__init__(
            module_name="narrator",
            agent_name="narrator_agent",
            language=language,
        )

        # Override prompts to load from co_writer module
        # (narrator_agent prompts are stored under co_writer/prompts/)
        from src.services.prompt import get_prompt_manager

        self.prompts = get_prompt_manager().load_prompts(
            module_name="co_writer",
            agent_name="narrator_agent",
            language=language,
        )

        # Load TTS-specific configuration
        self._load_tts_config()

    def _load_tts_config(self):
        """Load TTS-specific configuration."""
        try:
            self.tts_config = get_tts_config()
            self.default_voice = self.tts_config.get("voice", "alloy")
        except Exception as e:
            self.logger.error(f"Failed to load TTS config: {e}")
            self.tts_config = None
            self.default_voice = "alloy"


    async def process(
        self,
        content: str,
        style: str = "friendly",
        voice: Optional[str] = None,
        skip_audio: bool = False,
    ) -> dict[str, Any]:
        """
        Main processing method - alias for narrate().

        Args:
            content: Note content
            style: Narration style
            voice: Voice role
            skip_audio: Whether to skip audio generation

        Returns:
            Dict containing script info and optionally audio info
        """
        return await self.narrate(content, style, voice, skip_audio)

    async def generate_script(self, content: str, style: str = "friendly") -> dict[str, Any]:
        """
        Generate narration script

        Args:
            content: Note content (Markdown format)
            style: Narration style (friendly, academic, concise)

        Returns:
            Dict containing:
                - script: Narration script text
                - key_points: List of extracted key points
        """
        # Estimate target length: OpenAI TTS supports up to 4096 characters
        is_long_content = len(content) > 5000

        style_prompts = {
            "friendly": self.get_prompt("style_friendly", ""),
            "academic": self.get_prompt("style_academic", ""),
            "concise": self.get_prompt("style_concise", ""),
        }

        length_instruction = (
            self.get_prompt("length_instruction_long", "")
            if is_long_content
            else self.get_prompt("length_instruction_short", "")
        )

        system_template = self.get_prompt("generate_script_system_template", "")
        system_prompt = system_template.format(
            style_prompt=style_prompts.get(style, style_prompts["friendly"]),
            length_instruction=length_instruction,
        )

        if is_long_content:
            user_template = self.get_prompt("generate_script_user_long", "")
            user_prompt = user_template.format(content=content[:8000] + "...")
        else:
            user_template = self.get_prompt("generate_script_user_short", "")
            user_prompt = user_template.format(content=content)

        self.logger.info(f"Generating narration script with style: {style}")

        # Use inherited call_llm method
        response = await self.call_llm(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            stage="generate_script",
        )

        # Clean and truncate response, ensure it doesn't exceed 4000 characters
        script = response.strip()
        if len(script) > 4000:
            self.logger.warning(
                f"Generated script length {len(script)} exceeds 4000 limit. Truncating..."
            )
            truncated = script[:3997]
            last_period = max(
                truncated.rfind("。"),
                truncated.rfind("！"),
                truncated.rfind("？"),
                truncated.rfind("."),
                truncated.rfind("!"),
                truncated.rfind("?"),
            )
            if last_period > 3500:
                script = truncated[: last_period + 1]
            else:
                script = truncated + "..."

        key_points = await self._extract_key_points(content)

        return {
            "script": script,
            "key_points": key_points,
            "style": style,
            "original_length": len(content),
            "script_length": len(script),
        }

    async def _extract_key_points(self, content: str) -> list:
        """Extract key points from notes"""
        system_prompt = self.get_prompt("extract_key_points_system", "")
        user_template = self.get_prompt(
            "extract_key_points_user",
            "Please extract key points from the following notes:\n\n{content}",
        )
        user_prompt = user_template.format(content=content[:4000])

        try:
            response = await self.call_llm(
                user_prompt=user_prompt,
                system_prompt=system_prompt,
                stage="extract_key_points",
            )

            # Try to parse JSON
            json_match = re.search(r"\[.*\]", response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return []
        except Exception as e:
            self.logger.warning(f"Failed to extract key points: {e}")
            return []

    async def generate_audio(self, script: str, voice: str = None) -> dict[str, Any]:
        """
        Convert narration script to audio using the unified TTS service.

        Args:
            script: Narration script text
            voice: Voice role (alloy, echo, fable, onyx, nova, shimmer)

        Returns:
            Dict containing:
                - audio_path: Audio file path
                - audio_url: Audio access URL
                - audio_id: Unique audio identifier
                - voice: Voice used
        """
        # Truncate script if needed (OpenAI limit is 4096)
        if len(script) > 4096:
            self.logger.warning(f"Script length {len(script)} exceeds 4096 limit. Truncating...")
            script = script[:4093] + "..."

        ensure_dirs()
        audio_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:6]
        audio_filename = f"narration_{audio_id}.mp3"
        audio_path = USER_DIR / audio_filename

        self.logger.info(f"Starting TTS audio generation - ID: {audio_id}, Voice: {voice or self.default_voice}")

        try:
            from src.services.tts import generate_audio
            
            result = await generate_audio(
                text=script,
                voice=voice or self.default_voice,
                output_path=audio_path
            )

            # Use correct path: co-writer/audio (matching the actual storage directory)
            relative_path = f"co-writer/audio/{audio_filename}"
            audio_access_url = f"/api/outputs/{relative_path}"

            return {
                "audio_path": result["audio_path"],
                "audio_url": audio_access_url,
                "audio_id": audio_id,
                "voice": result["voice"],
            }

        except Exception as e:
            self.logger.error(f"TTS generation failed: {e}", exc_info=True)
            raise ValueError(f"TTS generation failed: {e}")

    async def narrate(
        self,
        content: str,
        style: str = "friendly",
        voice: str = None,
        skip_audio: bool = False,
    ) -> dict[str, Any]:
        """
        Complete narration flow: generate script + generate audio

        Args:
            content: Note content
            style: Narration style
            voice: Voice role (alloy, echo, fable, onyx, nova, shimmer)
            skip_audio: Whether to skip audio generation (only return script)

        Returns:
            Dict containing script info and optionally audio info
        """
        # Refresh TTS config before starting to avoid stale credentials
        try:
            self.tts_config = get_tts_config()
        except Exception as e:
            self.logger.error(f"Failed to refresh TTS config: {e}")

        script_result = await self.generate_script(content, style)

        # Use default voice if not specified
        if voice is None:
            voice = self.default_voice

        result = {
            "script": script_result["script"],
            "key_points": script_result["key_points"],
            "style": style,
            "original_length": script_result["original_length"],
            "script_length": script_result["script_length"],
        }

        if not skip_audio and self.tts_config:
            try:
                audio_result = await self.generate_audio(script_result["script"], voice=voice)
                result.update(
                    {
                        "audio_url": audio_result["audio_url"],
                        "audio_path": audio_result["audio_path"],
                        "audio_id": audio_result["audio_id"],
                        "voice": voice,
                        "has_audio": True,
                    }
                )
            except Exception as e:
                self.logger.error(f"Audio generation failed: {e}")
                result["has_audio"] = False
                result["audio_error"] = str(e)
        else:
            result["has_audio"] = False
            if not self.tts_config:
                result["audio_error"] = "TTS not configured"

        return result


__all__ = ["NarratorAgent"]
