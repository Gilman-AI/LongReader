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
"""Convert long texts into speech audio using asynchronous processing."""

import io
from typing import Dict
import numpy as np
import pyrubberband as rb
import soundfile as sf
import httpx

from loguru import logger
from anyio import (
    create_memory_object_stream,
    create_task_group,
    sleep,
    Semaphore
)
from anyio.streams.memory import MemoryObjectSendStream
from spacy.language import Language as SpacyNLP

from multi_runner import create_dag_node
from httpx_anthropic import rewrite_for_tts
from httpx_openai import generate_speech
from split import split_text_into_chunks


async def get_audio(
    chunk: str,
    client: httpx.AsyncClient,
    ant_sem: Semaphore,
    oai_sem: Semaphore,
    send_to: MemoryObjectSendStream,
    chunk_no: int,
    voice: str
) -> None:
    """Process a text chunk and generate sped-up audio data.

    This function handles the processing of a single text chunk by rewriting it
    for TTS, generating speech audio using the OpenAI TTS API, speeding up the
    audio, and then sending it to the next stage in the pipeline.

    Args:
      chunk (str):
        The text chunk to process.
      client (httpx.AsyncClient):
        An asynchronous HTTP client for making requests.
      ant_sem (Semaphore):
        Semaphore to limit concurrent requests to the Anthropic API.
      oai_sem (Semaphore):
        Semaphore to limit concurrent requests to the OpenAI API.
      send_to (MemoryObjectSendStream):
        The send stream to pass the processed audio data.
      chunk_no (int):
        The chunk number for logging and tracking purposes.
      voice (str):
        The voice identifier to use for speech synthesis.

    Returns:
      None

    Raises:
      ValueError:
        If any step of the processing fails.
      httpx.HTTPStatusError:
        If any API response contains an HTTP error status.
    """
    for_read = await rewrite_for_tts(chunk, client, ant_sem, chunk_no)
    audio = await generate_speech(for_read, voice, client, oai_sem, chunk_no)

    logger.info('Speeding up chunk {}', chunk_no)
    # Use BytesIO to avoid saving to disk
    memory_file = io.BytesIO()
    memory_file.name = 'foobar.raw'
    memory_file.write(audio)
    memory_file.seek(0)
    with sf.SoundFile(
        memory_file, 'r', samplerate=24000,
        channels=1, subtype='PCM_16', endian='LITTLE'
    ) as sf_audio:
        sped_up = rb.time_stretch(
            sf_audio.read(), 24000, 1.43,
            rbargs={
                '--fine': '',
                '--no-transients': ''
            }
        )
    # Send the audio to the next node
    async with send_to:
        await send_to.send(('chunk_'+str(chunk_no), sped_up))


async def combine_audio_files(**kwargs) -> Dict[str, np.ndarray]:
    """Combine multiple audio chunks into a single audio array.

    This function accepts keyword arguments where each key corresponds to a
    chunk identifier (e.g., 'chunk_0') and each value is a NumPy array
    representing audio data. It sorts the chunks based on their identifiers and
    concatenates them into a single audio array.

    Args:
      **kwargs:
        Variable length keyword arguments representing audio chunks.

    Returns:
      Dict[str, np.ndarray]:
        A dictionary containing the combined audio under the key 'combined'.

    Raises:
      ValueError:
        If no audio chunks are provided.
    """
    logger.info('Combining audio files')
    audios = {
        int(k.split('_')[1]): v
        for k, v in kwargs.items()
        if k.startswith('chunk_')
    }
    sorted_audios = sorted(audios.items(), key=lambda x: x[0])
    sorted_audios = [v for _, v in sorted_audios]
    return {'combined': np.concatenate(sorted_audios, axis=0)}


async def long_read(
    text: str,
    voice: str,
    spacy_model: SpacyNLP
) -> np.ndarray:
    """Convert a long text into a combined audio array using TTS.

    This function processes a long text by splitting it into manageable chunks,
    processing each chunk asynchronously to generate speech audio, speeds up the
    audio, and combines all the audio chunks into a single NumPy array.

    Args:
      text (str):
        The full text to be converted into speech.
      voice (str):
        The voice identifier to use for speech synthesis.
      spacy_model (SpacyNLP):
        The spaCy language model used for text processing.

    Returns:
      np.ndarray:
        A NumPy array containing the combined audio data.

    Raises:
      ValueError:
        If text splitting or audio processing fails.
      httpx.HTTPStatusError:
        If any API response contains an HTTP error status.
    """
    async with httpx.AsyncClient() as client:
        logger.info('Splitting text into chunks')
        doc = spacy_model(text)
        chunks = split_text_into_chunks(doc, max_chunk_size=3800)

        num_chunks = len(chunks)
        dynamic_params = ['chunk_'+str(i) for i in range(num_chunks)]
        logger.info(f'Text has {num_chunks} chunks, starting to generate audio')

        final_send_stream, final_receive_stream = create_memory_object_stream()
        anthropic_semaphore, openai_semaphore = Semaphore(3), Semaphore(3)
        async with create_task_group() as tg:
            comb_wrapper, comb_send = create_dag_node(
                combine_audio_files, [final_send_stream], dynamic_params
            )
            for i, chunk in enumerate(chunks):
                dest_stream = (
                    comb_send if i == 0
                    else comb_send.clone()
                )
                tg.start_soon(
                    get_audio,
                    chunk,
                    client,
                    anthropic_semaphore,
                    openai_semaphore,
                    dest_stream,
                    i,
                    voice
                )
                await sleep(0.25)
            logger.info('All tasks queued, waiting for results')
            tg.start_soon(comb_wrapper)
            await sleep(0.25)
            async with final_receive_stream:
                _, combined_audio = await final_receive_stream.receive()
    logger.info('Audio files successfully combined')
    return combined_audio
