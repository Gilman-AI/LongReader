# LongReader: OpenAI TTS Without Limits

**LongReader** is a collection of Python scripts and modules designed to convert long text files into high-quality M4A audio files. It leverages the power of the OpenAI Text-to-Speech API and the Anthropic API to preprocess text, generate natural-sounding speech, and handle long texts efficiently by processing them asynchronously in chunks.

## Features

- Converts `.txt` files to `.m4a` audio files.
- Utilizes asynchronous processing for efficient handling of long texts.
- Rewrites text for natural speech synthesis using the Anthropic API.
- Generates speech audio using the OpenAI Text-to-Speech API.
- Speeds up audio playback using `pyrubberband` for a more efficient listening experience.
- Handles text chunking without breaking sentences for seamless audio output.
- Provides configurable options, including voice selection.

## Requirements

- Python 3.8 or higher
- [OpenAI API Key](https://platform.openai.com/api-keys)
- [Anthropic API Key](https://console.anthropic.com/account/keys)
- [FFmpeg](https://ffmpeg.org/) (must be installed and added to your PATH)
- [spaCy](https://spacy.io/) language model `en_core_web_trf`

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/Gilman-AI/longreader.git
   cd longreader
   ```

2. **Set Up a Virtual Environment (Optional but Recommended)**

   ```bash
   python -m venv venv
   source venv/bin/activate        # On Windows use `venv\Scripts\activate`
   ```

3. **Install the Required Packages**

   ```bash
   pip install -r requirements.txt
   ```

4. **Download the spaCy Language Model**

   ```bash
   sh scripts/download_models.sh
   ```

5. **Ensure FFmpeg is Installed**

   - **Linux/macOS**: Install via package manager or download from [FFmpeg's website](https://ffmpeg.org/download.html).
   - **Windows**: Download the executable and add it to your PATH.

6. **Set Environment Variables**

   - **OpenAI API Key**

     ```bash
     export OPENAI_API_KEY='your-openai-api-key'
     ```

   - **Anthropic API Key**

     ```bash
     export ANTHROPIC_API_KEY='your-anthropic-api-key'
     ```

     *On Windows, use `set` instead of `export`.*

## Usage

The main script `ReadToM4A.py` is used to convert a text file into an M4A audio file.

```bash
python scripts/ReadToM4A.py [--voice VOICE] <input_file.txt> <output_file.m4a>
```

- `<input_file.txt>`: Path to the input text file.
- `<output_file.m4a>`: Path for the output M4A audio file.
- `--voice VOICE`: (Optional) Specify the OpenAI voice to use. Default is `'alloy'`.

### Example

```bash
python scripts/ReadToM4A.py --voice 'alloy' input.txt output.m4a
```

## Configuration

- **Voice Selection**: You can choose different voices offered by the OpenAI TTS API using the `--voice` option.
- **Concurrency Limits**: Adjust the semaphores in `longreader.py` to change the number of concurrent API requests.
  - `anthropic_semaphore = Semaphore(<desired_number>)`
  - `openai_semaphore = Semaphore(<desired_number>)`
- **spaCy Model**: The `en_core_web_trf` model is used for sentence splitting. It is the highest-quality native spaCy model, but also the largest and slowest. On slower machines, consider using the `en_core_web_sm` model instead.

## Examples

### Basic Conversion

Convert `article.txt` to `article.m4a` using the default voice:

```bash
python scripts/ReadToM4A.py article.txt article.m4a
```

### Using a Specific Voice

Use the `'onyx'` voice for conversion:

```bash
python scripts/ReadToM4A.py article.txt article.m4a --voice 'onyx'
```

### Adjusting Concurrency

To process more chunks concurrently, modify the semaphores in `longreader.py`:

```python
# longreader.py
anthropic_semaphore = Semaphore(5)   # Increase from 3 to 5
openai_semaphore = Semaphore(5)
```

### Adjusting the spaCy Model

To use the smaller `en_core_web_sm` model, change the `spacy_model` variable in `ReadToM4A.py`:

```python
spacy_model = spacy_load('en_core_web_sm')
```

You will need to download the `en_core_web_sm` model separately:

```bash
python -m spacy download en_core_web_sm
```

## Acknowledgements

**LongReader** utilizes several open-source packages and third-party tools. We thank the [Trio](https://github.com/python-trio/trio) community for developing this robust asynchronous framework. We acknowledge the contributions of Alex Grönholm and the [AnyIO](https://github.com/agronholm/anyio) developers. We thank Delgan for creating [Loguru](https://github.com/Delgan/loguru), making logging simpler and more pleasant. We acknowledge Explosion and the spaCy community for their work on [this powerful NLP library](https://github.com/explosion/spaCy), as well as the contributors of the pre-trained `en_core_web_trf` model. We thank the maintainers of [SoundFile](https://github.com/bastibe/python-soundfile). We acknowledge Erik de Castro Lopo for developing [libsndfile](http://www.mega-nerd.com/libsndfile/). We acknowledge the [NumPy](https://github.com/numpy/numpy) developers for their essential work in the scientific Python ecosystem. We thank Brian McFee for developing [PyRubberband](https://github.com/bmcfee/pyrubberband). We acknowledge Breakfast Quay and the developers of the [Rubber Band Library](https://breakfastquay.com/rubberband/). We thank Ilya Kulakov for developing [orjson](https://github.com/ijl/orjson). We acknowledge the Encode team for creating [HTTPX](https://github.com/encode/httpx). We acknowledge the [FFmpeg project](https://ffmpeg.org/) and its contributors. We thank OpenAI for providing the Text-to-Speech API and language models. We thank Anthropic for providing access to their language models. Finally, we acknowledge the [Python Software Foundation](https://www.python.org/) and express our gratitude to the Python community worldwide.

## License

Copyright (c) 2024 Herbert F Gilman. Licensed under the Apache License, Version 2.0. You may not use the files in this repository except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0, and a copy is included in [LICENSE](LICENSE). Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

See the [NOTICE](NOTICE) file for further copyright and licensing information.

This program calls the OpenAI API and the Anthropic API for machine-learning inference services. Use of these APIs is governed by their respective terms of service ([OpenAI](https://openai.com/policies/business-terms/), [Anthropic](https://www.anthropic.com/legal/commercial-terms)).
