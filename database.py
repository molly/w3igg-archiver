import firebase_admin
from firebase_admin import credentials, firestore


class Database:
    app = None
    client = None

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

    def get_entry_links(self, entry_id):
        doc_ref = self.client.collection("entries").document(entry_id)
        doc = doc_ref.get()
        if doc.exists:
            entry = doc.to_dict()
            if "links" in entry:
                return entry["links"]
            return {}
        else:
            print("No document with ID {}".format(entry_id))

    def update_entry_with_archives(self, entry_id, archive_links):
        doc_ref = self.client.collection("entries").document(entry_id)
        doc = doc_ref.get()
        entry = doc.to_dict()

        change_flag = False
        no_archives_counter = 0
        updated_links = entry["links"].copy()
        for idx, link in enumerate(archive_links):
            if link is not None:
                if link["type"] == "wayback":
                    change_flag = True
                    updated_links[idx]["archiveHref"] = link["href"]
            else:
                no_archives_counter += 1

        if change_flag:
            doc_ref.update({"links": updated_links})
            print("Entry updated with archive links.")
            if no_archives_counter:
                print("{} links not archived.".format(no_archives_counter))
        else:
            print("No archives to add to the entry.")
