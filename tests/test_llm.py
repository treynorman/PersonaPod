import config as c
from utils.news import NewsStory,fetch_rss_news_stories
from utils.container_management import *
from utils.llm import *

"""
    Test automatic generation of a news segment with NewsPlease and LLM.
    
    build_mode = "concurrent": Build concerrently from N character news
        stories plopped into single news summary prompt
    build_mode = "iterative": Build iteratively from N character news
        stories stitched with generated intro and outro
        (more accurate, but sometimes more boring)
"""

def test_news_segment_generation(character_system_prompt, build_mode):
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

    if build_mode == "concurrent":
        # Build news segment from character summaries in one prompt
        news_segment = llama_cpp_news_segment_concurrent(
            character_system_prompt,
            c.NEWS_SEGMENT_FULL,
            news_stories,
            "character"
        )
    elif build_mode == "iterative":
        # Build news segment from character summaries iteratively and stitch
        news_segment = llama_cpp_news_segment_iterative(
            character_system_prompt,
            c.NEWS_SEGMENT_INTRO,
            c.NEWS_SEGMENT_OUTRO,
            news_stories
        )
    else:
        raise ValueError(f"Invalid build mode: {build_mode}. Supported values: {valid_build_modes}")
    
    print("Generated news segment:\n" + news_segment)
    return news_segment