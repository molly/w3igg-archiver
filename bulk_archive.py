import argparse

from archive import archive
from Database import Database

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Archive links in all Web3 is Going Just Great entries."
    )
    parser.add_argument(
        "--start",
        help="ID of the W3IGG entry to start archiving at (ordered descending, most to least recent)",
        required=False,
    )
    args = parser.parse_args()

    entry_ids = Database().get_all_entry_ids(args.start)
    for entry_id in entry_ids:
        print("\n\n============ Archiving {} ============".format(entry_id))
        archive(entry_id)
