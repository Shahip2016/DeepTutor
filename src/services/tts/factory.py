from typing import Any, Dict, Optional
from src.services.tts.providers.openai import OpenAITTSProvider
from src.services.tts.providers.base_provider import BaseTTSProvider
from src.services.tts.config import get_tts_config
import os

class TTSFactory:
    """Factory for creating TTS providers."""
    
    _providers: Dict[str, BaseTTSProvider] = {}

    @classmethod
    def get_provider(cls, name: Optional[str] = None) -> BaseTTSProvider:
        """
        Get a TTS provider instance.
        
        Args:
            name: Provider name ('openai', 'azure_openai', etc.)
            
        Returns:
            A BaseTTSProvider instance.
        """
        # If name not provided, use default from environment or config
        if not name:
            name = os.getenv("TTS_BINDING", "openai")
        
        if name not in cls._providers:
            config = get_tts_config()
            if name in ["openai", "azure_openai"]:
                cls._providers[name] = OpenAITTSProvider(config)
            else:
                # Default to OpenAI for now, or raise error
                # For Qwen, we would add it here
                cls._providers[name] = OpenAITTSProvider(config)
                
        return cls._providers[name]

async def generate_audio(text: str, voice: Optional[str] = None, **kwargs):
    """Convenience function to generate audio using the default provider."""
    provider = TTSFactory.get_provider()
    return await provider.generate_audio(text, voice, **kwargs)
