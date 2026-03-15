import os
import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import aiofiles
import httpx

logger = logging.getLogger(__name__)


class LocalAudioProvider:
    def __init__(self):
        self.temp_dir = Path(__file__).parent.parent.parent.parent / 'temp'
        self.name = 'Local (Whisper CLI + eSpeak)'
        
        # Whisper CLI settings
        self.whisper_model = os.getenv('WHISPER_MODEL', 'base.en')
        self.whisper_path = os.getenv('WHISPER_CPP_PATH', 'whisper-cli')
        self.whisper_model_path = os.getenv(
            'WHISPER_MODEL_PATH',
            str(Path.home() / '.whisper-cpp/models')
        )
        
        # eSpeak settings
        self.espeak_enabled = os.getenv('ESPEAK_ENABLED', 'true').lower() == 'true'
        self.espeak_path = os.getenv('ESPEAK_PATH', 'espeak')
        # OpenAI voice names passed by TTS service; eSpeak uses codes like en-us, en-gb
        self._openai_voice_names = {'alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer'}
        
        # Client TTS settings
        self.client_tts_enabled = os.getenv('CLIENT_TTS_ENABLED', 'false').lower() == 'true'
        
        # Debug settings
        self.keep_temp_audio = os.getenv('KEEP_TEMP_AUDIO', 'false').lower() == 'true'
        if self.keep_temp_audio:
            logger.info('KEEP_TEMP_AUDIO enabled - audio files will be saved in temp/ folder')

    async def transcribe_audio(self, audio_buffer: bytes, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if options is None:
            options = {}
        
        temp_raw_path = None
        temp_wav_path = None
        temp_output_path = None
        
        try:
            timestamp = asyncio.get_event_loop().time()
            timestamp_ms = int(timestamp * 1000)
            temp_raw_path = self.temp_dir / f'input_raw_{timestamp_ms}.webm'
            temp_wav_path = self.temp_dir / f'input_{timestamp_ms}.wav'
            temp_output_path = self.temp_dir / f'output_{timestamp_ms}.txt'

            # Save raw audio buffer first
            async with aiofiles.open(temp_raw_path, 'wb') as f:
                await f.write(audio_buffer)
            
            if self.keep_temp_audio:
                logger.info(f'Raw audio saved to: {temp_raw_path}')

            # Convert to WAV format that whisper.cpp expects (16kHz, mono, 16-bit PCM)
            await self.convert_to_whisper_format(temp_raw_path, temp_wav_path)
            
            if self.keep_temp_audio:
                logger.info(f'Converted audio saved to: {temp_wav_path}')

            # Try Whisper.cpp first
            try:
                result = await self.transcribe_with_whisper_cpp(temp_wav_path, options)
                # Add audio file path for emotion detection
                result['audio_file_path'] = str(temp_wav_path)
                return result
            except Exception as whisper_error:
                logger.warning('Whisper.cpp not available, trying Groq Whisper API...')
                
                # Fallback to Groq's free Whisper API
                if os.getenv('GROQ_API_KEY'):
                    result = await self.transcribe_with_groq_whisper(audio_buffer, options)
                    result['audio_file_path'] = str(temp_wav_path)
                    return result
                
                raise Exception('No STT provider available. Install Whisper.cpp or add GROQ_API_KEY')
        except Exception as error:
            logger.error(f'Error transcribing audio: {error}')
            raise
        finally:
            # Cleanup (only if KEEP_TEMP_AUDIO is false)
            if not self.keep_temp_audio:
                for temp_path in [temp_raw_path, temp_wav_path, temp_output_path]:
                    if temp_path and temp_path.exists():
                        try:
                            temp_path.unlink()
                        except Exception:
                            pass

    async def convert_to_whisper_format(self, input_path: Path, output_path: Path):
        """Convert audio to WAV format that whisper.cpp expects using FFmpeg"""
        try:
            logger.debug(f'Converting audio: {input_path} -> {output_path}')
            
            # Use FFmpeg directly to convert to 16kHz, mono, 16-bit PCM WAV
            args = [
                'ffmpeg',
                '-i', str(input_path),
                '-ar', '16000',  # Sample rate: 16kHz
                '-ac', '1',      # Channels: mono
                '-sample_fmt', 's16',  # Sample format: 16-bit signed integer
                '-y',            # Overwrite output file
                str(output_path)
            ]
            
            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode('utf-8')
                logger.error(f'FFmpeg conversion failed: {error_msg}')
                raise Exception(f'FFmpeg conversion failed: {error_msg}')
            
            logger.debug('Audio converted successfully')
        except FileNotFoundError:
            logger.error('FFmpeg not found')
            raise Exception('FFmpeg not found. Install with: brew install ffmpeg (macOS) or sudo apt install ffmpeg (Linux)')
        except Exception as error:
            logger.error(f'Audio conversion failed: {error}')
            raise

    async def transcribe_with_whisper_cpp(self, audio_path: Path, options: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        if options is None:
            options = {}
        
        model_path = Path(self.whisper_model_path) / f'ggml-{self.whisper_model}.bin'
        args = [
            self.whisper_path,
            str(audio_path),
            '--model', str(model_path),
            '--language', options.get('language', 'en'),
            '--no-timestamps',
            '--no-prints'
        ]

        logger.info(f'Running whisper-cli: {" ".join(args)}')
        
        try:
            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            logger.info(f'Whisper process exited with code {process.returncode}')
            
            if process.returncode != 0:
                error_msg = stderr.decode('utf-8')
                logger.error(f'Whisper CLI failed with error: {error_msg}')
                raise Exception(f'Whisper CLI failed: {error_msg}')
            
            # Extract just the transcription text (remove timing info and extra whitespace)
            output = stdout.decode('utf-8')
            lines = output.split('\n')
            transcription = ' '.join([
                line.strip()
                for line in lines
                if line.strip() and 
                   not line.strip().startswith('[') and 
                   'whisper_' not in line
            ]).strip()
            
            logger.info(f'Whisper transcription: "{transcription}"')

            return {
                'text': transcription,
                'language': options.get('language', 'en')
            }
        except FileNotFoundError:
            logger.error(f'Whisper CLI not found at: {self.whisper_path}')
            raise Exception(f'Whisper CLI not found. Install whisper.cpp or set WHISPER_CPP_PATH')
        except Exception as error:
            logger.error(f'Whisper spawn error: {error}')
            raise

    async def transcribe_with_groq_whisper(self, audio_buffer: bytes, options: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        if options is None:
            options = {}
        
        try:
            async with httpx.AsyncClient() as client:
                files = {
                    'file': ('audio.webm', audio_buffer, 'audio/webm')
                }
                data = {
                    'model': 'whisper-large-v3',
                    'language': options.get('language', 'en'),
                    'response_format': 'json'
                }
                
                response = await client.post(
                    'https://api.groq.com/openai/v1/audio/transcriptions',
                    files=files,
                    data=data,
                    headers={
                        'Authorization': f'Bearer {os.getenv("GROQ_API_KEY")}'
                    }
                )
                
                response.raise_for_status()
                result = response.json()

                logger.info('Audio transcribed with Groq Whisper (FREE)')
                
                return {
                    'text': result['text'],
                    'language': options.get('language', 'en')
                }
        except Exception as error:
            logger.error(f'Groq Whisper error: {error}')
            raise

    async def generate_speech(self, text: str, options: Optional[Dict[str, Any]] = None) -> bytes:
        if options is None:
            options = {}
        
        try:
            logger.info(f'🔊 LocalAudioProvider.generate_speech called (espeak_enabled={self.espeak_enabled}, client_tts={self.client_tts_enabled})')
            
            if self.client_tts_enabled:
                logger.info('Client TTS enabled - skipping server-side TTS')
                return b''
            
            # Try Piper first (better quality)
            if await self.is_piper_available():
                logger.info('Using Piper for TTS')
                return await self.generate_speech_with_piper(text, options)
            
            # Fallback to eSpeak if enabled
            if self.espeak_enabled:
                logger.info('Using eSpeak for TTS')
                return await self.generate_speech_with_espeak(text, options)
            
            logger.warning('No TTS provider available (eSpeak disabled, Piper not available)')
            return b''
        except Exception as error:
            logger.error(f'Error generating speech: {error}')
            raise

    def _espeak_voice(self, options: Dict[str, Any]) -> str:
        """Return eSpeak voice code. TTS service passes OpenAI names (alloy, nova); eSpeak needs en-us, en-gb, etc."""
        voice = (options.get('voice') or 'en-us').lower()
        if voice in self._openai_voice_names or '-' not in voice:
            return os.getenv('ESPEAK_VOICE', 'en-us')
        return voice

    async def generate_speech_with_espeak(self, text: str, options: Optional[Dict[str, Any]] = None) -> bytes:
        if options is None:
            options = {}
        text = (text or '').strip()
        if not text:
            return b''

        timestamp = asyncio.get_event_loop().time()
        timestamp_ms = int(timestamp * 1000)
        output_path = self.temp_dir / f'speech_{timestamp_ms}.wav'

        try:
            speed = round((options.get('speed', 1.0)) * 175)
            voice = self._espeak_voice(options)
            # Pass options only; feed text via stdin so long sentences are not truncated (argv limit / quoting)
            args = [
                self.espeak_path,
                '-w', str(output_path),
                '-s', str(speed),
                '-v', voice,
                '--stdin',  # espeak-ng; classic espeak reads stdin when no words given
            ]

            process = await asyncio.create_subprocess_exec(
                *args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate(input=text.encode('utf-8'))
            
            if process.returncode != 0:
                error_msg = stderr.decode('utf-8')
                raise Exception(f'eSpeak failed: {error_msg}')
            
            # Read the generated audio file
            async with aiofiles.open(output_path, 'rb') as f:
                buffer = await f.read()
            
            if self.keep_temp_audio:
                logger.info(f'Generated speech saved to: {output_path}')
            else:
                output_path.unlink()
            
            return buffer
        except FileNotFoundError:
            raise Exception('eSpeak not found. Install with: sudo apt install espeak (Linux) or brew install espeak (macOS)')
        except Exception as error:
            if output_path.exists() and not self.keep_temp_audio:
                output_path.unlink()
            raise

    async def generate_speech_with_piper(self, text: str, options: Optional[Dict[str, Any]] = None) -> bytes:
        if options is None:
            options = {}
        
        timestamp = asyncio.get_event_loop().time()
        timestamp_ms = int(timestamp * 1000)
        output_path = self.temp_dir / f'speech_{timestamp_ms}.wav'
        piper_path = os.getenv('PIPER_PATH', 'piper')
        piper_model = os.getenv('PIPER_MODEL', 'en_US-lessac-medium')

        try:
            args = [
                piper_path,
                '--model', piper_model,
                '--output_file', str(output_path)
            ]

            process = await asyncio.create_subprocess_exec(
                *args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Send text to stdin
            stdout, stderr = await process.communicate(input=text.encode('utf-8'))
            
            if process.returncode != 0:
                error_msg = stderr.decode('utf-8')
                raise Exception(f'Piper failed: {error_msg}')
            
            # Read the generated audio file
            async with aiofiles.open(output_path, 'rb') as f:
                buffer = await f.read()
            
            if self.keep_temp_audio:
                logger.info(f'Generated speech (Piper) saved to: {output_path}')
            else:
                output_path.unlink()
            
            return buffer
        except Exception as error:
            if output_path.exists() and not self.keep_temp_audio:
                output_path.unlink()
            raise

    async def is_piper_available(self) -> bool:
        try:
            piper_path = os.getenv('PIPER_PATH', 'piper')
            process = await asyncio.create_subprocess_exec(
                piper_path,
                '--version',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            return process.returncode == 0
        except Exception:
            return False

    def validate_config(self) -> bool:
        """Check if any STT option is available"""
        return self.check_whisper_cpp() or bool(os.getenv('GROQ_API_KEY'))

    def check_whisper_cpp(self) -> bool:
        """Simple check - will fail gracefully if not available"""
        return True

    def get_provider_info(self) -> Dict[str, Any]:
        tts_options = []
        if not self.client_tts_enabled:
            tts_options.append('Piper (local)')
            if self.espeak_enabled:
                tts_options.append('eSpeak (local)')
        else:
            tts_options.append('Client-side (Kokoro)')
        
        return {
            'name': self.name,
            'type': 'local',
            'cost': 'free',
            'stt_options': ['Whisper CLI (local)', 'Groq Whisper (free cloud)'],
            'tts_options': tts_options,
            'note': 'Requires local installation of tools' if not self.client_tts_enabled else 'Client-side TTS enabled'
        }
