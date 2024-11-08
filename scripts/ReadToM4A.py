import argparse
import os
import random
import warnings

import ffmpeg
import trio
from loguru import logger
from spacy import load as spacy_load

from longreader import long_read
import soundfile as sf


parser = argparse.ArgumentParser(
    prog='ReadToM4A',
    description='Convert a text file to an M4A file using LongReader APIs',
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
    if not args.output.endswith('.m4a'):
        raise ValueError('Output file must have .m4a extension')
    if not args.input.endswith('.txt'):
        raise ValueError('Input file must have .txt extension')

    logger.info(f'Reading {args.input}')
    with open(args.input, 'r') as f:
        text = f.read()
    logger.info(f'Loading spaCy model')
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
    args = parser.parse_args()
    trio.run(main, args)
