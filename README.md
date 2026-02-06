<div align="center">
<h2>🎙️ PersonaPod: AI News Podcast Generator with Voice & Persona Cloning</h2>
</div>

<div align="center">
<picture>
  <img src="podcast/assets/personapod-logo.svg" alt="PersonaPod Logo" width="300">
</picture>
</div>

### Overview

**PersonaPod** is an open source AI podcast generator. It follows news article links from a news RSS feed, extracts the content, summarizes the articles, generates a news segment, then delivers the latest news using a cloned voice and personality of a defined persona. PersonaPod **runs  locally on open source AI models** and requires **zero commercial AI services**. Docker containers are automatically managed on the host machine to swap between **local LLM & TTS models** during podcast generation, allowing PersonaPod to run on systems with limited VRAM (15 GB minimum required when using the default TTS model).

Generated podcast episodes are automatically uploaded to cloud storage. A **podcast RSS feed** is maintained on publicly accessible storage and updated with the latest generated episodes. A **web podcast player** is also included to serve the podcast episodes in a web browser.

### Features

- Automatic podcast generation from any news RSS feed
- Voice cloning & personality customization
- Fully local, open source operation with local AI services
- Automatic management of AI Docker containers
- Automatic updating of podcast RSS feed on cloud
- Web app for playing podcasts in the browser

### Demos

**Kmart Radio News**

<video controls>
  <source src="https://personapod.lol/demos/kmart_radio.mp4" type="audio/mp4">
</video>

**Rob Boss News**

<video controls>
  <source src="https://personapod.lol/demos/rob_boss.mp4" type="audio/mp4">
</video>

**Jim Booyah News**

<video controls>
  <source src="https://personapod.lol/demos/jim_booyah.mp4" type="audio/mp4">
</video>

**Michael's Cot News**

<video controls>
  <source src="https://personapod.lol/demos/michaels_cot.mp4" type="audio/mp4">
</video>


### Models & Services Employed

**[MaskGCT: Zero-Shot Text-to-Speech with Masked Generative Codec Transformer](https://maskgct.github.io/)**

MaskGCT is a highly performant text-to-speech (TTS) model with the ability to clone voices in inference using a voice clip ~5-10 seconds long.

Unlike models built on an autoregressive / diffusion decoder architecture, MaskGCT does not require clean voice samples or use a denoising processes to generate outputs. As a result it is able to preserve the microphone dynamics, tone, and overall ambiance of the voice sample. Rather than erroneously matching features like room dynamics or environment noise, failing to clone the provided voice sample, MaskGCT is far less sensitive and reliably matches inputs.

MaskGCT was not released in a Docker container or designed to run as a service on the local network. I've provided a container to encapsulate it, making it accessible on the local network via API.

**[Qwen3-32b: Reasoning LLM with Hybrid Thinking Modes](https://huggingface.co/Qwen/Qwen3-32B)** (used in demos)

Qwen3 is a series of open source LLMs from Alibaba with reasoning capabilities that can be enabled or disabled through prompting.

Qwen3-32b with 4-bit quantization has been tested for LLM inference and performs well for both summarization and persona preservation with thinking mode enabled. It consumes nearly 24 GB of VRAM during operation. Smaller LLMs can be used on systems with tighter hardware constraints.

**[llama.cpp: LLM inference in C/C++](https://github.com/ggml-org/llama.cpp)**

llama.cpp is used to run large language models (LLMs) locally. It is fast, robust, and fully free and open source. Since llama.cpp uses an Open AI compatible API, LLM API calls in this project can easily be pointed to another service with minor modification to the code base.

**[Cloudflare R2 Free Tier: S3-compatible Object Storage](https://www.cloudflare.com/developer-platform/products/r2/)**

Cloudflare R2 offers a very generous free tier for hosting the generated podcast, making it publicly accessible. With MP3 VBR-V2 compression for the podcast audio, multiple years of daily news podcast episodes can be hosted for free.

**[Docker](https://www.docker.com/)**

Docker containers are used for all AI services in this project. LLM and TTS containers are started and stopped as needed, allowing the largest possible models to be used on systems with limited VRAM.

### Installation & Setup

Build and run a MaskGCT inside Docker container that's been modified to listen on all network interfaces. MaskGCT does not include a native Docker container. I've provided a Dockerfile that builds and encapsulates the project, resolves dependency issues, and listens on all interfaces. 

This MaskGCT Dockerfile is provided in a [separate GitHub repo](https://github.com/treynorman/MaskGCT-Docker).
```
git clone https://github.com/treynorman/MaskGCT-Docker
cd "MaskGCT-Docker"
docker build -t Amphion/mask-gct .
docker run --runtime=nvidia --privileged --cap-add=ALL --name mask-gct -p 2121:2121 -p 2222:4200 -p 7860:7860 -d Amphion/mask-gct
```

Clone this GitHub repo.
```
git clone https://github.com/treynorman/PersonaPod
```

Create and activate a virtual environment for the project. Then, install all dependencies from the `requirements.txt`.
```
cd PersonaPod
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

[Install ffmpeg](https://www.ffmpeg.org/download.html), e.g. for Debian based Linux systems:
```
sudo apt install ffmpeg
```

Create a public Cloudflare R2 bucket for hosting the podcast. Take note of the Cloudflare account ID, bucket name, and API keys.
1. In the Cloudflare dashboard, go to the R2 object storage page, go to **Overview**
2. Select Create bucket.
3. Enter the bucket name, e.g. `ai-news-pod`
4. Select Create bucket.
5. Go to **Object Storage** > **Manage API Tokens**
6. Create a **Custom API Token**

Upload the podcast player web application and image assets to the Cloudflare R2 bucket.
```
├── assets
│   ├── kmart-radio.jpg
│   ├── main-image.jpg
│   └── rss-parser.min.js
├── favicon (optional)
│   ├── apple-touch-icon.png
│   ├── favicon-16x16.png
│   ├── favicon-32x32.png
│   ├── favicon-96x96.png
│   ├── favicon.ico
│   ├── favicon.svg
│   ├── site.webmanifest
│   ├── web-app-manifest-192x192.png
│   └── web-app-manifest-512x512.png
└── index.html
```

Configure the project using the template provided in `.env`.

Below is an overview of the required environment variables:
1. RSS feed for news articles & number of top stories to use.
2. Cloudflare account ID, bucket name, and API keys.
3. AI Docker container names, boot wait times, and any *excluded containers* which will remain running during AI operations.
4. llama.cpp API base URL and key (any OpenAI compatible LLM API will work)
5. MaskGCT API base URL, path to voice samples directory, and voice sample filenames.
6. Podcast episode background tracks directory and background track filenames.
7. Podcast assets directory on local machine for storing generated episodes and RSS feed XML file.
8. Podcast title, description, and RSS feed filename.
9. Podcast cloud repo base URL and relative links to images used in the podcast feed.
10. Define a custom environment variable for your AI persona with a path to the system prompt TXT file. `SYSTEM_CHARACTER_KMART_RADIO` is provided as an example.

Define a custom prompt for your podcast persona. An example persona prompt is provided in `prompts/system_character_kmart_radio.txt`.

### Usage

Inside `main.py` use the `create_episode` function to configure the podcast. This function will pull the latest news, manage local AI containers to generate the episode, upload the episode to cloud storage, and update the podcast RSS feed.

**Required Arguments:**
*   `character_system_prompt` (str): Defines the character's personality.
*   `character_voice_ref` (str): Path to the voice sample.
*   `episode_image` (str): Path to the remote image.
*   `title` (str): Episode title.

**Optional Arguments:**
*   `bg_track` (str): Path to the background track.
*   `tts_start_delay_ms` (int): Delay before podcast voice starts (ms).
*   `fade_duration_s` (int): Fade out duration for background track (s).

**Example:**
```python
create_episode(
    c.SYSTEM_CHARACTER_KMART_RADIO, 
    c.MASKGCT_VOICE_REF_KMART_RADIO, 
    c.PODCAST_EPISODE_IMAGE_URL_KMART_RADIO, "Kmart Radio News", 
    c.BG_TRACK_KMART_RADIO, 12000, 5)
```

**Run main.py to Generate Podcast Episodes:**
```
source venv/bin/activate
python3 main.py
```

**(Optional) Update Podcast Daily Using a Cron Job:**

Create a script, e.g. `update-podcast.sh`, to run generate new podcast episodes. Be sure to use absolute paths to active the virtual environment and run the code.
```
#!/bin/bash

cd /absolute/path/to/PersonaPod
source venv/bin/activate
python3 main.py
```

Then create a cron job to run the script on a daily schedule, e.g. at 7am each day, and write output to `update-podcast-cron.log` by following the instructions below.

Run `crontab -e` and add this line, using absolute paths to the project files on your system.
```
0 7 * * * /absolute/path/to/PersonaPod/update-podcast.sh >> //absolute/path/to/PersonaPod/update-podcast-cron.log 2>&1
```

### Disclaimer

While efforts have been made to optimize outputs through various techniques, this project may still produce outputs that are unexpected, biased, or inaccurate. High-quality synthetic speech can be misused to create convincing fake audio content for impersonation, fraud, or spreading disinformation. Users must ensure transcripts are reliable, check content accuracy, and avoid using generated content in misleading ways. Users are expected to use the generated content and to deploy the models in a lawful manner, in full compliance with all applicable laws and regulations in the relevant jurisdictions. It is best practice to disclose the use of AI when sharing AI-generated content. PersonaPod is a hobby project and not intended for use in commercial or real-world applications without further testing and development.