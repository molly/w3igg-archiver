import selenium.webdriver.remote.webelement

from constants import *
from page_is_scrolled_to_top import page_is_scrolled_to_top
from secrets import *
from tweet_utils import *

from TweetEntryLink import TweetEntryLink

from PIL import Image
from time import sleep
import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
)

USERNAME_XPATH = "//div[@data-testid='User-Name']//a//*[starts-with(text(), '@')]"
TWEET_LINK_XPATH = ".//a[contains(@href, '{}')]//time"


class TweetScreenshotter:
    webdriver_options = None
    driver = None

    def __init__(self):
        if TweetScreenshotter.driver is None:
            print("Setting up Selenium instance.")

            # Needs to use existing profile with logged-in Twitter account to capture screenshot, due to Twitter
            # changes that won't show replies to logged-out visitors
            profile = webdriver.FirefoxProfile(
                "/Users/molly/Library/Application Support/Firefox/Profiles/9e81e71e.w3igg-archiver",
            )

            TweetScreenshotter.webdriver_options = webdriver.FirefoxOptions()
            TweetScreenshotter.webdriver_options.profile = profile
            TweetScreenshotter.webdriver_options.add_argument("--headless")
            TweetScreenshotter.webdriver_options.add_argument("--disable-gpu")
            TweetScreenshotter.webdriver_options.add_argument("--window-size=600,10000")
            TweetScreenshotter.webdriver_options.set_preference(
                "layout.css.devPixelsPerPx", str(SCALING_FACTOR)
            )
            TweetScreenshotter.webdriver_options.set_preference(
                "general.useragent.override", USER_AGENT
            )

            TweetScreenshotter.driver = webdriver.Firefox(
                options=TweetScreenshotter.webdriver_options,
            )
            TweetScreenshotter.driver.set_window_size(600, 10000)
        self.webdriver_options = TweetScreenshotter.webdriver_options
        self.driver = TweetScreenshotter.driver

    @staticmethod
    def shutdown():
        if TweetScreenshotter.driver:
            try:
                TweetScreenshotter.driver.quit()
            except FileNotFoundError:
                # This is messy for some reason I can't identify yet
                pass
            except Exception as e:
                pass

    def _get_tweet(self, link: TweetEntryLink) -> bool:
        """
        Load the tweet specified in the link.
        :param link: URL of tweet
        :return: Boolean representing if the load succeeded.
        """
        # Find tweet
        tweet_link_xpath = TWEET_LINK_XPATH.format(urlparse(link.href).path)
        for i in range(3):
            self.driver.get(link.href)
            try:
                WebDriverWait(self.driver, 10).until(
                    expected_conditions.presence_of_element_located(
                        (
                            By.XPATH,
                            tweet_link_xpath + "| //*[@data-testid='error-detail']",
                        )
                    )
                )
                try:
                    self.driver.find_element(
                        By.CSS_SELECTOR, "*[data-testid='error-detail']"
                    )
                    print("Tweet was deleted.")
                    return False
                except NoSuchElementException:
                    return True
            except TimeoutException:
                print(
                    "Timed out waiting to load tweet. Link #{}: {}".format(
                        link.index, link.href
                    )
                )
                pass
        print("Tried 3 times to load link #{}, giving up.".format(link.index))
        return False

    def _clear_overlays(self):
        """
        Clear the various overlays that sometimes appear when you open Twitter so they're not in the way of the
        screenshotter.
        """
        # Close Google credentials prompt
        try:
            google_credentials_iframe = self.driver.find_element(
                By.XPATH, "//iframe[contains(@title, 'Sign in with Google Dialog')]"
            )
            close_button = google_credentials_iframe.find_element(
                By.CSS_SELECTOR, "#credentials-picker-container #close"
            )
            close_button.click()
            WebDriverWait.until(
                expected_conditions.invisibility_of_element(google_credentials_iframe)
            )
        except NoSuchElementException:
            pass
        except TimeoutException:
            print(
                "Something went wrong while trying to close the Google credentials overlay. Check the screenshot to "
                "make sure it's not in the way."
            )

        # Close "turn on notifications" prompt
        try:
            notifications_overlay = self.driver.find_element(
                By.XPATH,
                "//div[@data-testid='sheetDialog']//*[text()='Turn on notifications']",
            )
            close_button = self.driver.find_element(
                By.XPATH,
                "//div[@data-testid='sheetDialog']//*[@role='button'][@data-testid='app-bar-close']",
            )
            close_button.click()
            WebDriverWait.until(
                expected_conditions.invisibility_of_element(notifications_overlay)
            )
        except NoSuchElementException:
            pass
        except TimeoutException:
            print(
                "Something went wrong while trying to close the Twitter notifications overlay. Check the screenshot to "
                "make sure it's not in the way."
            )

        # Delete floating app elements that get in the way
        try:
            self.driver.execute_script("document.getElementById('layers').remove()")
        except Exception:
            pass

    @staticmethod
    def _find_tweet_index_in_thread(
        tweets: list[selenium.webdriver.remote.webelement.WebElement],
        link: TweetEntryLink,
    ) -> int:
        """
        Find the index of the specified link in the list of tweets supplied.
        :param tweets: List of tweets to search
        :param link: Link to find in list of tweets
        :return: Index of the tweet in the list, or None if not found.
        """
        tweet_link_xpath = TWEET_LINK_XPATH.format(urlparse(link.href).path)
        for ind, tweet in enumerate(tweets):
            try:
                el = tweet.find_element(By.XPATH, tweet_link_xpath)
                return ind
            except NoSuchElementException:
                pass
        # Something went wrong, but fall back to assuming it's the first tweet if so
        return 0

    @staticmethod
    def _find_end_of_thread_by_user(
        tweets: list[selenium.webdriver.remote.webelement.WebElement],
    ) -> int:
        """
        Find the last tweet by the original thread author in the supplied list of tweets.
        :param tweets: List of tweets to search
        :return: Index of the last tweet by the original author
        """
        user = tweets[0].find_element(By.XPATH, USERNAME_XPATH)
        tweeter = user.text

        # Find the last tweet in the thread by the original user
        last_tweet_index = 0
        while last_tweet_index < len(tweets) - 1:
            username = tweets[last_tweet_index + 1].find_element(
                By.XPATH, "." + USERNAME_XPATH
            )
            if username.text != tweeter:
                break
            last_tweet_index += 1
        return last_tweet_index

    def _capture_thread(
        self,
        tweets: list[selenium.webdriver.remote.webelement.WebElement],
        last_tweet_index: int,
        tweet_output_dir: str,
    ) -> object:
        """
        Capture a full thread of tweets, saving screenshots and assets to the specified tweet_output_dir
        :param tweets: Tweets on this page, some of which are tweets in the thread to capture
        :param last_tweet_index: Index of the last tweet to capture
        :param tweet_output_dir: Output directory to save screenshots and assets
        :return: Object containing tweet alt text, links, and optionally asset alt text if it exists
        """
        # Capture images and their alt text (if supplied)
        assets_alt = {}
        for ind, tweet in enumerate(tweets[: last_tweet_index + 1]):
            alt = download_assets_from_tweet(tweet, tweet_output_dir, ind)
            assets_alt.update(alt)

        # Get alt text and metadata
        meta = scrape_links_and_alt_text_from_tweets(tweets[: last_tweet_index + 1])
        if len(assets_alt):
            meta["assets_alt"] = assets_alt

        try:
            # Click on last tweet in thread to get reply box out of the way
            last_tweet_link = tweets[last_tweet_index].find_element(
                By.CSS_SELECTOR, "a > time"
            )
            last_tweet_link.click()
        except ElementClickInterceptedException:
            print(
                "Something went wrong clicking on last tweet, screenshot saved to error.png"
            )
            self.driver.save_full_page_screenshot("error.png")

        try:
            WebDriverWait(self.driver, 10).until(
                expected_conditions.invisibility_of_element_located(
                    (By.CSS_SELECTOR, "*[role='progressbar']")
                )
            )
            sleep(1)  # Even after the wait it needs a little more time :(
        except TimeoutException:
            print("Timed out waiting for page to load.")

        # Scroll to top of page
        self.driver.execute_script("window.scrollTo(0, 0)")
        try:
            WebDriverWait(self.driver, 10).until(page_is_scrolled_to_top())
        except TimeoutException:
            print("Timed out waiting for page to scroll to top.")
        timeline = self.driver.find_element(
            By.CSS_SELECTOR, "div[aria-label='Timeline: Conversation']"
        )

        # Find bottom boundary
        cutoff_element = self.driver.find_element(
            By.XPATH, "//time[contains(text(), '·')]"
        )
        bottom_boundary = cutoff_element.rect["y"] * SCALING_FACTOR

        # Get screenshot and crop to bottom boundary
        # No sleep needed since the page should already be loaded
        screenshot_path = os.path.join(tweet_output_dir, "screenshot.png")
        screenshot_path_webp = os.path.join(tweet_output_dir, "screenshot.webp")
        timeline.screenshot(screenshot_path)

        with Image.open(screenshot_path) as image:
            cropped = image.crop((0, 0, image.width, bottom_boundary + 70))
            convert_pil_image_to_webp(cropped, screenshot_path_webp)
        os.remove(screenshot_path)

        return meta

    def archive_tweet(self, link: TweetEntryLink) -> None:
        """
        Capture screenshot archive of the specified tweet link, which can be a single tweet or a thread. Then update
        the tweet link instance with the archive data.
        :param link: The link to the tweet (or start of the tweet thread) to capture
        :return: None
        """
        print("Archiving tweet or tweet thread for link {}.".format(link.index))

        success = self._get_tweet(link)
        if success:
            self._clear_overlays()
            link_text = link.link_text.lower()
            tweets = self.driver.find_elements(
                By.CSS_SELECTOR, "article[data-testid='tweet']"
            )

            try:
                # Set up directories to store screenshot/assets
                tweet_output_dir = os.path.join(OUTPUT_DIR, link.index_str)
                os.mkdir(tweet_output_dir)
                os.mkdir(os.path.join(tweet_output_dir, "assets"))

                if "tweet thread" in link_text or "tweets" in link_text:
                    print("Capturing tweet thread for link {}.".format(link.index))
                    last_tweet_index = self._find_end_of_thread_by_user(tweets)
                    metadata = self._capture_thread(
                        tweets, last_tweet_index, tweet_output_dir
                    )
                    link.archive_tweet_alt = metadata["alt"]
                    link.archive_tweet_links = metadata["links"]
                    link.archive_tweet_assets_alt = metadata.get("assets_alt", {})
                else:
                    last_tweet_index = self._find_tweet_index_in_thread(tweets, link)
                    if last_tweet_index != 0:
                        # The tweet we want to capture is a reply that's not first in the thread
                        print("Capturing tweet thread for link {}.".format(link.index))
                        metadata = self._capture_thread(
                            tweets, last_tweet_index, tweet_output_dir
                        )
                        link.archive_tweet_alt = metadata["alt"]
                        link.archive_tweet_links = metadata["links"]
                        link.archive_tweet_assets_alt = metadata.get("assets_alt", {})

                    else:
                        # Just one tweet to capture, and it's the first in the thread
                        print("Capturing tweet for link {}.".format(link.index))
                        tweet = tweets[0]

                        # Download assets from tweet
                        assets_alt = download_assets_from_tweet(
                            tweet, tweet_output_dir, 0
                        )

                        # Get alt text
                        link.archive_tweet_alt = get_tweet_alt_text(tweet)
                        link.archive_tweet_links = {"0": get_tweet_links(tweet)}
                        if len(assets_alt):
                            link.archive_tweet_assets_alt = assets_alt

                        sleep(
                            1
                        )  # Janky, but this gives images/etc. an extra second to load
                        screenshot_path = os.path.join(
                            tweet_output_dir, "screenshot.png"
                        )
                        screenshot_path_webp = os.path.join(
                            tweet_output_dir, "screenshot.webp"
                        )
                        tweet.screenshot(screenshot_path)
                        convert_file_to_webp(screenshot_path, screenshot_path_webp)
            except Exception as e:
                print(e)
