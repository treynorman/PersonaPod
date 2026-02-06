import glob, os, shutil, time, wave
from gradio_client import Client, handle_file

import config as c

"""
Multiple retries are made if TTS API calls fail. This accounts
for uncertainty around the time required for the LLM container to boot.
The time to wait between retries (RETRY_INTERVAL) is given in seconds.
"""
MAX_RETRIES = 5
RETRY_INTERVAL = 2

OUTPUT_WAV_FILENAME = "tts_output.wav"

def maskgct_generate_audio(
    voices_dir: str,
    voice_ref: str,
    timesteps: str,
    input_text: str
) -> str:
    """
    Generate audio using MaskGCT Text-to-Speech.
    Multiple retries are made if API calls fail.

    Args:
        voices_dir (str): User-defined system prompt.
        voice_ref (str): User-defined summarization prompt.
        timesteps (str): Iterations used during TTS inference
        input_text (str): Text to convert to audio with TTS.

    Returns:
        str: Reference to output WAV file path (absolute path).
    """

    chunks = get_chunks(input_text, 250)

    # Check that path to TTS voice sample exists
    voice_path = os.path.join(voices_dir, voice_ref)
    if not os.path.exists(voice_path):
        raise FileNotFoundError(f"TTS voice reference file not found: {voice_path}")

    # Create or verify ./tmp directory exists for partial output WAVs & clear it
    os.makedirs("./tmp", exist_ok=True)
    [os.remove(f) for f in glob.glob('tmp/*') if os.path.isfile(f)]
    
    infiles = []
    for chunk in chunks:
        print(chunk)
        retries = 0
        # Try the API call multiple times after failure
        while retries < MAX_RETRIES:
            try:
                client = Client(c.MASKGCT_BASE_URL)
                result = client.predict(
                        prompt_wav=handle_file(voice_path),
                        target_text=chunk,
                        target_len=-1,
                        n_timesteps=int(timesteps),
                        api_name="/inference"
                )
                break # Exit retry loop on success
            except Exception as e:
                print(f"Attempt {retries + 1} failed: {e}")
                retries += 1
                if retries < MAX_RETRIES:
                    time.sleep(RETRY_INTERVAL)
                else:
                    raise Exception("Failed after maximum number of retries.")
                
        # Default location for result (MaskGCT API output) is /temp/gradio/...
        # Move it to ./tmp
        shutil.move(result, "./tmp")
        infiles.append("./tmp/" + result.split('/')[-1])
    
    # Create output WAV base filename
    output_wav = OUTPUT_WAV_FILENAME
    
    # Merge all WAVs from /tmp
    data= []
    for infile in infiles:
        w = wave.open(infile, 'rb')
        data.append( [w.getparams(), w.readframes(w.getnframes())] )
        w.close()
    output = wave.open(output_wav, 'wb')
    output.setparams(data[0][0])
    for i in range(len(data)):
        output.writeframes(data[i][1])
    output.close()
    
    # Remove all files in temporary file directory (indivi)
    [os.remove(f) for f in glob.glob('tmp/*') if os.path.isfile(f)]

    # Return absolute path to the output WAV file
    print(f"Merged WAV: {os.path.abspath(output_wav)}")
    return os.path.abspath(os.path.abspath(output_wav))

def get_chunks(
    input_text: str,
    max_length: int
) -> list[str]:
    """
    Chunk text into smaller units, suitable for Text-to-Speech model.
    Text is only split at predefined punctuation types.

    Args:
        input_text (str): Text to be split into smaller chunks.
        max_length (int): User-defined summarization prompt.

    Returns:
        list[str]: A list of all input_text chunks.
    """
    # Clean up input so TTS doesn't get confused
    input_text = input_text.replace("\n", " ").replace("+", " plus ").replace("—", ", ")
    
    start = 0
    while start < len(input_text):
        # If remaining text is shorter than max_length, yield it and break.
        if start + max_length >= len(input_text):
            yield input_text[start:]
            break

        # Valid punctuation for text splitting
        period = input_text.rfind('.', start, start + max_length + 1)
        comma = input_text.rfind(',', start, start + max_length + 1)
        question = input_text.rfind('?', start, start + max_length + 1)
        exclamation = input_text.rfind('!', start, start + max_length + 1)
        double_quote = input_text.rfind('"', start, start + max_length + 1)
        parenthesis = input_text.rfind(')', start, start + max_length + 1)
        colon = input_text.rfind(':', start, start + max_length + 1)
        semicolon = input_text.rfind(';', start, start + max_length + 1)
        space = input_text.rfind(' ', start, start + max_length + 1)
        
        # Get the last valid punctuation index
        split_index = max(period, comma, question, exclamation, double_quote, parenthesis, colon, semicolon)
        
        # If no valid punctuation is found, split at a space character
        if split_index == -1:
            split_index = space
        else:
            split_index += 1  # include the punctuation

        # Only yield non-empty chunks
        if split_index > start:
            yield input_text[start:split_index]
        start = split_index