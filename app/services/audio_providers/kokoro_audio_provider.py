import os
import asyncio
import logging
import warnings
from pathlib import Path
from typing import Optional, Dict, Any
import aiofiles

logger = logging.getLogger(__name__)

# Kokoro-82M Hugging Face repo
KOKORO_REPO_ID = 'hexgrad/Kokoro-82M'


class KokoroAudioProvider:
    """Kokoro-82M TTS provider for high-quality local text-to-speech"""
    
    def __init__(self):
        self.temp_dir = Path(__file__).parent.parent.parent.parent / 'temp'
        self.name = 'Kokoro-82M (Local, High Quality)'
        
        self.lang_code = os.getenv('KOKORO_LANG_CODE', 'a')
        self.default_voice = os.getenv('KOKORO_DEFAULT_VOICE', 'af_heart')
        self.sample_rate = int(os.getenv('KOKORO_SAMPLE_RATE', '24000'))
        
        self.emotional_voices = {
            'happy': 'af_bella',
            'excited': 'af_heart',
            'sad': 'af_sky',
            'anxious': 'af_alloy',
            'angry': 'am_adam',
            'neutral': 'af_heart',
            'grateful': 'af_bella',
            'confused': 'af_sarah'
        }
        
        self.pipeline = None
        self.keep_temp_audio = os.getenv('KEEP_TEMP_AUDIO', 'false').lower() == 'true'
        
        logger.info(f'Kokoro-82M TTS Provider initialized (lang: {self.lang_code}, voice: {self.default_voice})')
    
    def _initialize_pipeline(self):
        """Lazy initialization of Kokoro pipeline"""
        if self.pipeline is None:
            try:
                from kokoro import KPipeline
                logger.info('Loading Kokoro-82M model...')
                # Suppress noisy torch/kokoro warnings during load
                with warnings.catch_warnings():
                    warnings.filterwarnings('ignore', message='.*repo_id.*', category=UserWarning)
                    warnings.filterwarnings('ignore', message='.*dropout option adds dropout.*', category=UserWarning)
                    warnings.filterwarnings('ignore', message='.*weight_norm is deprecated.*', category=UserWarning)
                    self.pipeline = KPipeline(lang_code=self.lang_code, repo_id=KOKORO_REPO_ID)
                logger.info('✅ Kokoro-82M model loaded successfully')
            except ImportError as e:
                logger.error(f'Kokoro package not installed: {e}')
                raise Exception('Kokoro not installed. Run: pip install kokoro>=0.9.4 soundfile')
            except Exception as e:
                logger.error(f'Failed to initialize Kokoro pipeline: {e}')
                raise
        return self.pipeline
    
    async def generate_speech(self, text: str, options: Optional[Dict[str, Any]] = None) -> bytes:
        """Generate speech from text using Kokoro-82M"""
        if options is None:
            options = {}
        
        text = (text or '').strip()
        if not text:
            return b''
        
        timestamp = asyncio.get_event_loop().time()
        timestamp_ms = int(timestamp * 1000)
        output_path = self.temp_dir / f'kokoro_speech_{timestamp_ms}.wav'
        
        try:
            import soundfile as sf
            
            pipeline = self._initialize_pipeline()
            
            voice = options.get('voice', self.default_voice)
            speed = options.get('speed', 1.0)
            
            logger.info(f'Generating speech with Kokoro: voice={voice}, speed={speed}')
            
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            audio_data = await loop.run_in_executor(
                None,
                self._generate_sync,
                pipeline,
                text,
                voice,
                speed
            )
            
            if audio_data is None:
                raise Exception('Failed to generate audio')
            
            # Save to WAV file
            self.temp_dir.mkdir(exist_ok=True)
            sf.write(str(output_path), audio_data, self.sample_rate)
            
            # Read back as bytes
            async with aiofiles.open(output_path, 'rb') as f:
                buffer = await f.read()
            
            if self.keep_temp_audio:
                logger.info(f'Generated speech saved to: {output_path}')
            else:
                output_path.unlink()
            
            logger.info(f'✅ Kokoro speech generated: {len(buffer)} bytes')
            return buffer
            
        except ImportError as e:
            logger.error(f'Missing dependency: {e}')
            raise Exception('Kokoro dependencies not installed. Run: pip install kokoro>=0.9.4 soundfile')
        except Exception as error:
            logger.error(f'Error generating speech with Kokoro: {error}')
            if output_path.exists() and not self.keep_temp_audio:
                output_path.unlink()
            raise
    
    def _generate_sync(self, pipeline, text: str, voice: str, speed: float):
        """Synchronous generation for executor"""
        try:
            generator = pipeline(text, voice=voice, speed=speed)
            
            audio_chunks = []
            for gs, ps, audio in generator:
                audio_chunks.append(audio)
            
            if not audio_chunks:
                return None
            
            import numpy as np
            full_audio = np.concatenate(audio_chunks)
            return full_audio
            
        except Exception as e:
            logger.error(f'Error in sync generation: {e}')
            raise
    
    async def generate_emotional_speech(self, text: str, emotion: str, options: Optional[Dict[str, Any]] = None) -> bytes:
        """Generate speech with emotion-appropriate voice"""
        if options is None:
            options = {}
        
        voice = self.emotional_voices.get(emotion, self.default_voice)
        
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
    
    async def transcribe_audio(self, audio_buffer: bytes, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Kokoro is TTS only, no STT capability"""
        raise NotImplementedError('Kokoro provider does not support speech-to-text. Use Whisper for STT.')
    
    def validate_config(self) -> bool:
        """Check if Kokoro is properly installed"""
        try:
            from kokoro import KPipeline
            import soundfile
            return True
        except ImportError:
            return False
    
    def get_provider_info(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'type': 'local',
            'cost': 'free',
            'quality': 'high',
            'stt_options': ['Not supported - use Whisper'],
            'tts_options': ['Kokoro-82M (54 voices, 8 languages)'],
            'voices': list(self.emotional_voices.values()),
            'sample_rate': self.sample_rate,
            'note': 'Requires kokoro package and espeak-ng'
        }
    
    def get_available_voices(self) -> list:
        """Return list of available voices"""
        return [
            'af_heart', 'af_bella', 'af_sarah', 'af_nicole', 'af_alloy',
            'af_aoede', 'af_jessica', 'af_kore', 'af_nova', 'af_river', 'af_sky',
            'am_adam', 'am_echo', 'am_eric', 'am_fenrir', 'am_liam',
            'am_michael', 'am_onyx', 'am_puck', 'am_santa',
            'bf_alice', 'bf_emma', 'bf_isabella', 'bf_lily',
            'bm_daniel', 'bm_fable', 'bm_george', 'bm_lewis'
        ]
