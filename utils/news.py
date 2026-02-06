import requests
import xml.etree.ElementTree as ET
from newsplease import NewsPlease

import config as c

# HTTP headers for web requests to make them seem legit, e.g. iPhone headers
HTTP_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Referer': 'https://www.google.com/',
    'Upgrade-Insecure-Requests': '1'
}

class NewsStory():
    """
    Container for news stories and corresponding AI summaries
    """
    def __init__(
        self,
        title: str = '',
        link: str = '',
        content: str = '',
        summary_character: str = '',
        summary_normal: str = ''
    ):
        self.title = title
        self.link = link
        self.content = content
        self.summary_character = summary_character
        self.summary_normal = summary_normal

def fetch_news_story(
    article_link: str
) -> NewsStory:
    """
    Fetch a single news story from an article URL.
    
    Args:
        article_link (str): Links to news article.

    Returns:
        list[NewsStory]: A list of NewsStory objects.
    """
    article = NewsPlease.from_url(
        url=article_link, 
        request_args={'headers': HTTP_HEADERS}
    )

    story = NewsStory()
    story.title = article.title
    story.link=article_link
    story.content = article.maintext

    return story

def fetch_rss_news_stories(
    rss_feed: str,
    top_n_stories: int
) -> list[NewsStory]:
    """
    Fetch a list of the Top N news stories from an RSS feed.
    
    Args:
        rss_feed (str): RSS news feed URL with links to articles.
        top_n_stories (int): Number of stories to fetch from top of feed.

    Returns:
        list[NewsStory]: A list of NewsStory objects.
    """
    response = requests.get(rss_feed, headers=HTTP_HEADERS)
    rss_feed = response.content
    xml_root = ET.fromstring(rss_feed)

    # Get all items in RSS feed
    rss_items = xml_root.findall('.//item')

    stories_list = []

    # Parse the first N items in RSS feed, skipping broken items
    story_number = 0
    count = 0
    while count < top_n_stories:
        story = NewsStory()
        story.title = rss_items[story_number].find('title').text
        story.link = rss_items[story_number].find('link').text
        story.content = NewsPlease.from_url(
            url=story.link, 
            request_args={'headers': HTTP_HEADERS}).maintext
        # Skip past links that cannot be parsed, e.g. breaking news live feeds
        if not story.content:
            story_number += 1
            count = count
        else:
            stories_list.append(story)
            story_number += 1
            count += 1

    return stories_list