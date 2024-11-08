"""Convert a text file into an M4A audio file using the LongReader APIs."""
import argparse
import os
import random
import warnings

import ffmpeg
import trio
from loguru import logger
from spacy import load as spacy_load
import soundfile as sf

from longreader import long_read


parser = argparse.ArgumentParser(
    prog='ReadToM4A',
    description=(
        'Converts a text file to an M4A file using 3rd-party language models, '
        'text-to-speech, and ffmpeg.'
    ),
    epilog='Copyright © 2024 Herbert F Gilman. All rights reserved.'
)
parser.add_argument(
    'input',
    type=str,
    help='Input text file to be converted to M4A'
)
parser.add_argument(
    'output',
    type=str,
    help='Output M4A file'
)
parser.add_argument(
    '--voice',
    type=str,
    required=False,
    default='alloy',
    help='OpenAI voice to use'
)


async def main(args):
    """Convert a text file to an M4A audio file using the LongReader APIs.

    This function reads the input text file, processes it to generate speech
    audio, and writes the output to an M4A file using FFmpeg.

    Args:
      args (argparse.Namespace):
        Parsed command-line arguments containing input and output paths, and
        optional voice selection.

    Returns:
      None

    Raises:
      ValueError:
        If the input or output file extensions are incorrect.
      FileNotFoundError:
        If the input file does not exist.
      Exception:
        If any step of the audio processing or file operations fails.
    """
    if not args.output.endswith('.m4a'):
        raise ValueError('Output file must have .m4a extension')
    if not args.input.endswith('.txt'):
        raise ValueError('Input file must have .txt extension')

    logger.info('Reading {}', args.input)
    with open(args.input, 'r', encoding='utf-8') as f:
        text = f.read()
    logger.info('Loading spaCy model')
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        spacy_model = spacy_load('en_core_web_trf')

    resulting_audio = await long_read(text, args.voice, spacy_model)

    logger.info('Writing to temporary file and converting to m4a')
    temp_file = str(random.randbytes(10)) + '.wav'
    sf.write(temp_file, resulting_audio, 24000, subtype='PCM_16')
    ffmpeg.input(temp_file).output(args.output, loglevel='quiet').run()

    logger.info('Conversion complete, deleting temporary file')
    os.remove(temp_file)

    logger.info('Done')


if __name__ == '__main__':
    args_in = parser.parse_args()
    trio.run(main, args_in)
