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
"""Utility for splitting text into chunks without breaking sentences."""

def split_text_into_chunks(doc, max_chunk_size=4096):
    """
    Split a spaCy Doc into chunks without breaking sentences.

    This function takes a spaCy Doc object and splits it into smaller text
    chunks, ensuring no sentence is broken across chunks. Each chunk's size does
    not exceed the specified maximum number of characters.

    Args:
      doc (spacy.tokens.Doc):
        The spaCy Doc object containing the text to split.
      max_chunk_size (int):
        The maximum size of each chunk in characters.

    Returns:
      List[str]:
        A list of text chunks, each no longer than `max_chunk_size` characters.

    Raises:
      ValueError:
        If any sentence in the doc exceeds the maximum chunk size.
    """
    chunks = []
    current_chunk = ''

    for sent in doc.sents:
        sentence = sent.text.strip()
        # Check if adding the next sentence would exceed the max chunk size
        if len(current_chunk) + len(sentence) + 1 <= max_chunk_size:
            if current_chunk:
                current_chunk += ' ' + sentence
            else:
                current_chunk = sentence
        else:
            # Start a new chunk
            chunks.append(current_chunk)
            current_chunk = sentence

    # Add any remaining text as the last chunk
    if current_chunk:
        chunks.append(current_chunk)

    return chunks
