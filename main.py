import config as c
from utils.podcast import create_episode

"""
How to create a new episode and add/update the podcast RSS feed:

utils.podcast.create_episode(
    character_system_prompt,
    character_voice_ref, 
    episode_image, title, 
    bg_track=None, tts_start_delay_ms=None, fade_duration_s=None)

Creates a new podcast episode from scratch and uploads it to the cloud.
Podcast RSS feed is pulled and updated with an entry for the new episode.
Adding a background track is optional and configurable.

Args:
    character_system_prompt (str): System prompt defining character personality.
    character_voice_ref (str): Path to voice sample for text-to-speech (TTS).
    episode_image (str): Path to episode image on remote storage, used in RSS feed.
    title (str): Episode title. Current date is prepended.
Optional:
    bg_track (str): Path to podcast episode background track.
    tts_start_delay_ms (int): Delay (ms) to play background track before voice starts.
    fade_duration_s (int): Fade out duration (s) for background track, applied after voice track ends.
"""

if __name__ == "__main__":

    create_episode(
        c.SYSTEM_CHARACTER_KMART_RADIO, 
        c.MASKGCT_VOICE_REF_KMART_RADIO, 
        c.PODCAST_EPISODE_IMAGE_URL_KMART_RADIO, "Kmart Radio News", 
        c.BG_TRACK_KMART_RADIO, 12000, 5)