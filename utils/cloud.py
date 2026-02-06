import os, re, requests, shutil
from pathlib import Path
import boto3
import xml.etree.ElementTree as ET
from email.utils import formatdate
from io import BytesIO

import config as c

# Initialize session with S3 client, compatible with Cloudflare & AWS
session = boto3.session.Session()
s3 = session.client(
    "s3",
    region_name=c.R2_REGION,
    endpoint_url=f"https://{c.CLOUDFLARE_ACCOUNT_ID}.r2.cloudflarestorage.com",
    aws_access_key_id=c.R2_ACCESS_KEY,
    aws_secret_access_key=c.R2_SECRET_KEY
)

def list_existing_s3_files():
    """
    Lists all existing files in the S3 or R2 bucket.
    
    Returns:
        list(str): String list of all files in cloud storage.
    """
    try:
        response = s3.list_objects_v2(Bucket=c.R2_BUCKET_NAME)
        if "Contents" in response:
            return [obj["Key"] for obj in response["Contents"]]
        return []
    except Exception as e:
        print(f"Failed to list existing files in S3 / R2 bucket: {e}")
        return []

def upload_to_s3(file_path):
    """
    Uploads a file to the S3 or R2 bucket with public read permissions.
    
    Args:
        file_path (str): Path to the file to be uploaded.
    Returns:
        str: URL of uploaded file.
    """
    file_name = os.path.basename(file_path)
    try:
        print(f"Uploading {file_name}...")
        s3.upload_file(file_path, c.R2_BUCKET_NAME, file_name, ExtraArgs={"ACL": "public-read"})
        return f"{c.PODCAST_CLOUD_REPO}/{file_name}"
    except Exception as e:
        print(f"Failed to upload {file_name}: {e}")
        return None

def fetch_existing_rss():
    """
    Download existing podcast RSS feed from remote storage.

    Returns:
        ElementTree: XML element tree of the existing podcast RSS feed.
    """
    rss_url = f"{c.PODCAST_CLOUD_REPO}/{c.PODCAST_RSS_FILENAME}"
    try:
        response = requests.get(rss_url)
        if response.status_code == 200:
            return ET.parse(BytesIO(response.content))
    except Exception as e:
        print(f"Could not fetch existing RSS feed: {e}")
    return None

def sync_rss_feed(episode_url, episode_title, episode_duration, episode_image):
    """
    Generate a new podcast RSS feed, merging the latest episode to the
    beginning of the existing podcast RSS feed on cloud storage.

    Args:
        episode_url (str): Remote path to the new podcast episode MP3.
        episode_title (str): New podcast episode title.
        episode_duration (str): New podcast episode duration.
        episode_image (str): New podcast episode image.
    Returns:
        ElementTree: XML element tree of the new podcast RSS feed.
    """
    existing_rss = fetch_existing_rss()
    existing_items = {}

    # Create new RSS structure
    ET.register_namespace("itunes", "http://www.itunes.com/dtds/podcast-1.0.dtd")
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")

    # Podcast details
    ET.SubElement(channel, "title").text = c.PODCAST_TITLE
    ET.SubElement(channel, "link").text = c.PODCAST_CLOUD_REPO
    ET.SubElement(channel, "description").text = c.PODCAST_DESCRIPTION
    ET.SubElement(channel, "language").text = "en-us"

    # Podcast image
    image = ET.SubElement(channel, "image")
    ET.SubElement(image, "url").text = c.PODCAST_CLOUD_REPO + c.PODCAST_MAIN_IMAGE_URL
    ET.SubElement(image, "title").text = c.PODCAST_TITLE
    ET.SubElement(image, "link").text = c.PODCAST_CLOUD_REPO

    # If an existing RSS feed is available, extract old episodes
    if existing_rss:
        for item in existing_rss.findall(".//item"):
            guid = item.find("guid")
            if guid is not None:
                url = guid.text
                existing_items[url] = item

    if episode_url not in existing_items:  # Ensure no duplicates
        item = ET.SubElement(channel, "item")
        file_name = os.path.basename(episode_url)

        # Get file modification date, use as publication date
        # Requires RFC 2822-compliant date string (formatted with email.utils)
        file_path = os.path.join(c.PODCAST_ASSETS_DIRECTORY, file_name) 
        mod_time = os.path.getmtime(file_path)
        pub_date = formatdate(timeval=mod_time, usegmt=True)

        ET.SubElement(item, "title").text = episode_title
        ET.SubElement(item, "{http://www.itunes.com/dtds/podcast-1.0.dtd}duration").text = str(episode_duration)
        ET.SubElement(item, "{http://www.itunes.com/dtds/podcast-1.0.dtd}image").text = episode_image
        ET.SubElement(item, "link").text = episode_url
        ET.SubElement(item, "guid").text = episode_url
        ET.SubElement(item, "pubDate").text = pub_date

        enclosure = ET.SubElement(item, "enclosure")
        enclosure.set("url", episode_url)
        enclosure.set("type", "audio/mpeg")

        # Append old episodes
        for url, item in existing_items.items():
            channel.append(item)

    return ET.ElementTree(rss)

def upload_rss_feed(rss_tree):
    """
    Uploads the new podcast RSS feed to cloud storage with public read permissions.

    Args:
        rss_tree (ElementTree): XML element tree of the new podcast RSS feed.
    """
    rss_path = os.path.join(c.PODCAST_ASSETS_DIRECTORY, c.PODCAST_RSS_FILENAME)
    rss_tree.write(rss_path, encoding="utf-8", xml_declaration=True)
    
    try:
        s3.upload_file(rss_path, c.R2_BUCKET_NAME, c.PODCAST_RSS_FILENAME, ExtraArgs={"ACL": "public-read"})
        print(f"RSS feed updated: {c.PODCAST_CLOUD_REPO}/{c.PODCAST_RSS_FILENAME}")
    except Exception as e:
        print(f"Failed to upload RSS feed: {e}")