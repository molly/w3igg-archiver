import selenium.webdriver.remote.webelement
from selenium.webdriver.common.by import By

from constants import WEBP_MAX_SIZE

from io import BytesIO
from PIL import Image
from urllib.parse import urlparse
import os
import re
import requests


def download_assets_from_tweet(
    tweet: selenium.webdriver.remote.webelement.WebElement,
    tweet_output_dir: str,
    tweet_ind: int,
) -> object:
    """
    Download any images that are contained within this tweet, and record alt text if it's been supplied.
    :param tweet: WebElement representing this tweet
    :param tweet_output_dir: Output directory in which to save the screenshot
    :param tweet_ind: Index of this tweet in the tweet thread
    :return: Object, keyed by tweet index, and image index, containing alt text. Example:
      {
        "0": {
          "0": "Alt text for image 1 in tweet 1",
          "1": "Alt text for image 2 in tweet 1"
        }
      }
    """
    images = tweet.find_elements(
        By.XPATH, ".//div[@data-testid='tweetPhoto'][not(.//video)]"
    )
    alt_dict = {}
    for img_ind, image in enumerate(images):
        image_id = "{}-{}".format(tweet_ind, img_ind)
        image_element = image.find_element(By.TAG_NAME, "img")

        alt = image_element.get_attribute("alt")
        if alt != "Image":
            if tweet_ind in alt_dict:
                alt_dict[tweet_ind][img_ind] = alt
            else:
                alt_dict[tweet_ind] = {img_ind: alt}

        img_src = image_element.get_attribute("src")
        full_size_src = re.sub(r"[?&]name=[^?&]*", r"", img_src)
        format_match = re.search(r"[?&]format=([^?&]*)", full_size_src)
        extension = format_match.group(1) or "webp"

        resp = requests.get(full_size_src)
        if extension == "webp":
            # Save image if it's already in webp format
            with open(
                os.path.join(
                    tweet_output_dir,
                    "assets",
                    "{}.{}".format(image_id, extension),
                ),
                "wb",
            ) as f:
                f.write(resp.content)
        else:
            # Open and convert image to webp if not already a webp
            file = BytesIO(resp.content)
            with Image.open(file) as image_data:
                convert_pil_image_to_webp(
                    image_data,
                    os.path.join(
                        tweet_output_dir, "assets", "{}.webp".format(image_id)
                    ),
                )
    return alt_dict


def get_tweet_alt_text(tweet: selenium.webdriver.remote.webelement.WebElement) -> str:
    """
    Create alt text for the tweet we're screenshotting.
    :param tweet: WebElement representing the tweet
    :return: Alt text containing the tweet text and timestamp
    """
    tweet_text = tweet.find_element(By.XPATH, ".//div[@data-testid='tweetText']")
    tweet_timestamp = tweet.find_element(By.TAG_NAME, "time")
    return "{} \nTweeted at {}".format(tweet_text.text, tweet_timestamp.text)


def get_tweet_links(
    tweet: selenium.webdriver.remote.webelement.WebElement,
) -> list[str]:
    """
    Get all links contained in this one tweet, expanding them from the t.co shortener.
    :param tweet: WebElement representing the tweet
    :return: List of URLs
    """
    tweet_links = tweet.find_elements(By.XPATH, ".//a[starts-with(@href, 'http')]")
    links = []
    for link in tweet_links:
        href = link.get_attribute("href")
        if urlparse(href).netloc == "t.co":
            head = requests.head(href, allow_redirects=True)
            url = head.url
            if url not in links:
                links.append(head.url)
    return links


def scrape_links_and_alt_text_from_tweets(
    tweets: list[selenium.webdriver.remote.webelement.WebElement],
) -> object:
    """
    Loop over tweets, creating alt string and pulling out links from them.
    :param tweets: List of WebElements representing each tweet to capture
    :return: Object containing the alt text for the full tweet thread, and an object (keyed by tweet index) containing
        lists of links for each tweet

    Example:
      {
        "alt": "Long alt text string representing full tweet thread"
        "links": {
          "0": ["https://example.com", "https://example2.com"]
        }
      }
    """
    alt = ""
    links = {}
    for ind, tweet in enumerate(tweets):
        if len(alt) > 0:
            alt += "\n\n"
        alt += get_tweet_alt_text(tweet)
        tweet_links = get_tweet_links(tweet)
        if len(tweet_links):
            links[ind] = tweet_links
    return {"alt": alt, "links": links}


def resize_image(pil_image: Image) -> Image:
    """
    Resize the supplied image to fit maximum webp size.
    :param pil_image: Original image
    :return: Resized image
    """
    if pil_image.width > WEBP_MAX_SIZE or pil_image.height > WEBP_MAX_SIZE:
        ratio = min(
            WEBP_MAX_SIZE / pil_image.width,
            WEBP_MAX_SIZE / pil_image.height,
        )
        return pil_image.resize(
            (round(pil_image.width * ratio), round(pil_image.height * ratio))
        )
    return pil_image


def convert_pil_image_to_webp(pil_image: Image, output_filepath: str) -> None:
    """
    Resize image if it's too large for webp, and convert it to a webp and save it at the specified output_filepath.
    :param pil_image: Original image
    :param output_filepath: Filepath to store the converted file
    """
    image = resize_image(pil_image)
    image.save(output_filepath, format="webp")


def convert_file_to_webp(input_filepath: str, output_filepath: str) -> None:
    """
    Convert the image at the specified input_filepath to a webp, then save it at the output_filepath and delete the original.
    :param input_filepath: Filepath to original file
    :param output_filepath: New filepath
    """
    with Image.open(input_filepath) as image:
        convert_pil_image_to_webp(image, output_filepath)
    os.remove(input_filepath)
