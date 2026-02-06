import config as c
from utils.podcast import *

"""
    Tests for final podcast audio creation
"""

# Get the duration of an audio file using ffmpeg
def test_get_audio_duration(input_audio):

    duration = str(get_audio_duration(input_audio))
    print(f"({duration} seconds) {input_audio}")

# Add background track to TTS output, requries paths to both WAV files
def test_add_bg_track(tts_output_file, background_track, tts_start_delay_ms, fade_duration_s):

    # Mixes a TTS audio file with a background track file, applies a fade-out
    # to the background track. Background track starts at the beginning.
    # TTS audio is delayed by tts_start_delay_ms.
    # Background track fades out for fade_duration_s.
   merged_audio_path = add_background_track(tts_output_file, background_track, tts_start_delay_ms, fade_duration_s)
   print(merged_audio_path)
   return merged_audio_path

# Convert WAV to MP3: supports v0, v2, 192k, & 320k compression
def test_mp3_conversion(input_audio):
    mp3_path = wav_to_mp3(input_audio, "v2")