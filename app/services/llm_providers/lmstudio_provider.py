import os
from typing import List, Dict, Any, Optional, Callable
import aiohttp
import json
import logging

logger = logging.getLogger(__name__)


class LMStudioProvider:
    def __init__(self):
        self.base_url = os.getenv('LMSTUDIO_BASE_URL', 'http://localhost:1234/v1')
        self.model = os.getenv('LMSTUDIO_MODEL', 'local-model')
        self.name = 'LM Studio'

    async def generate_completion(
        self,
        messages: List[Dict[str, str]],
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        if options is None:
            options = {}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f'{self.base_url}/chat/completions',
                    json={
                        'model': options.get('model', self.model),
                        'messages': messages,
                        'temperature': options.get('temperature', 0.7),
                        'max_tokens': options.get('max_tokens', 1000),
                        'stream': False
                    }
                ) as response:
                    data = await response.json()
                    return data['choices'][0]['message']['content']
        except Exception as error:
            logger.error(f'LM Studio completion error: {error}')
            raise Exception(f'LM Studio error: {str(error)}. Is LM Studio running?')

    async def generate_streaming_completion(
        self,
        messages: List[Dict[str, str]],
        options: Optional[Dict[str, Any]] = None,
        on_chunk: Optional[Callable[[str], None]] = None
    ) -> str:
        if options is None:
            options = {}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f'{self.base_url}/chat/completions',
                    json={
                        'model': options.get('model', self.model),
                        'messages': messages,
                        'temperature': options.get('temperature', 0.7),
                        'max_tokens': options.get('max_tokens', 1000),
                        'stream': True
                    }
                ) as response:
                    full_content = ''
                    
                    async for line in response.content:
                        line_str = line.decode('utf-8').strip()
                        if line_str and line_str.startswith('data: '):
                            data_str = line_str.replace('data: ', '', 1)
                            if data_str == '[DONE]':
                                break
                            
                            try:
                                data = json.loads(data_str)
                                content = data.get('choices', [{}])[0].get('delta', {}).get('content', '')
                                if content:
                                    full_content += content
                                    if on_chunk:
                                        on_chunk(content)
                            except json.JSONDecodeError as err:
                                logger.error(f'Error parsing LM Studio stream: {err}')
                    
                    return full_content
        except Exception as error:
            logger.error(f'LM Studio streaming error: {error}')
            raise

    async def validate_config(self) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f'{self.base_url}/models',
                    timeout=aiohttp.ClientTimeout(total=3)
                ) as response:
                    return response.status == 200
        except Exception as error:
            logger.warning(f'LM Studio not available: {error}')
            return False

    def get_model_info(self) -> Dict[str, Any]:
        return {
            'provider': self.name,
            'model': self.model,
            'type': 'local',
            'cost': 'free',
            'base_url': self.base_url
        }
