import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from openai import AsyncAzureOpenAI, AsyncOpenAI
from src.services.tts.providers.base_provider import BaseTTSProvider
from src.logging.logger import get_logger

logger = get_logger("OpenAITTS")

class OpenAITTSProvider(BaseTTSProvider):
    """OpenAI and Azure OpenAI TTS Provider."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.validate_config(config)
        
        binding = os.getenv("TTS_BINDING", "openai")
        api_version = config.get("api_version")

        if binding == "azure_openai" or (binding == "openai" and api_version):
            self.client = AsyncAzureOpenAI(
                api_key=config["api_key"],
                azure_endpoint=config["base_url"],
                api_version=api_version,
            )
        else:
            self.client = AsyncOpenAI(
                base_url=config["base_url"], 
                api_key=config["api_key"]
            )

    def validate_config(self, config: Dict[str, Any]):
        required_keys = ["model", "api_key", "base_url"]
        missing_keys = [key for key in required_keys if key not in config]
        if missing_keys:
            raise ValueError(f"OpenAI TTS config missing: {missing_keys}")

    async def generate_audio(
        self, 
        text: str, 
        voice: Optional[str] = None, 
        output_path: Optional[Path] = None,
        **kwargs
    ) -> Dict[str, Any]:
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        voice = voice or self.config.get("voice", "alloy")
        model = self.config["model"]

        if not output_path:
            # Default output path logic if not provided
            # This is slightly simplified, NarratorAgent will usually provide it
            output_path = Path("data/user/co-writer/audio") / f"tts_{uuid.uuid4().hex[:8]}.mp3"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            response = await self.client.audio.speech.create(
                model=model, 
                voice=voice, 
                input=text
            )
            await response.stream_to_file(output_path)
            
            return {
                "audio_path": str(output_path),
                "voice": voice,
                "model": model,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"OpenAI TTS failed: {e}")
            raise
