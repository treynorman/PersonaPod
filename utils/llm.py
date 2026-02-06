import re, random, time
import openai
from typing import Literal

import config as c
from utils.news import NewsStory

"""
Multiple retries are made if LLM API calls fail. This accounts
for uncertainty around the time required for the LLM container to boot.
The time to wait between retries (RETRY_INTERVAL) is given in seconds.
"""
MAX_RETRIES = 5
RETRY_INTERVAL = 1

def llama_cpp_summarize_text(
    system_prompt: str,
    summary_prompt: str,
    text: str
) -> str:
    """
    Summarize text with llama.cpp via the OpenAI API.
    Multiple retries are made if API calls fail.

    Args:
        system_prompt (str): User-defined system prompt.
        summary_prompt (str): User-defined summarization prompt.
        text (str): Text to summarize.

    Returns:
        str: Summarized text from LLM running on llama.cpp.
    """
    
    # Try the API call every RETRY_INTERVAL until MAX_RETRIES is reached
    retries = 0
    while retries < MAX_RETRIES:
        try:
            print("Summarizing text with llama.cpp...")
            client = openai.OpenAI(
                base_url= c.LLAMA_CPP_BASE_URL,
                api_key = c.LLAMA_CPP_API_KEY
            )
            completion = client.chat.completions.create(
                model="",
                messages=[
                    {"role": "system", "content": f'''{system_prompt}'''},
                    {"role": "user", "content": f'''{summary_prompt}{text}'''}
                ]
            )
            
            # Capture LLM output and remove <think> block(s) from reasoning model
            llm_output = completion.choices[0].message.content
            llm_output = re.sub(r"<think>.*?</think>.", '', llm_output, flags=re.DOTALL)
            
            return llm_output

        except Exception as e:
            print(f"Attempt {retries + 1} failed: {e}")
            retries += 1
            if retries < MAX_RETRIES:
                time.sleep(RETRY_INTERVAL)
            else:
                raise Exception("Failed after maximum number of retries.")

def llama_cpp_news_segment_concurrent(
    system_prompt: str,
    segment_prompt: str,
    news_stories: list[NewsStory],
    build_mode: str
) -> str:
    """
    Builds a news segment concurrently with llama.cpp via the OpenAI API.
    News story summaries are merged to generate a full segment all at once.
    Can build using character summaries (character) or normal summaries (normal).
    Multiple retries are made if API calls fail.

    Args:
        system_prompt (str): User-defined system prompt.
        segment_prompt (str): User-defined prompt to generate a full news segment
        news_stories (list[NewsStory]): A list of NewsStory objects to process.
        build_mode (str): character OR normal
            "character": Use character news summaries from NewsStory objects
            "normal": Use normal news summaries from NewsStory objects)

    Returns:
        str: Full news segment text.
    """

    # Validate the summary type selected
    valid_build_modes = {"character", "normal"}
    if build_mode not in valid_build_modes:
        raise ValueError(f"Invalid build mode: {build_mode}. Supported values: {valid_build_modes}")

    if build_mode == "character":
        character_summaries = [story.summary_character for story in news_stories]
        # Check for empty character summaries and raise an error if found
        if any(summary == '' for summary in character_summaries):
            raise ValueError("One or more NewsStory character summaries are empty.")
    elif build_mode == "normal":
        normal_summaries = [story.summary_normal for story in news_stories]
        # Check for empty normal summaries and raise an error if found
        if any(summary == '' for summary in normal_summaries):
            raise ValueError("One or more NewsStory normal summaries are empty.")
    
    news_segment = ''
    retries = 0
    while retries < MAX_RETRIES:
        try:
            print(f"Building news segment llama.cpp (concurrent, {build_mode})...")
            client = openai.OpenAI(
                base_url= c.LLAMA_CPP_BASE_URL,
                api_key = c.LLAMA_CPP_API_KEY
            )
            
            if build_mode == "character":
                completion = client.chat.completions.create(
                    model="",
                    messages=[
                        {"role": "system", "content": f'''{system_prompt}'''},
                        {"role": "user", "content": f'''{segment_prompt}{"\n\n".join(character_summaries)}'''}
                    ]
                )

                # Capture output and remove <think> block(s) from reasoning model
                llm_output = completion.choices[0].message.content
                llm_output = re.sub(r"<think>.*?</think>.", '', llm_output, flags=re.DOTALL)
                news_segment += llm_output
                
                return news_segment
            elif build_mode == "normal":
                completion = client.chat.completions.create(
                    model="",
                    messages=[
                        {"role": "system", "content": f'''{system_prompt}'''},
                        {"role": "user", "content": f'''{segment_prompt}{"\n\n".join(normal_summaries)}'''}
                    ]
                )
                
                # Capture output and remove <think> block(s) from reasoning model
                llm_output = completion.choices[0].message.content
                llm_output = re.sub(r"<think>.*?</think>.", '', llm_output, flags=re.DOTALL)
                news_segment += llm_output
                
                return news_segment
            else:
                raise ValueError("Error: Unsupported build_mode was passed") 

        except Exception as e:
            print(f"Attempt {retries + 1} failed: {e}")
            retries += 1
            if retries < MAX_RETRIES:
                time.sleep(RETRY_INTERVAL)
            else:
                raise Exception("Failed after maximum number of retries.")

def llama_cpp_news_segment_iterative(
    system_prompt: str,
    intro_prompt: str,
    outro_prompt: str,
    news_stories: list[NewsStory]
) -> str:
    """
    Builds a news segment iteratively with llama.cpp via the OpenAI API.
    News story character summaries are used as-is. Summaries are stitched together
    with randomized hard-coded transitions in between. Intro and outro are generated.
    Multiple retries are made if API calls fail.

    Args:
        system_prompt (str): User-defined system prompt.
        intro_prompt (str): User-defined prompt to generate news segment intro.
        outro_prompt (str): User-defined prompt to generate news segment outtro.
        news_stories (list[NewsStory]): A list of NewsStory objects to process.

    Returns:
        str: Full news segment text.
    """
    
    news_segment = ''
    character_summaries = [story.summary_character for story in news_stories]

    # Check for empty character summaries and raise an error if found
    if any(summary == '' for summary in character_summaries):
        raise ValueError("One or more NewsStory character summaries are empty.")
    
    retries = 0
    while retries < MAX_RETRIES:
        try:
            print("Building news segment with llama.cpp (iterative)...")
            client = openai.OpenAI(
                base_url= c.LLAMA_CPP_BASE_URL,
                api_key = c.LLAMA_CPP_API_KEY
            )
            
            # Intro creation
            completion = client.chat.completions.create(
            model="",
            messages=[
                {"role": "system", "content": f'''{system_prompt}'''},
                {"role": "user", "content": f'''{intro_prompt}{"\n\n".join(character_summaries)}'''}
            ]
            )

            # Capture output and remove <think> block(s) from reasoning model
            llm_output = completion.choices[0].message.content
            llm_output = re.sub(r"<think>.*?</think>.", '', llm_output, flags=re.DOTALL)
            news_segment += llm_output + "\n\n"

            # News story character summary aggregation
            count = 0
            for summary in character_summaries:
                if count == 0:
                    news_segment += random.choice(["First, ", "Firstly, ", "First up, ", "To kick things off, "])
                    news_segment += summary + "\n\n"
                elif count < (len(character_summaries) - 1):
                    news_segment += random.choice(["In other news, ", "Meanwhile, ", "Moving on, ", "Elsewhere, ", "Turning to our next story, "])
                    news_segment += summary + "\n\n"
                else:
                    news_segment += random.choice(["Lastly, ", "Finally, ", "In our final story, "])
                    news_segment += summary + "\n\n"
                count += 1

            # Outro creation
            completion = client.chat.completions.create(
            model="",
            messages=[
                {"role": "system", "content": f'''{system_prompt}'''},
                {"role": "user", "content": f'''{outro_prompt}{"\n\n".join(character_summaries)}'''}
            ]
            )
            
            # Capture output and remove <think> block(s) from reasoning model
            llm_output = completion.choices[0].message.content
            llm_output = re.sub(r"<think>.*?</think>.", '', llm_output, flags=re.DOTALL)
            news_segment += llm_output
            
            return news_segment
        
        except Exception as e:
            print(f"Attempt {retries + 1} failed: {e}")
            retries += 1
            if retries < MAX_RETRIES:
                time.sleep(RETRY_INTERVAL)
            else:
                raise Exception("Failed after maximum number of retries.")
