import os
from typing import List, Dict, Any, Optional, Callable
import aiohttp
import asyncio
import logging

logger = logging.getLogger(__name__)


class HuggingFaceProvider:
    def __init__(self):
        self.api_key = os.getenv('HUGGINGFACE_API_KEY')
        self.model = os.getenv('HUGGINGFACE_MODEL', 'mistralai/Mistral-7B-Instruct-v0.2')
        self.base_url = 'https://api-inference.huggingface.co/models'
        self.name = 'Hugging Face'

    async def generate_completion(
        self,
        messages: List[Dict[str, str]],
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        if options is None:
            options = {}
        
        try:
            prompt = self.format_messages(messages)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f'{self.base_url}/{options.get("model", self.model)}',
                    json={
                        'inputs': prompt,
                        'parameters': {
                            'temperature': options.get('temperature', 0.7),
                            'max_new_tokens': options.get('max_tokens', 1000),
                            'return_full_text': False
                        }
                    },
                    headers={
                        'Authorization': f'Bearer {self.api_key}',
                        'Content-Type': 'application/json'
                    }
                ) as response:
                    data = await response.json()
                    
                    if response.status == 503:
                        raise Exception('Model is loading. Please wait a moment and try again.')
                    
                    if isinstance(data, list):
                        return data[0]['generated_text']
                    return data.get('generated_text', data[0].get('generated_text', ''))
        except Exception as error:
            logger.error(f'Hugging Face completion error: {error}')
            raise

    async def generate_streaming_completion(
        self,
        messages: List[Dict[str, str]],
        options: Optional[Dict[str, Any]] = None,
        on_chunk: Optional[Callable[[str], None]] = None
    ) -> str:
        result = await self.generate_completion(messages, options)
        
        if on_chunk:
            words = result.split(' ')
            for word in words:
                on_chunk(word + ' ')
                await asyncio.sleep(0.05)
        
        return result

    def format_messages(self, messages: List[Dict[str, str]]) -> str:
        formatted = []
        for msg in messages:
            role = msg['role']
            content = msg['content']
            
            if role == 'system':
                formatted.append(f'<s>[INST] {content} [/INST]')
            elif role == 'user':
                formatted.append(f'<s>[INST] {content} [/INST]')
            elif role == 'assistant':
                formatted.append(f'{content}</s>')
            else:
                formatted.append(content)
        
        return '\n'.join(formatted)

    def validate_config(self) -> bool:
        return bool(self.api_key)

    def get_model_info(self) -> Dict[str, Any]:
        return {
            'provider': self.name,
            'model': self.model,
            'type': 'cloud',
            'cost': 'free (with limits)',
            'note': 'Models may need time to load on first request'
        }
