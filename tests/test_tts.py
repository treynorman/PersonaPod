import config as c
from utils.tts import *
from utils.container_management import *

"""
    Tests to break long texts into chunks small enough for TTS model to handle
    and to merge them into a single WAV file after saving short TTS outputs
    in a temporary directory.
"""

# Prints text chunks of a defined max length from long text sample
def test_tts_chunk(long_text):

    # Define maximum chunk length in number of characters
    max_length = 250
    chunks = get_chunks(long_text, max_length)
    
    for chunk in chunks:
        print(chunk + "\n")

# Prints the location of the TTS WAV output file created by chunking a long text 
# sample, generating audio files for each chunk with TTS model, then merging them
def test_tts_merge(long_text, voice):

    stop_all_containers(c.EXCLUDED_CONTAINERS)
    start_container(c.CONTAINER_TTS, int(c.BOOT_WAIT_TTS))

    output_wav = maskgct_generate_audio(
        c.MASKGCT_VOICES_DIR,
        voice,
        c.MASKGCT_TIMESTEPS,
        long_text
    )

    return output_wav