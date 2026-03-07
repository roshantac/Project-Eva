import os
from typing import List, Dict, Any, Optional, Callable
from openai import AsyncOpenAI
import logging

logger = logging.getLogger(__name__)


class OpenAIProvider:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview')
        self.name = 'OpenAI'

    async def generate_completion(
        self, 
        messages: List[Dict[str, str]], 
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        if options is None:
            options = {}
        
        try:
            response = await self.client.chat.completions.create(
                model=options.get('model', self.model),
                messages=messages,
                temperature=options.get('temperature', 0.7),
                max_tokens=options.get('max_tokens', 1000),
                top_p=options.get('top_p', 1),
                frequency_penalty=options.get('frequency_penalty', 0),
                presence_penalty=options.get('presence_penalty', 0)
            )

            return response.choices[0].message.content
        except Exception as error:
            logger.error(f'OpenAI completion error: {error}')
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
            stream = await self.client.chat.completions.create(
                model=options.get('model', self.model),
                messages=messages,
                temperature=options.get('temperature', 0.7),
                max_tokens=options.get('max_tokens', 1000),
                stream=True
            )

            full_content = ''
            async for chunk in stream:
                content = chunk.choices[0].delta.content or ''
                if content:
                    full_content += content
                    if on_chunk:
                        on_chunk(content)

            return full_content
        except Exception as error:
            logger.error(f'OpenAI streaming error: {error}')
            raise

    def validate_config(self) -> bool:
        return bool(os.getenv('OPENAI_API_KEY'))

    def get_model_info(self) -> Dict[str, Any]:
        return {
            'provider': self.name,
            'model': self.model,
            'type': 'cloud',
            'cost': 'paid'
        }
