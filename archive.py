import argparse
import concurrent.futures
import os
import shutil

from constants import *
from Database import Database
from TweetScreenshotter import TweetScreenshotter
from wayback import archive_url

from EntryLink import EntryLink
from TweetEntryLink import TweetEntryLink


def cleanup():
    """Clean up output directory before run, or create it if it doesn't exist."""
    if os.path.exists(OUTPUT_DIR):
        # Erase all files in the output directory from last run
        shutil.rmtree(OUTPUT_DIR)
    os.mkdir(OUTPUT_DIR)


def archive_link(link: EntryLink) -> None:
    """
    Delegate archiving based on whether the link is a tweet or something else. Helper function passed to the thread
    pool executor.
    :param link: One link in a W3IGG entry.
    :return: None
    """
    if isinstance(link, TweetEntryLink):
        TweetScreenshotter().archive_tweet(link)
    else:
        archive_url(link)


def archive(entry_id: str) -> None:
    """Archive all links in the post with the specified entry_id.
    :param entry_id: Date-formatted entry ID (YYYY-MM-DD-ID)
    :return: None
    """
    if entry_id is None:
        print("Entry ID required.")
        return

    cleanup()
    db = Database()

    links: list[EntryLink] = db.get_entry_links(entry_id)

    # Add an index parameter to the links to help with logging
    # Pass along screenshotter instance for tweets
    for idx, link in enumerate(links):
        link.index = idx

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(links)) as executor:
        executor.map(archive_link, links)
    print("Done finding archive links")
    db.update_entry_with_archives(entry_id, links)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Archive links in a given Web3 is Going Just Great entry."
    )
    parser.add_argument("entry_id", help="ID of the W3IGG entry, in numerical format.")
    args = parser.parse_args()
    archive(**vars(args))
