import argparse
import concurrent.futures
import os
import shutil

from constants import *
from Database import Database
from TweetScreenshotter import TweetScreenshotter
from wayback import archive_url

from EntryLink import EntryLink
from ArchivableEntryLink import ArchivableEntryLink
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
        if link.archive_bucket_path is None:
            TweetScreenshotter().archive_tweet(link)
        elif link.force_overwrite:
            link.clear_old_archive_data()
            TweetScreenshotter().archive_tweet(link)
        else:
            print(
                "Not archiving link {}, as it's already been archived. Use --force-overwrite to re-archive.".format(
                    link.index
                )
            )
    elif isinstance(link, ArchivableEntryLink):
        if link.archive_href is None:
            archive_url(link)
        elif link.force_overwrite:
            link.clear_old_archive_data()
            archive_url(link)
        else:
            print(
                "Not archiving link {}, as it's already been archived. Use --force-overwrite to re-archive.".format(
                    link.index
                )
            )


def archive(entry_id: str, force_overwrite: bool = False) -> None:
    """Archive all links in the post with the specified entry_id.
    :param entry_id: Date-formatted entry ID (YYYY-MM-DD-ID)
    :param force_overwrite: Whether to re-archive links even if they've already been archived
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
        link.force_overwrite = force_overwrite

    # TODO: Thread this once the kinks are ironed out
    for link in links:
        archive_link(link)
    print("Done finding archive links")
    db.update_entry_with_archives(entry_id, links)
    TweetScreenshotter.shutdown()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Archive links in a given Web3 is Going Just Great entry."
    )
    parser.add_argument("entry_id", help="ID of the W3IGG entry, in numerical format.")
    parser.add_argument(
        "--force-overwrite",
        help="Re-archive links even if they've already been archived",
        action="store_true",
        default=False,
        required=False,
    )
    args = parser.parse_args()
    archive(**vars(args))
