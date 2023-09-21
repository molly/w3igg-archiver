import os
import firebase_admin
from firebase_admin import credentials, firestore
from urllib.parse import urlparse

from ArchivableEntryLink import ArchivableEntryLink
from EntryLink import EntryLink
from Storage import Storage
from TweetEntryLink import TweetEntryLink


class Database:
    _instance = None
    app = None
    client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if Database.app is None:
            try:
                cred = credentials.Certificate(
                    "/Users/molly/Misc/web3-334501-5c7ea9ea0e88.json"
                )
                Database.app = firebase_admin.initialize_app(cred)
                Database.client = firestore.client()
            except Exception as error:
                print("Database connection error: {}".format(error))
            else:
                print("Database connected.")
        self.app = Database.app
        self.client = Database.client

    def __del__(self):
        firebase_admin.delete_app(self.app)

    def get_entry_links(self, entry_id: str) -> list[EntryLink]:
        """
        Get a list of links for the specified entry.
        :param entry_id: Date-formatted entry ID (YYYY-MM-DD-ID)
        :return: List of links in the specified entry
        """
        doc_ref = self.client.collection("entries").document(entry_id)
        doc = doc_ref.get()
        if doc.exists:
            entry = doc.to_dict()
            entry_links = []
            if "links" in entry:
                for link in entry["links"]:
                    if urlparse(link["href"]).netloc in ["twitter.com", "x.com"]:
                        entry_links.append(TweetEntryLink(link))
                    else:
                        entry_links.append(ArchivableEntryLink(link))
            return entry_links
        else:
            print("No document with ID {}".format(entry_id))
            return []

    def update_entry_with_archives(
        self, entry_id: str, archive_links: list[EntryLink]
    ) -> None:
        """
        Record archive data to the entry database.
        :param entry_id: Date-formatted entry ID (YYYY-MM-DD-ID)
        :param archive_links: Links with archive data for each link in the entry
        """
        doc_ref = self.client.collection("entries").document(entry_id)
        change_flag = False
        no_archives_counter = 0
        for idx, link in enumerate(archive_links):
            if link is not None:
                if (
                    isinstance(link, ArchivableEntryLink)
                    and link.archive_href is not None
                ):
                    change_flag = True
                elif (
                    isinstance(link, TweetEntryLink)
                    and link.archive_tweet_alt is not None
                ):
                    change_flag = True
                    link.archive_bucket_path = os.path.join(entry_id, link.index_str)
                    Storage().upload_files(link)
                    link.format_archive_data_for_upload()
                else:
                    no_archives_counter += 1
            else:
                no_archives_counter += 1

        if change_flag:
            doc_ref.update(
                {"links": [link.get_link_for_database() for link in archive_links]}
            )
            print("Entry updated with archive links.")
            if no_archives_counter:
                print("{} links not archived.".format(no_archives_counter))
        else:
            print("No archives to add to the entry.")
