"""Use the OpenAI TTS API to generate speech."""


import os

import httpx
import orjson
from anyio import Semaphore
from loguru import logger


OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError('OPENAI_API_KEY is not set')


async def generate_speech(
        text: str,
        voice: str,
        client: httpx.AsyncClient,
        semaphore: Semaphore,
        chunk_no: int
) -> bytes:
    """Generate speech from text using the OpenAI TTS API."""
    if len(text) > 4096:
        raise ValueError('Text is too long to be processed by the OpenAI API')
    api_request = {
        'model': 'tts-1-hd',
        'input': text,
        'voice': voice,
        'response_format': 'pcm'
    }
    api_request_bytes = orjson.dumps(api_request)
    async with semaphore:
        logger.info('Sending chunk {} to TTS API', chunk_no)
        response = await client.request(
            method='POST',
            url='https://api.openai.com/v1/audio/speech',
            headers={
                'Authorization': f'Bearer {OPENAI_API_KEY}',
                'Content-Type': 'application/json'
            },
            data=api_request_bytes
        )
        response.raise_for_status()
        audio_bytes = response.content
        logger.info('TTS API returned chunk {}', chunk_no)
    return audio_bytes
