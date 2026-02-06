import config as c
from tests.test_news import *
from tests.test_cloud import *
from tests.test_container_management import *
from tests.test_llm import *
from tests.test_tts import *
from tests.test_podcast import *

if __name__ == "__main__":

    print("----- TEST NEWS FETCHING -----")
    # Test news article fetch
    article_link = "https://www.state.gov/releases/office-of-the-spokesperson/2026/02/joint-statement-on-the-inaugural-meeting-of-the-joint-steering-committee-of-the-u-s-drc-strategic-partnership-agreement/"
    test_news_article_fecth(article_link)

    # Test RSS feed fetch
    c.RSS_NEWS_FEED = "https://www.state.gov/rss-feed/press-releases/feed/"
    test_rss_feed(c.RSS_NEWS_FEED, int(c.TOP_N_STORIES))

    print("\n----- TEST CLOUD FUNCTIONALITY -----")
    # Test podcast cloud repo: list files, upload test file
    test_list_cloud_files()
    test_upload_to_cloud("README.md")

    print("\n----- TEST CONTAINER MANAGEMENT -----")
    # Test Docker container management, cycling from LLM to TTS container
    test_contianer_cycling(c.CONTAINER_LLM, int(c.BOOT_WAIT_LLM), c.CONTAINER_TTS, int(c.BOOT_WAIT_TTS), c.EXCLUDED_CONTAINERS)

    print("\n----- TEST LLM -----")
    # Test news segment generation with LLM
    news_segment_build_mode = "concurrent"  # concurrent OR iterative
    news_segment = test_news_segment_generation(c.SYSTEM_CHARACTER_KMART_RADIO, news_segment_build_mode)

    print("\n----- TEST TTS -----")
    # Test TTS chunking, generation, and merging of long texts
    long_text = news_segment
    test_tts_chunk(long_text)
    tts_output_file = test_tts_merge(long_text, c.MASKGCT_VOICE_REF_KMART_RADIO)

    print("\n----- TEST PODCAST BUILD -----")
    # Test adding background track to TTS WAV file
    background_track = c.BG_TRACK_KMART_RADIO
    tts_start_delay_ms = 4250
    fade_duration_s = 0
    final_podcast_file = test_add_bg_track(tts_output_file, background_track, tts_start_delay_ms, fade_duration_s)

    test_get_audio_duration(final_podcast_file)
    test_mp3_conversion(final_podcast_file)