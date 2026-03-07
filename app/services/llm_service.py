import os
from typing import List, Dict, Any, Optional, Callable
import logging

from .llm_providers import (
    OpenAIProvider,
    OllamaProvider,
    LMStudioProvider,
    GroqProvider,
    HuggingFaceProvider
)

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        self.provider = self.initialize_provider()
        self.default_max_tokens = 1000
        
        logger.info(f'LLM Provider initialized: {self.provider.name}')
        logger.info(f'Model info: {self.provider.get_model_info()}')

    def initialize_provider(self):
        provider_type = os.getenv('LLM_PROVIDER', 'ollama').lower()
        
        providers = {
            'openai': OpenAIProvider,
            'ollama': OllamaProvider,
            'lmstudio': LMStudioProvider,
            'groq': GroqProvider,
            'huggingface': HuggingFaceProvider
        }

        provider_class = providers.get(provider_type)
        
        if not provider_class:
            logger.warning(f'Unknown provider: {provider_type}, falling back to Ollama')
            return OllamaProvider()

        return provider_class()

    async def generate_completion(
        self,
        messages: List[Dict[str, str]],
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        if options is None:
            options = {}
        
        try:
            options['max_tokens'] = options.get('max_tokens', self.default_max_tokens)
            content = await self.provider.generate_completion(messages, options)
            logger.info(f'LLM completion generated: {content[:100]}...')
            return content
        except Exception as error:
            logger.error(f'Error generating LLM completion: {error}')
            raise

    async def generate_streaming_completion(
        self,
        messages: List[Dict[str, str]],
        options: Optional[Dict[str, Any]] = None,
        on_chunk: Optional[Callable[[str], None]] = None
    ) -> str:
        if options is None:
            options = {}
        
        try:
            options['max_tokens'] = options.get('max_tokens', self.default_max_tokens)
            full_content = await self.provider.generate_streaming_completion(
                messages, options, on_chunk
            )
            logger.info(f'Streaming completion generated: {full_content[:100]}...')
            return full_content
        except Exception as error:
            logger.error(f'Error generating streaming completion: {error}')
            raise

    async def generate_response(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        if conversation_history is None:
            conversation_history = []
        if options is None:
            options = {}
        
        try:
            messages = [{'role': 'system', 'content': system_prompt}]

            if conversation_history:
                messages.extend([
                    {'role': msg['role'], 'content': msg['content']}
                    for msg in conversation_history
                ])

            messages.append({'role': 'user', 'content': user_message})

            return await self.generate_completion(messages, options)
        except Exception as error:
            logger.error(f'Error generating response: {error}')
            raise

    async def generate_streaming_response(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        on_chunk: Optional[Callable[[str], None]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        if conversation_history is None:
            conversation_history = []
        if options is None:
            options = {}
        
        try:
            messages = [{'role': 'system', 'content': system_prompt}]

            if conversation_history:
                messages.extend([
                    {'role': msg['role'], 'content': msg['content']}
                    for msg in conversation_history
                ])

            messages.append({'role': 'user', 'content': user_message})

            return await self.generate_streaming_completion(messages, options, on_chunk)
        except Exception as error:
            logger.error(f'Error generating streaming response: {error}')
            raise

    async def function_call(
        self,
        messages: List[Dict[str, str]],
        functions: List[Dict[str, Any]],
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        if options is None:
            options = {}
        
        logger.warning('Function calling may not be supported by all providers')
        
        if self.provider.name == 'OpenAI':
            try:
                response = await self.provider.client.chat.completions.create(
                    model=options.get('model', self.provider.model),
                    messages=messages,
                    functions=functions,
                    function_call=options.get('function_call', 'auto'),
                    temperature=options.get('temperature', 0.7),
                    max_tokens=options.get('max_tokens', self.default_max_tokens)
                )

                message = response.choices[0].message

                if message.function_call:
                    import json
                    return {
                        'type': 'function_call',
                        'name': message.function_call.name,
                        'arguments': json.loads(message.function_call.arguments)
                    }

                return {
                    'type': 'message',
                    'content': message.content
                }
            except Exception as error:
                logger.error(f'Error in function call: {error}')
                raise
        
        return {
            'type': 'message',
            'content': await self.generate_completion(messages, options)
        }

    async def embed_text(self, text: str) -> Optional[List[float]]:
        if self.provider.name == 'OpenAI':
            try:
                response = await self.provider.client.embeddings.create(
                    model='text-embedding-ada-002',
                    input=text
                )
                return response.data[0].embedding
            except Exception as error:
                logger.error(f'Error generating embedding: {error}')
                raise
        
        logger.warning('Embeddings not supported by current provider')
        return None

    def validate_api_key(self) -> bool:
        return self.provider.validate_config()

    def get_provider_info(self) -> Dict[str, Any]:
        return self.provider.get_model_info()
