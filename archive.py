import argparse
from database import Database


def archive(entry_id):
    if entry_id is None:
        print("Entry ID required.")
    else:
        db = Database()
        links = db.get_entry_links(entry_id)
        print(links)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Archive links in a given Web3 is Going Just Great entry."
    )
    parser.add_argument("entry_id", help="ID of the W3IGG entry, in numerical format.")
    args = parser.parse_args()
    archive(**vars(args))
