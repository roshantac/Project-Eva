import os
from typing import List, Dict, Any, Optional, Callable
import aiohttp
import json
import logging

logger = logging.getLogger(__name__)


class OllamaProvider:
    def __init__(self):
        self.base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.model = os.getenv('OLLAMA_MODEL', 'llama3.1:8b')
        self.name = 'Ollama'

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
                    f'{self.base_url}/api/generate',
                    json={
                        'model': options.get('model', self.model),
                        'prompt': prompt,
                        'stream': False,
                        'options': {
                            'temperature': options.get('temperature', 0.7),
                            'num_predict': options.get('max_tokens', 1000),
                            'top_p': options.get('top_p', 1)
                        }
                    }
                ) as response:
                    data = await response.json()
                    return data['response']
        except Exception as error:
            logger.error(f'Ollama completion error: {error}')
            raise Exception(f'Ollama error: {str(error)}. Is Ollama running?')

    async def generate_streaming_completion(
        self,
        messages: List[Dict[str, str]],
        options: Optional[Dict[str, Any]] = None,
        on_chunk: Optional[Callable[[str], None]] = None
    ) -> str:
        if options is None:
            options = {}
        
        try:
            prompt = self.format_messages(messages)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f'{self.base_url}/api/generate',
                    json={
                        'model': options.get('model', self.model),
                        'prompt': prompt,
                        'stream': True,
                        'options': {
                            'temperature': options.get('temperature', 0.7),
                            'num_predict': options.get('max_tokens', 1000)
                        }
                    }
                ) as response:
                    full_content = ''
                    
                    async for line in response.content:
                        line_str = line.decode('utf-8').strip()
                        if line_str:
                            try:
                                data = json.loads(line_str)
                                if 'response' in data:
                                    full_content += data['response']
                                    if on_chunk:
                                        on_chunk(data['response'])
                                if data.get('done', False):
                                    break
                            except json.JSONDecodeError as err:
                                logger.error(f'Error parsing Ollama stream: {err}')
                    
                    return full_content
        except Exception as error:
            logger.error(f'Ollama streaming error: {error}')
            raise

    def format_messages(self, messages: List[Dict[str, str]]) -> str:
        formatted = []
        for msg in messages:
            role = msg['role']
            content = msg['content']
            
            if role == 'system':
                formatted.append(f'System: {content}')
            elif role == 'user':
                formatted.append(f'User: {content}')
            elif role == 'assistant':
                formatted.append(f'Assistant: {content}')
            else:
                formatted.append(content)
        
        return '\n\n'.join(formatted) + '\n\nAssistant:'

    async def validate_config(self) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f'{self.base_url}/api/tags',
                    timeout=aiohttp.ClientTimeout(total=3)
                ) as response:
                    return response.status == 200
        except Exception as error:
            logger.warning(f'Ollama not available: {error}')
            return False

    def get_model_info(self) -> Dict[str, Any]:
        return {
            'provider': self.name,
            'model': self.model,
            'type': 'local',
            'cost': 'free',
            'base_url': self.base_url
        }
