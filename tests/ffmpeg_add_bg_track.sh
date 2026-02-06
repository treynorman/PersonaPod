#!/bin/bash

# --- Configuration ---
TTS_FILE="tts_output.wav"
MUSIC_FILE="kmart-radio.mp3"
OUTPUT_FILE="output_with_overlay.wav"
TTS_DELAY_MS=12000
FADE_DURATION_S=5
FADE_OFFSET_S=3

# --- 1. Get the duration of the TTS file in seconds ---
TTS_DURATION=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$TTS_FILE")

# --- 2. Calculate timings in seconds ---
TTS_DELAY_S=$(echo "scale=3; $TTS_DELAY_MS / 1000" | bc)
FADE_START_TIME=$(echo "$TTS_DELAY_S + $TTS_DURATION - $FADE_OFFSET_S" | bc)

# --- 3. Calculate the total desired output duration ---
# This is the time from the start until the TTS file finishes playing.
TOTAL_DURATION=$(echo "$TTS_DELAY_S + $TTS_DURATION + $FADE_DURATION_S - $FADE_OFFSET_S"| bc)

echo "TTS Duration: $TTS_DURATION seconds"
echo "Music will start fading out at: $FADE_START_TIME seconds"
echo "Total output duration will be: $TOTAL_DURATION seconds"

# --- 4. Run the ffmpeg command ---
# Note: Input 0 is the music file, and Input 1 is the TTS file.
ffmpeg \
    -i "$MUSIC_FILE" \
    -i "$TTS_FILE" \
    -filter_complex \
"[0:a]afade=t=out:st=${FADE_START_TIME}:d=${FADE_DURATION_S}[faded_music]; \
 [1:a]pan=stereo|c0<c0|c1<c0,adelay=${TTS_DELAY_MS}|${TTS_DELAY_MS}[delayed_tts]; \
 [faded_music][delayed_tts]amix=inputs=2:normalize=0[mixed_audio]; \
 [mixed_audio]atrim=end=${TOTAL_DURATION}[out]" \
    -map "[out]" \
    -c:a pcm_s16le \
    -ac 2 \
    -ar 44100 \
    "$OUTPUT_FILE"

echo "Processing complete. Output saved to $OUTPUT_FILE"