from utils.news import *

"""
    Tests for news objects, news article fetching, story fetching from RSS
"""

def test_news_objects():
    story = NewsStory()

    story1 = NewsStory(
        title="AI Breakthrough",
        content="New AI model achieves...",
        link="https://example.com/ai-news"
    )

    story2 = NewsStory(
        title="Climate Summit Update",
        content="Global leaders agree on climate goals...",
        link="https://example.com/climate"
    )

    story3 = NewsStory(
        title="Warming Trend Accelerates",
        content="Fueled by Climate change...",
        link="https://example.com/warming"
    )

    stories = []
    stories.append(story1)
    stories.append(story2)
    stories.append(story3)

    print(f'Total stories: {len(stories)}')
    print(f'First NewsStory title: {stories[0].title}')
    print(f'Second NewsStory link: {stories[1].link}')
    print(f'Third NewsStory content: {stories[2].content}')

def test_news_article_fecth(article_link):
    story = fetch_news_story(article_link)

    print(f'NewsStory title: {story.title}')
    print(f'NewsStory link: {story.link}')
    print(f'NewsStory content:\n{story.content}')

def test_rss_feed(rss_link, top_n_stories, headers=None):
    news_stories = fetch_rss_news_stories(rss_link, top_n_stories)

    for story in news_stories:
        print(f'NewsStory title: {story.title}')
        print(f'NewsStory link: {story.link}')
        print(f'NewsStory content:\n{story.content}')
        print()