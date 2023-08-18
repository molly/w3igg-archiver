from constants import *
from page_is_scrolled_to_top import page_is_scrolled_to_top

from PIL import Image
from time import sleep
import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException

USERNAME_XPATH = "//div[@data-testid='User-Name']//a//*[starts-with(text(), '@')]"


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
            # TweetScreenshotter.webdriver_options.add_argument("--headless")
            TweetScreenshotter.webdriver_options.set_preference(
                "layout.css.devPixelsPerPx", str(SCALING_FACTOR)
            )

            TweetScreenshotter.driver = webdriver.Firefox(
                profile,
                options=TweetScreenshotter.webdriver_options,
                service_log_path="/dev/null",
            )
            TweetScreenshotter.driver.set_window_size(600, 5000)
        self.webdriver_options = TweetScreenshotter.webdriver_options
        self.driver = TweetScreenshotter.driver

    def clear_overlays(self):
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

    def archive_tweet(self, link):
        url = link["href"]
        self.driver.get(url)
        try:
            WebDriverWait(self.driver, 10).until(
                expected_conditions.presence_of_element_located(
                    (By.CSS_SELECTOR, "div[data-testid='tweetText']")
                )
            )
        except TimeoutException:
            print(
                "Timed out waiting to load tweet. Link #{}: {}".format(
                    link["index"], url
                )
            )

        self.clear_overlays()

        screenshot_path = os.path.join(OUTPUT_DIR, "screenshot.png")
        link_text = link["linkText"].lower()
        tweets = self.driver.find_elements(
            By.CSS_SELECTOR, "article[data-testid='tweet']"
        )
        if "tweet thread" in link_text:
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

            # Click on last tweet in thread to get reply box out of the way
            last_tweet_link = tweets[last_tweet_index].find_element(
                By.CSS_SELECTOR, "a > time"
            )
            last_tweet_link.click()
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
                By.XPATH,
                "//div[@role='group']//span[starts-with(text(), 'Repost') or starts-with(text(), 'Quote') or "
                "starts-with(text(), 'Like') or starts-with(text(), 'Bookmark')] | "
                "//div[@role='group']//div[@role='button' and @aria-label='Reply']",
            )
            bottom_boundary = cutoff_element.rect["y"] * SCALING_FACTOR

            # Get screenshot and crop to bottom boundary
            # No sleep needed since the page should already be loaded
            timeline.screenshot(screenshot_path)

            with Image.open(screenshot_path) as image:
                cropped = image.crop((0, 0, image.width, bottom_boundary - 20))
                cropped.save(screenshot_path)
        else:
            # Just one tweet to capture.
            tweet = tweets[0]
            sleep(1)  # Janky, but this gives images/etc. an extra second to load
            tweet.screenshot(screenshot_path)

    def shutdown(self):
        if self.driver is not None:
            self.driver.quit()
