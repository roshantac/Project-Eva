"""
WebSocket handler for managing real-time communication with clients
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import socketio
from datetime import datetime

from app.config.constants import WebSocketEvents, CommunicationMode
from app.utils.helpers import sanitize_input, generate_session_id, validate_audio_chunk
from app.utils.logger import logger
from app.utils.conversation_logger import conversation_logger
from app.services.conversation_service import conversation_service
from app.services.llm_service import LLMService
from app.services.stt_service import STTService
from app.services.tts_service import TTSService
from app.services.audio_emotion_service import audio_emotion_service
from app.engines.emotion_engine import EmotionEngine
from app.engines.persona_engine import PersonaEngine
from app.engines.memory_engine import MemoryEngine
from app.engines.tool_engine import ToolEngine


class SessionData:
    """Data structure for active session"""
    
    def __init__(
        self,
        session_id: str,
        user_id: str,
        persona: str = 'friend',
        input_mode: str = CommunicationMode.TEXT.value,
        output_mode: str = CommunicationMode.TEXT.value
    ):
        self.session_id = session_id
        self.user_id = user_id
        self.persona = persona
        self.input_mode = input_mode
        self.output_mode = output_mode
        self.audio_disabled = False
        self.is_processing = False
        self.conversation_created = False


class SocketHandler:
    """Handler for WebSocket connections and events"""
    
    def __init__(
        self,
        sio: socketio.AsyncServer,
        llm_service: LLMService,
        stt_service: STTService,
        tts_service: TTSService,
        emotion_engine: EmotionEngine,
        persona_engine: PersonaEngine,
        memory_engine: MemoryEngine,
        tool_engine: ToolEngine
    ):
        self.sio = sio
        self.llm_service = llm_service
        self.stt_service = stt_service
        self.tts_service = tts_service
        self.emotion_engine = emotion_engine
        self.persona_engine = persona_engine
        self.memory_engine = memory_engine
        self.tool_engine = tool_engine
        
        self.active_sessions: Dict[str, SessionData] = {}
        self.audio_buffers: Dict[str, List[bytes]] = {}
        
        self.audio_enabled = self._check_audio_enabled()
        
        self._register_handlers()
    
    def _check_audio_enabled(self) -> bool:
        """Check if audio features are enabled"""
        # Check if audio is explicitly disabled
        audio_enabled = os.getenv('AUDIO_ENABLED', 'true').lower() == 'true'
        if not audio_enabled:
            return False
        
        # Check audio provider
        audio_provider = os.getenv('AUDIO_PROVIDER', 'local').lower()
        
        if audio_provider == 'openai':
            # OpenAI requires API key
            openai_key = os.getenv('OPENAI_API_KEY', '')
            return bool(openai_key and openai_key != 'your_openai_api_key_here')
        elif audio_provider == 'local':
            # Local audio is always available (uses whisper-cli + espeak)
            return True
        
        return False
    
    def _register_handlers(self):
        """Register all Socket.IO event handlers"""
        
        @self.sio.event
        async def connect(sid: str, environ: dict, auth: Optional[dict] = None):
            await self.handle_connection(sid, environ)
        
        @self.sio.event
        async def disconnect(sid: str):
            await self.handle_disconnect(sid)
        
        @self.sio.on(WebSocketEvents.USER_TEXT)
        async def on_user_text(sid: str, data: dict):
            await self.handle_user_text(sid, data)
        
        @self.sio.on(WebSocketEvents.USER_AUDIO_CHUNK)
        async def on_user_audio_chunk(sid: str, data: dict):
            await self.handle_user_audio_chunk(sid, data)
        
        @self.sio.on(WebSocketEvents.PERSONA_CHANGED)
        async def on_persona_changed(sid: str, data: dict):
            await self.handle_persona_change(sid, data)
        
        @self.sio.on(WebSocketEvents.MODE_CHANGED)
        async def on_mode_changed(sid: str, data: dict):
            await self.handle_mode_change(sid, data)
        
        @self.sio.on(WebSocketEvents.MEMORY_REQUEST)
        async def on_memory_request(sid: str, data: dict):
            await self.handle_memory_request(sid, data)
        
        @self.sio.on(WebSocketEvents.MEMORY_ADD)
        async def on_memory_add(sid: str, data: dict):
            await self.handle_memory_add(sid, data)
        
        @self.sio.on(WebSocketEvents.MEMORY_UPDATE)
        async def on_memory_update(sid: str, data: dict):
            await self.handle_memory_update(sid, data)
        
        @self.sio.on(WebSocketEvents.MEMORY_DELETE)
        async def on_memory_delete(sid: str, data: dict):
            await self.handle_memory_delete(sid, data)
        
        @self.sio.on(WebSocketEvents.STOP_AUDIO)
        async def on_stop_audio(sid: str):
            await self.handle_stop_audio(sid)
        
        @self.sio.on('CONVERSATIONS_REQUEST')
        async def on_conversations_request(sid: str, data: dict):
            await self.handle_conversations_request(sid, data)
        
        @self.sio.on('CONVERSATION_LOAD')
        async def on_conversation_load(sid: str, data: dict):
            await self.handle_conversation_load(sid, data)
        
        @self.sio.on('CONVERSATION_DELETE')
        async def on_conversation_delete(sid: str, data: dict):
            await self.handle_conversation_delete(sid, data)
    
    async def handle_connection(self, sid: str, environ: dict):
        """Handle new WebSocket connection"""
        try:
            query_string = environ.get('QUERY_STRING', '')
            query_params = dict(param.split('=') for param in query_string.split('&') if '=' in param)
            user_id = query_params.get('userId', 'anonymous')
            
            active_conversation = await conversation_service.get_active_conversation(user_id)
            
            session_id = None
            is_resumed = False
            
            if active_conversation and active_conversation.get('messages') and len(active_conversation['messages']) > 0:
                session_id = active_conversation['sessionId']
                is_resumed = True
                logger.info(f"Resuming conversation: {sid}, Session: {session_id}")
            else:
                session_id = generate_session_id()
                logger.info(f"New session: {sid}, Session: {session_id}")
            
            persona = active_conversation.get('persona', 'friend') if active_conversation else 'friend'
            
            session = SessionData(
                session_id=session_id,
                user_id=user_id,
                persona=persona,
                input_mode=CommunicationMode.TEXT.value,
                output_mode=CommunicationMode.TEXT.value
            )
            session.conversation_created = is_resumed
            
            self.active_sessions[sid] = session
            
            await self.memory_engine.initialize_session(session_id, user_id)
            
            await conversation_logger.log_session_start(session_id, user_id, persona)
            
            await self.sio.emit(
                WebSocketEvents.CONNECTION_ESTABLISHED,
                {
                    'sessionId': session_id,
                    'userId': user_id,
                    'message': 'Connected to Eva AI',
                    'isResumed': is_resumed,
                    'audioEnabled': self.audio_enabled,
                    'audioProvider': os.getenv('AUDIO_PROVIDER', 'local')
                },
                to=sid
            )
            
        except Exception as error:
            logger.error(f"Error handling connection: {error}")
            await self.sio.emit(
                WebSocketEvents.ERROR,
                {
                    'message': 'Failed to establish connection',
                    'error': str(error)
                },
                to=sid
            )
    
    async def handle_user_text(self, sid: str, data: dict):
        """Handle text message from user"""
        try:
            session = self.active_sessions.get(sid)
            if not session or session.is_processing:
                return
            
            session.is_processing = True
            await self.sio.emit(WebSocketEvents.PROCESSING_START, to=sid)
            
            user_message = sanitize_input(data.get('message', ''))
            
            logger.info('═══════════════════════════════════════════════════════')
            logger.info(f'💬 USER TEXT: "{user_message}"')
            logger.info('═══════════════════════════════════════════════════════')
            
            await conversation_logger.log_user_input(
                session.session_id,
                session.user_id,
                user_message,
                'text'
            )
            
            if not session.conversation_created:
                await conversation_service.create_conversation(
                    session.session_id,
                    session.user_id,
                    session.persona
                )
                session.conversation_created = True
            
            await conversation_service.add_message(
                session.session_id,
                'user',
                user_message,
                {'isTranscribed': False}
            )
            
            emotion_data = await self.emotion_engine.detect_emotion(user_message)
            await self.sio.emit(
                WebSocketEvents.EMOTION_DETECTED,
                emotion_data,
                to=sid
            )
            
            await self.memory_engine.add_message(
                session.session_id,
                'user',
                user_message,
                emotion_data.get('emotion', 'neutral'),
                emotion_data.get('sentiment', 'neutral')
            )
            
            tool_result = await self.tool_engine.detect_and_execute_tools(
                user_message,
                self.llm_service,
                session.user_id,
                sid
            )
            
            if tool_result.get('toolUsed'):
                await self.sio.emit(
                    WebSocketEvents.TOOL_USED,
                    {
                        'toolName': tool_result.get('toolName'),
                        'result': tool_result.get('result')
                    },
                    to=sid
                )
                
                await conversation_logger.log_tool_usage(
                    session.session_id,
                    tool_result.get('toolName'),
                    tool_result.get('result')
                )
            elif tool_result.get('error') and tool_result.get('message'):
                logger.info(f"Tool unavailable: {tool_result.get('message')}")
            
            contextual_message = user_message
            if tool_result.get('error') and tool_result.get('message'):
                contextual_message = f"{user_message}\n\n[Note: User asked about weather but the weather API is not configured. Please respond helpfully without weather data.]"
            
            response = await self.generate_response(
                session,
                contextual_message,
                emotion_data,
                tool_result
            )
            
            logger.info('───────────────────────────────────────────────────────')
            logger.info(f'🤖 EVA RESPONSE: "{response}"')
            logger.info(f'   Emotion: {emotion_data.get("emotion")} | Persona: {session.persona}')
            logger.info('───────────────────────────────────────────────────────')
            
            output_mode = 'voice' if session.output_mode == CommunicationMode.VOICE.value else 'text'
            await conversation_logger.log_bot_response(
                session.session_id,
                session.user_id,
                response,
                emotion_data.get('emotion', 'neutral'),
                session.persona,
                output_mode
            )
            
            await conversation_service.add_message(
                session.session_id,
                'assistant',
                response,
                {
                    'emotion': emotion_data.get('emotion'),
                    'persona': session.persona
                }
            )
            
            await self.sio.emit(
                WebSocketEvents.BOT_TEXT_RESPONSE,
                {
                    'text': response,
                    'emotion': emotion_data.get('emotion'),
                    'persona': session.persona
                },
                to=sid
            )
            
            await self.memory_engine.add_message(
                session.session_id,
                'assistant',
                response,
                emotion_data.get('emotion', 'neutral'),
                emotion_data.get('sentiment', 'neutral')
            )
            
            if session.output_mode == CommunicationMode.VOICE.value and not session.audio_disabled:
                await self.generate_and_stream_audio(sid, response, emotion_data.get('emotion', 'neutral'))
            
            if self.emotion_engine.should_save_as_memory(emotion_data):
                await self.memory_engine.analyze_and_save_important_moments(
                    session.session_id,
                    session.user_id
                )
            
            session.is_processing = False
            await self.sio.emit(WebSocketEvents.PROCESSING_END, to=sid)
            
        except Exception as error:
            logger.error(f"Error handling user text: {error}")
            await self.sio.emit(
                WebSocketEvents.ERROR,
                {
                    'message': 'Failed to process your message',
                    'error': str(error)
                },
                to=sid
            )
            session = self.active_sessions.get(sid)
            if session:
                session.is_processing = False
    
    async def handle_user_audio_chunk(self, sid: str, data: dict):
        """Handle audio chunk from user"""
        try:
            if not self.audio_enabled or not self.stt_service:
                await self.sio.emit(
                    WebSocketEvents.ERROR,
                    {
                        'message': 'Audio features are disabled. Voice input requires OpenAI API key.',
                        'error': 'Audio not enabled'
                    },
                    to=sid
                )
                return
            
            session = self.active_sessions.get(sid)
            if not session or session.audio_disabled:
                return
            
            audio_data = data.get('audio')
            if not audio_data:
                logger.warning('No audio data in chunk')
                return
            
            logger.debug(f'Received audio data type: {type(audio_data)}, length: {len(audio_data) if hasattr(audio_data, "__len__") else "N/A"}')
            
            if isinstance(audio_data, str):
                import base64
                try:
                    audio_buffer = base64.b64decode(audio_data)
                    logger.debug(f'Decoded base64 to {len(audio_buffer)} bytes')
                except Exception as e:
                    logger.warning(f'Failed to decode base64 audio: {e}')
                    return
            elif isinstance(audio_data, (bytes, bytearray)):
                audio_buffer = bytes(audio_data)
                logger.debug(f'Using bytes directly: {len(audio_buffer)} bytes')
            else:
                logger.warning(f'Invalid audio data type: {type(audio_data)}')
                return
            
            is_final = data.get('isFinal', False)
            
            if not validate_audio_chunk(audio_buffer, is_final):
                logger.warning(f'Invalid audio buffer received (size: {len(audio_buffer)}, isFinal: {is_final}, type: {type(audio_buffer)})')
                return
            
            if sid not in self.audio_buffers:
                self.audio_buffers[sid] = []
            
            self.audio_buffers[sid].append(audio_buffer)
            logger.debug(f'Audio chunk received: {len(audio_buffer)} bytes, isFinal: {is_final}, total chunks: {len(self.audio_buffers[sid])}')
            
            if is_final:
                total_size = sum(len(chunk) for chunk in self.audio_buffers[sid])
                logger.info(f'Processing complete audio buffer: {total_size} bytes from {len(self.audio_buffers[sid])} chunks')
                await self.process_audio_buffer(sid)
                
        except Exception as error:
            logger.error(f"Error handling audio chunk: {error}")
            await self.sio.emit(
                WebSocketEvents.ERROR,
                {
                    'message': 'Failed to process audio',
                    'error': str(error)
                },
                to=sid
            )
    
    async def process_audio_buffer(self, sid: str):
        """Process accumulated audio buffer"""
        try:
            session = self.active_sessions.get(sid)
            if not session:
                return
            
            if session.is_processing:
                return
            
            session.is_processing = True
            await self.sio.emit(WebSocketEvents.PROCESSING_START, to=sid)
            
            audio_chunks = self.audio_buffers.get(sid, [])
            if sid in self.audio_buffers:
                del self.audio_buffers[sid]
            
            if not audio_chunks:
                session.is_processing = False
                return
            
            # Calculate total audio size
            total_size = sum(len(chunk) for chunk in audio_chunks)
            
            # Validate minimum audio size (500 bytes minimum - very permissive)
            if total_size < 500:
                logger.warning(f'Audio buffer too small: {total_size} bytes. Need at least 500 bytes.')
                await self.sio.emit(
                    WebSocketEvents.ERROR,
                    {
                        'message': 'Recording too short or invalid. Please speak clearly for at least 2-3 seconds.',
                        'error': f'Audio size: {total_size} bytes (need at least 500 bytes)'
                    },
                    to=sid
                )
                session.is_processing = False
                return
            
            logger.info(f"Processing {len(audio_chunks)} audio chunks ({total_size} bytes)")
            start_time = datetime.now()
            
            transcription = await self.stt_service.transcribe_audio_stream(audio_chunks)
            
            duration = (datetime.now() - start_time).total_seconds() * 1000
            
            transcribed_text = (transcription.get('text') or '').strip()
            audio_file_path = transcription.get('audio_file_path')  # For emotion detection
            
            # Empty audio / no speech: don't add messages or generate response
            if not transcribed_text:
                logger.info('Empty transcription (no speech detected) - skipping')
                await self.sio.emit(
                    WebSocketEvents.TRANSCRIPTION_RESULT,
                    {'text': '', 'empty': True},
                    to=sid
                )
                session.is_processing = False
                await self.sio.emit(WebSocketEvents.PROCESSING_END, to=sid)
                return
            
            logger.info('═══════════════════════════════════════════════════════')
            logger.info(f'🎤 USER SPEECH (Audio → Text): "{transcribed_text}"')
            logger.info('═══════════════════════════════════════════════════════')
            
            await conversation_logger.log_user_input(
                session.session_id,
                session.user_id,
                transcribed_text,
                'voice'
            )
            
            if not session.conversation_created:
                await conversation_service.create_conversation(
                    session.session_id,
                    session.user_id,
                    session.persona
                )
                session.conversation_created = True
            
            await conversation_service.add_message(
                session.session_id,
                'user',
                transcribed_text,
                {'isTranscribed': True}
            )
            
            await self.sio.emit(
                WebSocketEvents.TRANSCRIPTION_RESULT,
                {'text': transcribed_text},
                to=sid
            )
            
            # Process the transcribed text (generate response)
            # Don't call handle_user_text as it would save the message again
            # Detect emotion from both text and audio (voice)
            audio_path_obj = Path(audio_file_path) if audio_file_path else None
            emotion_data = await self.emotion_engine.detect_emotion(transcribed_text, audio_path_obj)
            
            # Log if audio emotion was used
            if emotion_data.get('emotion_source') == 'audio':
                logger.info(f"🎤 Emotion from voice: {emotion_data['emotion']} (confidence: {emotion_data['confidence']:.2f})")
            
            await self.sio.emit(
                WebSocketEvents.EMOTION_DETECTED,
                emotion_data,
                to=sid
            )
            
            await self.memory_engine.add_message(
                session.session_id,
                'user',
                transcribed_text,
                emotion_data.get('emotion', 'neutral'),
                emotion_data.get('sentiment', 'neutral')
            )
            
            tool_result = await self.tool_engine.detect_and_execute_tools(
                transcribed_text,
                self.llm_service,
                session.user_id,
                sid
            )
            
            if tool_result.get('toolUsed'):
                await self.sio.emit(
                    WebSocketEvents.TOOL_USED,
                    {
                        'toolName': tool_result.get('toolName'),
                        'result': tool_result.get('result')
                    },
                    to=sid
                )
            
            contextual_message = transcribed_text
            if tool_result.get('error') and tool_result.get('message'):
                contextual_message = f"{transcribed_text}\n\n[Note: User asked about weather but the weather API is not configured. Please respond helpfully without weather data.]"
            
            response = await self.generate_response(
                session,
                contextual_message,
                emotion_data,
                tool_result
            )
            
            logger.info('───────────────────────────────────────────────────────')
            logger.info(f'🤖 EVA RESPONSE: "{response}"')
            logger.info(f'   Emotion: {emotion_data.get("emotion")} | Persona: {session.persona}')
            logger.info('───────────────────────────────────────────────────────')
            
            output_mode = 'voice' if session.output_mode == CommunicationMode.VOICE.value else 'text'
            await conversation_logger.log_bot_response(
                session.session_id,
                session.user_id,
                response,
                emotion_data.get('emotion', 'neutral'),
                session.persona,
                output_mode
            )
            
            await conversation_service.add_message(
                session.session_id,
                'assistant',
                response,
                {
                    'emotion': emotion_data.get('emotion'),
                    'persona': session.persona
                }
            )
            
            await self.sio.emit(
                WebSocketEvents.BOT_TEXT_RESPONSE,
                {
                    'text': response,
                    'emotion': emotion_data.get('emotion'),
                    'persona': session.persona
                },
                to=sid
            )
            
            await self.memory_engine.add_message(
                session.session_id,
                'assistant',
                response,
                emotion_data.get('emotion', 'neutral'),
                emotion_data.get('sentiment', 'neutral')
            )
            
            if output_mode == 'voice' and not session.audio_disabled:
                await self.generate_and_stream_audio(sid, response, emotion_data.get('emotion', 'neutral'))
            
            session.is_processing = False
            await self.sio.emit(WebSocketEvents.PROCESSING_END, to=sid)
            
        except Exception as error:
            logger.error(f"Error processing audio buffer: {error}")
            await self.sio.emit(
                WebSocketEvents.ERROR,
                {
                    'message': 'Failed to transcribe audio',
                    'error': str(error)
                },
                to=sid
            )
            session = self.active_sessions.get(sid)
            if session:
                session.is_processing = False
    
    async def generate_response(
        self,
        session: SessionData,
        user_message: str,
        emotion_data: Dict[str, Any],
        tool_result: Dict[str, Any]
    ) -> str:
        """Generate AI response based on context"""
        try:
            emotional_context = self.emotion_engine.generate_emotional_context(emotion_data)
            system_prompt = self.persona_engine.get_system_prompt(
                session.persona,
                emotional_context
            )
            
            conversation_history = await self.memory_engine.get_conversation_context(
                session.session_id,
                10
            )
            
            memory_context = await self.memory_engine.get_memory_context(
                session.user_id,
                3
            )
            
            contextual_message = user_message
            if tool_result and tool_result.get('toolUsed') and tool_result.get('result', {}).get('success'):
                tool_context = self.tool_engine.format_tool_result_for_context(tool_result['result'])
                contextual_message = f"{user_message}\n\n{tool_context}\n\nPlease incorporate this information naturally into your response."
            
            messages = [
                {'role': 'system', 'content': system_prompt + memory_context}
            ]
            
            if conversation_history:
                history_lines = conversation_history.split('\n')
                for line in history_lines:
                    if line.startswith('user:'):
                        messages.append({'role': 'user', 'content': line[5:].strip()})
                    elif line.startswith('assistant:'):
                        messages.append({'role': 'assistant', 'content': line[10:].strip()})
            
            messages.append({'role': 'user', 'content': contextual_message})
            
            response = await self.llm_service.generate_completion(
                messages,
                {
                    'temperature': 0.8,
                    'max_tokens': 500
                }
            )
            
            return response
            
        except Exception as error:
            logger.error(f"Error generating response: {error}")
            raise
    
    def clean_text_for_tts(self, text: str) -> str:
        """Clean text for better TTS pronunciation"""
        import re
        
        # Remove markdown formatting
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # Remove bold **text**
        text = re.sub(r'\*([^*]+)\*', r'\1', text)      # Remove italic *text*
        text = re.sub(r'__([^_]+)__', r'\1', text)      # Remove bold __text__
        text = re.sub(r'_([^_]+)_', r'\1', text)        # Remove italic _text_
        
        # Remove code blocks and inline code
        text = re.sub(r'```[^`]*```', '', text)         # Remove code blocks
        text = re.sub(r'`([^`]+)`', r'\1', text)        # Remove inline code
        
        # Remove URLs
        text = re.sub(r'http[s]?://\S+', '', text)
        
        # Replace multiple punctuation with single
        text = re.sub(r'\.{2,}', '.', text)             # Multiple dots to single
        text = re.sub(r'\!{2,}', '!', text)             # Multiple ! to single
        text = re.sub(r'\?{2,}', '?', text)             # Multiple ? to single
        
        # Remove special characters that sound bad in TTS
        text = re.sub(r'[#@$%^&+=<>{}[\]\\|~]', '', text)
        
        # Clean up extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    async def generate_and_stream_audio(self, sid: str, text: str, emotion: str):
        """Generate and stream audio response"""
        try:
            if not self.audio_enabled or not self.tts_service:
                logger.warning('Audio output disabled - TTS service not available')
                return
            
            # Clean text for better TTS pronunciation
            cleaned_text = self.clean_text_for_tts(text)
            
            if not cleaned_text.strip():
                logger.warning('Text is empty after cleaning, skipping audio generation')
                return
            
            logger.info(f"🔊 Generating audio for text: '{cleaned_text[:50]}...' with emotion: {emotion}")
            audio_buffer = await self.tts_service.generate_emotional_speech(cleaned_text, emotion)
            logger.info(f"✅ Audio generated: {len(audio_buffer)} bytes")
            
            # Convert bytes to base64 for reliable transmission over WebSocket
            import base64
            audio_base64 = base64.b64encode(audio_buffer).decode('utf-8')
            
            logger.info(f"📦 Sending complete audio: {len(audio_buffer)} bytes (base64: {len(audio_base64)} chars)")
            
            # Send the complete audio file as base64
            await self.sio.emit(
                WebSocketEvents.BOT_AUDIO_STREAM,
                {
                    'audio': audio_base64,
                    'isLast': True,
                    'format': 'base64'
                },
                to=sid
            )
            logger.info(f"✅ Audio sent to client {sid}")
                
        except Exception as error:
            logger.error(f"❌ Error generating audio: {error}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    async def handle_persona_change(self, sid: str, data: dict):
        """Handle persona change request"""
        try:
            session = self.active_sessions.get(sid)
            if not session:
                return
            
            new_persona = data.get('persona')
            if not new_persona:
                return
            
            self.persona_engine.set_persona(new_persona)
            session.persona = new_persona
            
            await self.memory_engine.update_persona(session.session_id, new_persona)
            
            logger.info(f"Persona changed to {new_persona} for session {session.session_id}")
            
        except Exception as error:
            logger.error(f"Error changing persona: {error}")
    
    async def handle_mode_change(self, sid: str, data: dict):
        """Handle communication mode change"""
        try:
            session = self.active_sessions.get(sid)
            if not session:
                return
            
            if 'inputMode' in data:
                session.input_mode = data['inputMode']
            
            if 'outputMode' in data:
                session.output_mode = data['outputMode']
            
            if 'audioDisabled' in data:
                session.audio_disabled = data['audioDisabled']
            
            logger.info(f"Mode changed for session {session.session_id}: "
                       f"inputMode={session.input_mode}, "
                       f"outputMode={session.output_mode}, "
                       f"audioDisabled={session.audio_disabled}")
            
        except Exception as error:
            logger.error(f"Error changing mode: {error}")
    
    async def handle_memory_request(self, sid: str, data: dict):
        """Handle memory retrieval request"""
        try:
            session = self.active_sessions.get(sid)
            if not session:
                return
            
            limit = data.get('limit', 50)
            memories = await self.memory_engine.get_long_term_memories(
                session.user_id,
                limit
            )
            
            await self.sio.emit(
                WebSocketEvents.MEMORY_DATA,
                {'memories': memories},
                to=sid
            )
            
        except Exception as error:
            logger.error(f"Error retrieving memories: {error}")
            await self.sio.emit(
                WebSocketEvents.ERROR,
                {
                    'message': 'Failed to retrieve memories',
                    'error': str(error)
                },
                to=sid
            )
    
    async def handle_memory_add(self, sid: str, data: dict):
        """Handle add memory request"""
        try:
            session = self.active_sessions.get(sid)
            if not session:
                return
            
            memory = await self.memory_engine.save_long_term_memory(
                session.session_id,
                session.user_id,
                data
            )
            
            await self.sio.emit(
                WebSocketEvents.MEMORY_UPDATED,
                {
                    'action': 'added',
                    'memory': memory
                },
                to=sid
            )
            
        except Exception as error:
            logger.error(f"Error adding memory: {error}")
            await self.sio.emit(
                WebSocketEvents.ERROR,
                {
                    'message': 'Failed to add memory',
                    'error': str(error)
                },
                to=sid
            )
    
    async def handle_memory_update(self, sid: str, data: dict):
        """Handle update memory request"""
        try:
            memory_id = data.get('memoryId')
            updates = data.get('updates', {})
            
            memory = await self.memory_engine.update_memory(memory_id, updates)
            
            await self.sio.emit(
                WebSocketEvents.MEMORY_UPDATED,
                {
                    'action': 'updated',
                    'memory': memory
                },
                to=sid
            )
            
        except Exception as error:
            logger.error(f"Error updating memory: {error}")
            await self.sio.emit(
                WebSocketEvents.ERROR,
                {
                    'message': 'Failed to update memory',
                    'error': str(error)
                },
                to=sid
            )
    
    async def handle_memory_delete(self, sid: str, data: dict):
        """Handle delete memory request"""
        try:
            memory_id = data.get('memoryId')
            
            await self.memory_engine.delete_memory(memory_id)
            
            await self.sio.emit(
                WebSocketEvents.MEMORY_UPDATED,
                {
                    'action': 'deleted',
                    'memoryId': memory_id
                },
                to=sid
            )
            
        except Exception as error:
            logger.error(f"Error deleting memory: {error}")
            await self.sio.emit(
                WebSocketEvents.ERROR,
                {
                    'message': 'Failed to delete memory',
                    'error': str(error)
                },
                to=sid
            )
    
    async def handle_stop_audio(self, sid: str):
        """Handle stop audio playback request"""
        logger.info(f"Audio stopped for socket {sid}")
    
    async def handle_conversations_request(self, sid: str, data: dict):
        """Handle request for conversation list"""
        try:
            session = self.active_sessions.get(sid)
            if not session:
                logger.warning('No session found for conversations request')
                await self.sio.emit(
                    'CONVERSATIONS_LIST',
                    {'conversations': []},
                    to=sid
                )
                return
            
            logger.info(f"Loading conversations for user: {session.user_id}")
            
            limit = data.get('limit', 50)
            conversations = await conversation_service.get_user_conversations(
                session.user_id,
                limit
            )
            
            logger.info(f"Found {len(conversations)} conversations")
            logger.info(f"Emitting CONVERSATIONS_LIST to socket {sid}")
            
            await self.sio.emit(
                'CONVERSATIONS_LIST',
                {'conversations': conversations},
                to=sid
            )
            
            logger.info('CONVERSATIONS_LIST emitted successfully')
            
        except Exception as error:
            logger.error(f"Error handling conversations request: {error}")
            await self.sio.emit(
                WebSocketEvents.ERROR,
                {
                    'message': 'Failed to load conversations',
                    'error': str(error)
                },
                to=sid
            )
    
    async def handle_conversation_load(self, sid: str, data: dict):
        """Handle load conversation request"""
        try:
            session = self.active_sessions.get(sid)
            if not session:
                return
            
            session_id = data.get('sessionId')
            if not session_id:
                return
            
            messages = await conversation_service.get_conversation_messages(session_id)
            
            await conversation_service.end_conversation(session.session_id)
            
            session.session_id = session_id
            
            await self.sio.emit(
                'CONVERSATION_LOADED',
                {
                    'sessionId': session_id,
                    'messages': messages
                },
                to=sid
            )
            
            logger.info(f"Loaded conversation: {session_id}")
            
        except Exception as error:
            logger.error(f"Error loading conversation: {error}")
            await self.sio.emit(
                WebSocketEvents.ERROR,
                {
                    'message': 'Failed to load conversation',
                    'error': str(error)
                },
                to=sid
            )
    
    async def handle_conversation_delete(self, sid: str, data: dict):
        """Handle delete conversation request"""
        try:
            session_id = data.get('sessionId')
            if not session_id:
                return
            
            await conversation_service.delete_conversation(session_id)
            
            await self.sio.emit(
                'CONVERSATION_DELETED',
                {'sessionId': session_id},
                to=sid
            )
            
            logger.info(f"Deleted conversation: {session_id}")
            
        except Exception as error:
            logger.error(f"Error deleting conversation: {error}")
            await self.sio.emit(
                WebSocketEvents.ERROR,
                {
                    'message': 'Failed to delete conversation',
                    'error': str(error)
                },
                to=sid
            )
    
    async def handle_disconnect(self, sid: str):
        """Handle client disconnect"""
        try:
            session = self.active_sessions.get(sid)
            if not session:
                return
            
            logger.info(f"Client disconnected: {sid}, Session: {session.session_id}")
            
            if session.conversation_created:
                conversation = await conversation_service.get_conversation(session.session_id)
                if conversation and conversation.get('messages') and len(conversation['messages']) > 0:
                    await conversation_service.end_conversation(session.session_id)
                else:
                    await conversation_service.delete_conversation(session.session_id)
                    logger.info(f"Deleted empty conversation: {session.session_id}")
            
            await conversation_logger.log_session_end(session.session_id, session.user_id)
            
            if sid in self.active_sessions:
                del self.active_sessions[sid]
            
            if sid in self.audio_buffers:
                del self.audio_buffers[sid]
                
        except Exception as error:
            logger.error(f"Error handling disconnect: {error}")
    
    def get_active_sessions_count(self) -> int:
        """Get count of active sessions"""
        return len(self.active_sessions)
