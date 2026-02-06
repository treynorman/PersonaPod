import os, re, requests, shutil
from pathlib import Path
from datetime import datetime, timezone
import subprocess

from utils.cloud import *
from utils.news import NewsStory,fetch_rss_news_stories
from utils.container_management import *
from utils.llm import *
from utils.tts import *

import config as c

def create_episode(character_system_prompt, character_voice_ref, episode_image, title, bg_track=None, tts_start_delay_ms=None, fade_duration_s=None):
    """
    Creates a new podcast episode from scratch and uploads it to the cloud.
    Podcast RSS feed is pulled and updated with an entry for the new episode.
    Adding a background track is OPTIONAL and configurable.

    Args:
        character_system_prompt (str): System prompt defining character personality.
        character_voice_ref (str): Path to voice sample for text-to-speech (TTS).
        episode_image (str): Path to episode image on remote storage, relative to cloud repo base URL.
        title (str): Episode title. Current date is prepended.
    Optional:
        bg_track (str): Podcast background track filename.
        tts_start_delay_ms (int): Wait time (ms) to play background track before voice starts.
        fade_duration_s (int): Fade out duration (s) for background track when longer than voice track.
    """

    # Fetch list of news stories from a public news feed
    news_stories = fetch_rss_news_stories(c.RSS_NEWS_FEED, int(c.TOP_N_STORIES))
    
    stop_all_containers(c.EXCLUDED_CONTAINERS)
    start_container(c.CONTAINER_LLM, int(c.BOOT_WAIT_LLM))

    # Add character summary to each news story
    for story in news_stories:
        story.summary_character = llama_cpp_summarize_text(
            character_system_prompt,
            c.SUMMARY_CHARACTER,
            story.content
        )

    # # Add normal summary to each news story
    # for story in news_stories:
    #     story.summary_normal = llama_cpp_summarize_text(
    #         c.SYSTEM_NORMAL,
    #         c.SUMMARY_NORMAL,
    #         story.content
    #     )

    # Build news segment from character summaries in one prompt
    news_segment = llama_cpp_news_segment_concurrent(
        character_system_prompt,
        c.NEWS_SEGMENT_FULL,
        news_stories,
        "character"
    )

    # # Build news segment from character summaries iteratively and stitch
    # news_segment = llama_cpp_news_segment_iterative(
    #     character_system_prompt,
    #     c.NEWS_SEGMENT_INTRO,
    #     c.NEWS_SEGMENT_OUTRO,
    #     news_stories
    # )
    
    print(news_segment)

    stop_container(c.CONTAINER_LLM)
    start_container(c.CONTAINER_TTS, int(c.BOOT_WAIT_TTS))

    # Generate podcast audio
    output_wav = maskgct_generate_audio(
        c.MASKGCT_VOICES_DIR,
        character_voice_ref,
        c.MASKGCT_TIMESTEPS,
        news_segment
    )

    stop_container(c.CONTAINER_TTS)

    if bg_track:
        output_wav = add_background_track(output_wav, bg_track, tts_start_delay_ms,fade_duration_s)
    
    # Create MP3 from generated WAV in variable bitrate V2 quality
    output_mp3 = wav_to_mp3(output_wav, "v2")

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    episode_title = timestamp + " " + title
    episode_image_full_url = c.PODCAST_CLOUD_REPO + episode_image
    update_podcast(output_mp3, episode_title, episode_image_full_url)

def update_podcast(input_mp3, episode_title, episode_image_full_url):
    """
    Update podcast on Cloudflare R2 bucket.

    Args:
        input_mp3 (str): Absolute path to the podcast MP3 file.
        episode_title (str): title tag assigned to the podcast episode in RSS feed.
        episode_image_full_url (str): itunes:image tag assigned to the episode in RSS feed.
    """

    print(f"Updating podcast on Cloudflare...")

    # Ensure the input file exists
    input_path = Path(input_mp3)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_mp3}")

    # Get the duration of the input MP3
    episode_duration = get_audio_duration(input_mp3)
    
    # Copy the input MP3 to podcast assets directory and rename with epsiode title
    new_filename = episode_title + " " + str(episode_duration) + "s.mp3"
    podcast_mp3 = os.path.join(c.PODCAST_ASSETS_DIRECTORY, new_filename)
    shutil.copy2(input_mp3, podcast_mp3)

    episode_url = upload_to_s3(podcast_mp3)

    rss_tree = sync_rss_feed(episode_url, episode_title, episode_duration, episode_image_full_url)
    upload_rss_feed(rss_tree)

def add_background_track(tts_file, bg_track, tts_start_delay_ms, fade_duration_s):
    """
    Mixes a TTS audio file with a background track file,
    applying a fade-out to the background track.

    Background track starts at the beginning.
    TTS audio is delayed by tts_start_delay_ms.
    Background track fades out for fade_duration_s, starting at a time
    calculated from total length of merged audio files and offsets.

    Args:
        tts_file (str): Path to the mono TTS WAV file.
        bg_track (str): Background track filename.
        output_file (str): Path to save the final mixed WAV file.
        tts_start_delay_ms (int): Delay in milliseconds before TTS starts.
        fade_duration_s (int): Duration of music fade-out in seconds, starting from TTS end.

    Returns:
        str: Output WAV file path (absolute path).
    """

    bg_track_path = os.path.join(c.BG_TRACKS_DIR, bg_track)
    if not os.path.exists(bg_track_path):
        raise FileNotFoundError(f"Background track file not found: {bg_track_path}")
    
    if not tts_start_delay_ms: tts_start_delay_ms = 0
    if not fade_duration_s or fade_duration_s < 0: fade_duration_s = 0

    tts_duration_s = get_audio_duration(tts_file)

    # Ensure the input file exists
    tts_path = Path(tts_file)
    if not tts_path.exists():
        raise FileNotFoundError(f"TTS file not found: {tts_file}")

    # Define output file path and remove any existing file with same name
    # ffmpeg cannot overwrite existing files
    output_path = tts_path.parent / (tts_path.stem + '_bg_music' + tts_path.suffix)
    if output_path.exists():
        os.remove(output_path)

    # Calculate timings in seconds
    tts_delay_s = tts_start_delay_ms / 1000.0
    fade_start_time = tts_delay_s + tts_duration_s
    total_duration = tts_delay_s + tts_duration_s + fade_duration_s

    # Pad total length of merged audio when fade duration is 0 seconds,
    # otherwise final milliseconds of TTS audio will be truncated
    if fade_duration_s < 1: total_duration += 1

    # Construct ffmpeg complex filter for merging audio
    filter_complex = (
        f"[0:a]afade=t=out:st={fade_start_time}:d={fade_duration_s}[faded_music];"
        f" [1:a]pan=stereo|c0<c0|c1<c0,adelay={tts_start_delay_ms}|{tts_start_delay_ms}[delayed_tts];"
        f" [faded_music][delayed_tts]amix=inputs=2:normalize=0[mixed_audio];"
        f" [mixed_audio]atrim=end={total_duration}[out]"
    )

    command = [
        'ffmpeg',
        '-i', bg_track_path,
        '-i', tts_file,
        '-filter_complex', filter_complex,
        '-map', '[out]',
        '-c:a', 'pcm_s16le',
        '-ac', '2',
        '-ar', '44100',
        '-y', # Overwrite output file if it exists
        str(output_path)
    ]
    
    print("\nAdding background music...")

    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running ffmpeg command: {e}", file=sys.stderr)
        print(f"FFmpeg Stderr:\n---\n{e.stderr}\n---", file=sys.stderr)

    return str(output_path.resolve())

def get_audio_duration(input_audio):
    """
    Gets the duration of an audio file.

    Args:
        input_audio (str): Path to the audio file.
    
    Returns:
        int: Audio track duration in seconds.
    """

    # Ensure the input file exists
    input_path = Path(input_audio)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_audio}")

    # Construct ffmpeg command to get duration
    ffmpeg_cmd = [
        "ffmpeg",
        "-i", str(input_path),  # Input file
        "-f", "null",           # Output format (null to suppress output)
        "-"                     # Output to stdout
    ]

    # Run ffmpeg command and capture stderr
    try:
        result = subprocess.run(
            ffmpeg_cmd,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"ffmpeg command failed: {e.stderr}")

    # Parse the duration from ffmpeg's stderr output
    for line in result.stderr.splitlines():
        if "Duration" in line:
            # Extract the duration string (e.g., "00:01:23.45")
            duration_str = line.split("Duration: ")[1].split(",")[0].strip()
            # Convert to seconds
            hours, minutes, seconds = map(float, duration_str.split(":"))
            duration_seconds = hours * 3600 + minutes * 60 + seconds
            return int(duration_seconds)

    # If duration not found, raise an error
    raise RuntimeError("Could not determine duration from ffmpeg output.")

def wav_to_mp3(input_wav, quality):
    """
    Convert WAV file to MP3 file with a specified variable bit rate (VBR)
    quality level or a constant bit rate (CBR). using ffmpeg.
    Loudness normalization is also applied.

    Args:
        input_wav (str): Path to the WAV file.
        quality (str): Supports: v0, v2, 192k, 320k

    Returns:
        str: Output MP3 file path (absolute path).
    """

    # Validate MP3 quality level
    valid_qualities = {"v0", "v2", "192k", "320k"}
    if quality not in valid_qualities:
        raise ValueError(f"Invalid quality level: {quality}. Supported values: {valid_qualities}")

    # Ensure the input file exists
    input_path = Path(input_wav)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_wav}")

    # Define output file path and remove any existing file with same name
    # ffmpeg cannot overwrite existing files
    output_mp3 = input_path.with_suffix(".mp3")
    if output_mp3.exists():
        os.remove(output_mp3)

    # Construct ffmpeg command
    if quality.startswith("v"):
        # Variable Bit Rate (VBR)
        ffmpeg_cmd = [
            "ffmpeg",
            "-i", str(input_path),  # Input file
            "-codec:a", "libmp3lame",  # Use LAME MP3 codec
            "-q:a", quality[1:],  # VBR quality (0 = highest, 9 = lowest)
            str(output_mp3)  # Output file
        ]
    else:
        # Constant Bit Rate (CBR)
        ffmpeg_cmd = [
            "ffmpeg",
            "-i", str(input_path),  # Input file
            "-codec:a", "libmp3lame",  # Use LAME MP3 codec
            "-b:a", quality,  # CBR bitrate (e.g., 192k, 320k)
            str(output_mp3)  # Output file
        ]

    # Run ffmpeg command
    try:
        subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"ffmpeg command failed: {e.stderr.decode()}")

    # Return absolute path to the output MP3 file
    print(f"WAV to MP3 ({quality}): {output_mp3.resolve()}")
    return str(output_mp3.resolve())