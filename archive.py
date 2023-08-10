import argparse
import concurrent.futures
from urllib.parse import urlparse

from database import Database
from twitter import archive_tweet
from wayback import archive_url


def archive_link(link):
    url = link["href"]
    parsed_url = urlparse(url)
    if parsed_url.netloc == "twitter.com":
        return archive_tweet(link)
    else:
        return archive_url(link)


def archive(entry_id):
    if entry_id is None:
        print("Entry ID required.")
        return
    db = Database()
    links = db.get_entry_links(entry_id)

    # Add an index parameter to the links to help with logging
    for idx, link in enumerate(links):
        link["index"] = idx

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(links)) as executor:
        archive_links = list(executor.map(archive_link, links))
        print("Done finding archive links")
        db.update_entry_with_archives(entry_id, archive_links)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Archive links in a given Web3 is Going Just Great entry."
    )
    parser.add_argument("entry_id", help="ID of the W3IGG entry, in numerical format.")
    args = parser.parse_args()
    archive(**vars(args))
