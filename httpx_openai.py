# Copyright (c) 2024 Herbert F Gilman.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.
"""Generate speech audio using the OpenAI Text-to-Speech API."""

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
    """Generate speech audio data from text using the OpenAI Text-to-Speech API.

    This function sends a POST request to the OpenAI Text-to-Speech (TTS) API to
    generate audio data from the provided text input. It handles request
    throttling using a semaphore to limit the number of concurrent API calls.

    Args:
      text (str):
        The text to be converted into speech. Must not exceed 4096 characters.
      voice (str):
        The voice identifier to use for speech synthesis.
      client (httpx.AsyncClient):
        An asynchronous HTTP client for making requests.
      semaphore (Semaphore):
        A semaphore to limit the number of concurrent API requests.
      chunk_no (int):
        The chunk number for logging and tracking purposes.

    Returns:
      bytes:
        The raw audio data in PCM format returned by the TTS API.

    Raises:
      ValueError:
        If the input text exceeds the maximum allowed length.
      httpx.HTTPStatusError:
        If the TTS API response contains an HTTP error status.
    """
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
