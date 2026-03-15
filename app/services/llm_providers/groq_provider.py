import os
from typing import List, Dict, Any, Optional, Callable
from groq import AsyncGroq
import logging

logger = logging.getLogger(__name__)


class GroqProvider:
    def __init__(self):
        self.api_key = os.getenv('GROQ_API_KEY')
        self.client = AsyncGroq(api_key=self.api_key)
        self.model = os.getenv('GROQ_MODEL', 'llama-3.1-70b-versatile')
        self.name = 'Groq'

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
                max_tokens=options.get('max_tokens', 1000)
            )

            return response.choices[0].message.content
        except Exception as error:
            logger.error(f'Groq completion error: {error}')
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
            logger.error(f'Groq streaming error: {error}')
            raise

    def validate_config(self) -> bool:
        return bool(self.api_key)

    def get_model_info(self) -> Dict[str, Any]:
        return {
            'provider': self.name,
            'model': self.model,
            'type': 'cloud',
            'cost': 'free (with limits)'
        }
