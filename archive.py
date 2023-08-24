import argparse
import concurrent.futures
import os
import shutil
from urllib.parse import urlparse

from constants import *
from database import Database
from storage import Storage
from tweet_screenshotter import TweetScreenshotter
from wayback import archive_url


def cleanup():
    """Clean up output directory before run, or create it if it doesn't exist."""
    if os.path.exists(OUTPUT_DIR):
        # Erase all files in the output directory from last run
        shutil.rmtree(OUTPUT_DIR)
    os.mkdir(OUTPUT_DIR)


def archive_link(link):
    if "screenshotter" in link:
        return link["screenshotter"].archive_tweet(link)
    else:
        return archive_url(link)


def archive(entry_id):
    db = None
    storage = None
    tweet_screenshotter = None
    try:
        if entry_id is None:
            print("Entry ID required.")
            return

        cleanup()
        db = Database()

        links = db.get_entry_links(entry_id)

        # Set up an instance of TweetScreenshotter if there are any tweets in the links, otherwise we don't need it
        if any([urlparse(link["href"]).netloc == "twitter.com" for link in links]):
            tweet_screenshotter = TweetScreenshotter()
            storage = Storage()

        # Add an index parameter to the links to help with logging
        # Pass along screenshotter instance for tweets
        for idx, link in enumerate(links):
            link["index"] = idx
            if urlparse(link["href"]).netloc == "twitter.com":
                link["screenshotter"] = tweet_screenshotter

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(links)) as executor:
            archive_links = list(executor.map(archive_link, links))
            print("Done finding archive links")
            db.update_entry_with_archives(entry_id, storage, archive_links)
    finally:
        if db is not None:
            db.shutdown()
        if tweet_screenshotter is not None:
            tweet_screenshotter.shutdown()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Archive links in a given Web3 is Going Just Great entry."
    )
    parser.add_argument("entry_id", help="ID of the W3IGG entry, in numerical format.")
    args = parser.parse_args()
    archive(**vars(args))
