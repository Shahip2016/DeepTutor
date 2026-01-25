# -*- coding: utf-8 -*-
"""
TTS Service
===========

Text-to-Speech configuration for DeepTutor.
"""

from .config import get_tts_config
from .factory import TTSFactory, generate_audio

__all__ = ["get_tts_config", "TTSFactory", "generate_audio"]
