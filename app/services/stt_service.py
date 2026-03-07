import os
import logging
from typing import Optional, Dict, Any

from .audio_providers import OpenAIAudioProvider, LocalAudioProvider

logger = logging.getLogger(__name__)


class STTService:
    def __init__(self):
        self.provider = self.initialize_provider()
        logger.info(f'STT Provider initialized: {self.provider.name}')

    def initialize_provider(self):
        audio_provider = os.getenv('AUDIO_PROVIDER', 'local').lower()
        
        if audio_provider == 'openai' and os.getenv('OPENAI_API_KEY'):
            return OpenAIAudioProvider()
        
        # Default to local
        return LocalAudioProvider()

    async def transcribe_audio(self, audio_buffer: bytes, options: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        if options is None:
            options = {}
        
        try:
            return await self.provider.transcribe_audio(audio_buffer, options)
        except Exception as error:
            logger.error(f'Error transcribing audio: {error}')
            raise

    async def transcribe_audio_stream(self, audio_chunks: list, options: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        if options is None:
            options = {}
        
        try:
            audio_buffer = b''.join(audio_chunks)
            return await self.transcribe_audio(audio_buffer, options)
        except Exception as error:
            logger.error(f'Error transcribing audio stream: {error}')
            raise

    def validate_config(self) -> bool:
        return self.provider.validate_config()

    def get_provider_info(self) -> Dict[str, Any]:
        return self.provider.get_provider_info()
