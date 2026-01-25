from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pathlib import Path

class BaseTTSProvider(ABC):
    """Abstract base class for TTS providers."""

    @abstractmethod
    async def generate_audio(
        self, 
        text: str, 
        voice: Optional[str] = None, 
        output_path: Optional[Path] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate audio from text.
        
        Args:
            text: Text to convert to speech.
            voice: Voice ID or name.
            output_path: Path to save the generated audio.
            **kwargs: Provider-specific arguments.
            
        Returns:
            Dict containing metadata about the generated audio.
        """
        pass

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]):
        """Validate the provider configuration."""
        pass
