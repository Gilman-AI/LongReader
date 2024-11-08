"""Function for text splitting."""

def split_text_into_chunks(doc, max_chunk_size=4096):
    """
    Splits a spaCy Doc into chunks of specified maximum size without breaking
    sentences.

    Args:
      doc (spacy.tokens.Doc): The spaCy Doc object containing the text.
      max_chunk_size (int): The maximum size of each chunk in characters.

    Returns:
      List[str]:
        A list of text chunks.
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
