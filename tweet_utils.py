from selenium.webdriver.common.by import By

from constants import WEBP_MAX_SIZE

from io import BytesIO
from PIL import Image
import os
import re
import urllib


def download_assets_from_tweet(tweet, tweet_output_dir, tweet_ind):
    images = tweet.find_elements(By.XPATH, ".//div[@data-testid='tweetPhoto']")
    alt_dict = {}
    for img_ind, image in enumerate(images):
        image_id = "{}-{}".format(tweet_ind, img_ind)
        image_element = image.find_element(By.TAG_NAME, "img")
        alt = image_element.get_attribute("alt")
        if alt != "Image":
            alt_dict[image_id] = alt
        img_src = image_element.get_attribute("src")
        full_size_src = re.sub(r"[?&]name=[^?&]*", r"", img_src)
        format_match = re.search(r"[?&]format=([^?&]*)", full_size_src)
        extension = format_match.group(1) or "webp"

        if extension == "webp":
            # Save image if it's already in webp format
            urllib.request.urlretrieve(
                full_size_src,
                os.path.join(
                    tweet_output_dir,
                    "assets",
                    "{}.{}".format(image_id, extension),
                ),
            )
        else:
            # Open and convert image to webp if not already a webp
            with urllib.request.urlopen(full_size_src) as url:
                file = BytesIO(url.read())
                with Image.open(file) as image_data:
                    convert_pil_image_to_webp(
                        image_data,
                        os.path.join(
                            tweet_output_dir, "assets", "{}.webp".format(image_id)
                        ),
                    )
    return alt_dict


def get_tweet_alt_text(tweet):
    tweet_text = tweet.find_element(By.XPATH, ".//div[@data-testid='tweetText']")
    tweet_timestamp = tweet.find_element(By.TAG_NAME, "time")
    return '"{}" \nTweeted at {}'.format(tweet_text.text, tweet_timestamp.text)


def resize_image(pil_image):
    if pil_image.width > WEBP_MAX_SIZE or pil_image.height > WEBP_MAX_SIZE:
        ratio = min(
            WEBP_MAX_SIZE / pil_image.width,
            WEBP_MAX_SIZE / pil_image.height,
        )
        return pil_image.resize(
            (round(pil_image.width * ratio), round(pil_image.height * ratio))
        )
    return pil_image


def convert_pil_image_to_webp(pil_image, output_filepath):
    image = resize_image(pil_image)
    image.save(output_filepath, format="webp")


def convert_file_to_webp(input_filepath, output_filepath):
    with Image.open(input_filepath) as image:
        convert_pil_image_to_webp(image, output_filepath)
    os.remove(input_filepath)
