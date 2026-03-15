import os
import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from openai import AsyncOpenAI
import aiofiles

logger = logging.getLogger(__name__)


class OpenAIAudioProvider:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.stt_model = 'whisper-1'
        self.tts_model = 'tts-1'
        self.temp_dir = Path(__file__).parent.parent.parent.parent / 'temp'
        self.name = 'OpenAI'

    async def transcribe_audio(self, audio_buffer: bytes, options: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        if options is None:
            options = {}
        
        temp_file_path = None
        
        try:
            timestamp = asyncio.get_event_loop().time()
            timestamp_ms = int(timestamp * 1000)
            filename = f'audio_{timestamp_ms}.webm'
            temp_file_path = self.temp_dir / filename

            async with aiofiles.open(temp_file_path, 'wb') as f:
                await f.write(audio_buffer)

            # Open file for OpenAI API
            with open(temp_file_path, 'rb') as audio_file:
                transcription = await self.client.audio.transcriptions.create(
                    file=audio_file,
                    model=self.stt_model,
                    language=options.get('language', 'en'),
                    response_format=options.get('response_format', 'json'),
                    temperature=options.get('temperature', 0)
                )

            logger.info(f'Audio transcribed: {transcription.text[:100]}...')
            
            return {
                'text': transcription.text,
                'language': options.get('language', 'en')
            }
        except Exception as error:
            logger.error(f'Error transcribing audio: {error}')
            raise
        finally:
            if temp_file_path and temp_file_path.exists():
                try:
                    temp_file_path.unlink()
                except Exception as err:
                    logger.warning(f'Failed to delete temp audio file: {err}')

    async def generate_speech(self, text: str, options: Optional[Dict[str, Any]] = None) -> bytes:
        if options is None:
            options = {}
        
        try:
            voice = options.get('voice', 'nova')
            model = 'tts-1-hd' if options.get('hd') else self.tts_model

            response = await self.client.audio.speech.create(
                model=model,
                voice=voice,
                input=text,
                response_format=options.get('format', 'mp3'),
                speed=options.get('speed', 1.0)
            )

            buffer = response.content
            
            logger.info(f'Speech generated: {text[:50]}... ({len(buffer)} bytes)')
            
            return buffer
        except Exception as error:
            logger.error(f'Error generating speech: {error}')
            raise

    def validate_config(self) -> bool:
        return bool(os.getenv('OPENAI_API_KEY'))

    def get_provider_info(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'type': 'cloud',
            'cost': 'paid',
            'stt_model': self.stt_model,
            'tts_model': self.tts_model
        }
