import os
import re
import logging
from typing import Optional, Dict, Any, List, AsyncGenerator

from .audio_providers import OpenAIAudioProvider, LocalAudioProvider

logger = logging.getLogger(__name__)


class TTSService:
    def __init__(self):
        self.provider = self.initialize_provider()
        self.emotional_voices = {
            'happy': 'nova',
            'excited': 'shimmer',
            'sad': 'alloy',
            'anxious': 'echo',
            'angry': 'onyx',
            'neutral': 'nova',
            'grateful': 'nova',
            'confused': 'alloy'
        }
        logger.info(f'TTS Provider initialized: {self.provider.name}')

    def initialize_provider(self):
        audio_provider = os.getenv('AUDIO_PROVIDER', 'local').lower()
        
        if audio_provider == 'openai' and os.getenv('OPENAI_API_KEY'):
            return OpenAIAudioProvider()
        
        # Default to local
        return LocalAudioProvider()

    async def generate_speech(self, text: str, options: Optional[Dict[str, Any]] = None) -> bytes:
        if options is None:
            options = {}
        
        try:
            return await self.provider.generate_speech(text, options)
        except Exception as error:
            logger.error(f'Error generating speech: {error}')
            raise

    async def generate_emotional_speech(self, text: str, emotion: str, options: Optional[Dict[str, Any]] = None) -> bytes:
        if options is None:
            options = {}
        
        try:
            voice = self.emotional_voices.get(emotion, 'nova')
            
            speed = 1.0
            if emotion == 'excited':
                speed = 1.1
            elif emotion in ['sad', 'anxious']:
                speed = 0.9

            return await self.generate_speech(text, {
                **options,
                'voice': voice,
                'speed': options.get('speed', speed)
            })
        except Exception as error:
            logger.error(f'Error generating emotional speech: {error}')
            raise

    def validate_config(self) -> bool:
        return self.provider.validate_config()

    def get_provider_info(self) -> Dict[str, Any]:
        return self.provider.get_provider_info()

    async def generate_streaming_speech(self, text: str, options: Optional[Dict[str, Any]] = None) -> AsyncGenerator[bytes, None]:
        if options is None:
            options = {}
        
        try:
            # Only OpenAI provider supports streaming
            if not isinstance(self.provider, OpenAIAudioProvider):
                # For non-streaming providers, generate full audio and chunk it
                audio_buffer = await self.generate_speech(text, options)
                chunk_size = 4096
                for i in range(0, len(audio_buffer), chunk_size):
                    yield audio_buffer[i:i + chunk_size]
                return

            voice = options.get('voice', 'nova')
            model = 'tts-1-hd' if options.get('hd') else self.provider.tts_model

            response = await self.provider.client.audio.speech.create(
                model=model,
                voice=voice,
                input=text,
                response_format='mp3',
                speed=options.get('speed', 1.0)
            )

            buffer = response.content
            
            chunk_size = 4096
            for i in range(0, len(buffer), chunk_size):
                yield buffer[i:i + chunk_size]
            
            logger.info(f'Streaming speech generated: {text[:50]}...')
        except Exception as error:
            logger.error(f'Error generating streaming speech: {error}')
            raise

    def get_available_voices(self) -> List[str]:
        return ['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer']

    def get_emotional_voice_mapping(self) -> Dict[str, str]:
        return self.emotional_voices

    async def generate_speech_chunks(self, text_chunks: List[str], options: Optional[Dict[str, Any]] = None) -> List[bytes]:
        if options is None:
            options = {}
        
        try:
            audio_chunks = []
            
            for text in text_chunks:
                if text.strip():
                    audio = await self.generate_speech(text, options)
                    audio_chunks.append(audio)
            
            return audio_chunks
        except Exception as error:
            logger.error(f'Error generating speech chunks: {error}')
            raise

    def split_text_for_tts(self, text: str, max_length: int = 4000) -> List[str]:
        """Split text into chunks suitable for TTS processing"""
        chunks = []
        
        # Split by sentences
        sentences = re.findall(r'[^.!?]+[.!?]+', text)
        if not sentences:
            sentences = [text]
        
        current_chunk = ''
        
        for sentence in sentences:
            if len(current_chunk + sentence) > max_length:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk += sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
