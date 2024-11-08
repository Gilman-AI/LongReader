"""Uses the old Claude 3.5 model to format text for speech synthesis."""

import os

import httpx
from loguru import logger
import orjson
from anyio import Semaphore


ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
if not ANTHROPIC_API_KEY:
    raise ValueError('ANTHROPIC_API_KEY is not set')


REWRITE_PROMPT = """Please generate a speech audio file from the following text by passing it to the `read_aloud` tool.

<text>
{text}
</text>"""


READ_ALOUD_TOOL = {
    "name": "read_aloud",
    "description": "Converts the provided text into an audio file suitable for text-to-speech systems. Before generating the audio file, you must process the text by removing any word wrapping, citations, footnotes, or any other interrupting content that would interfere with a natural reading flow. The processed text should be exactly the same as the original in terms of words and meaning but formatted without interruptions. Include the processed text in the 'processed_text' parameter of the tool input.",
    "input_schema": {
        "type": "object",
        "properties": {
            "processed_text": {
                "type": "string",
                "description": "The text to be read aloud, processed to remove any word wrapping, citations, or other interrupting content that would interfere with a Text-to-Speech system reading it as a human would."
            }
        },
        "required": ["processed_text"]
    }
}


async def rewrite_for_tts(
    text: str,
    client: httpx.AsyncClient,
    semaphore: Semaphore,
    chunk_no: int
) -> str:
    """Rewrite text for TTS."""
    api_request = {
        'model': 'claude-3-5-sonnet-20240620',
        'max_tokens': 8192,
        'messages': [
            {'role': 'user', 'content': REWRITE_PROMPT.format(text=text)}
        ],
        'temperature': 0.1,
        'tools': [READ_ALOUD_TOOL],
        'tool_choice': {'type': 'tool', 'name': 'read_aloud'}
    }
    api_request_bytes = orjson.dumps(api_request)
    async with semaphore:
        logger.info('Sending chunk {} to LLM', chunk_no)
        response = await client.request(
            method='POST',
            url='https://api.anthropic.com/v1/messages',
            headers={
                'anthropic-version': '2023-06-01',
                'x-api-key': ANTHROPIC_API_KEY,
                'Content-Type': 'application/json'
            },
            timeout=60.0,
            data=api_request_bytes
        )
        response.raise_for_status()
        response_json = response.content
        logger.info('LLM returned chunk {}', chunk_no)
    response_json = orjson.loads(response_json)
    try:
        return response_json['content'][0]['input']['processed_text']
    except KeyError as e:
        raise ValueError(
            f'Anthropic API returned unexpected response: {response_json}'
        ) from e
