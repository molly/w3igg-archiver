from EntryLink import EntryLink


class ArchivableEntryLink(EntryLink):
    def __init__(self, link: dict):
        super().__init__(link)
        self.archive_href = None

    def get_link_for_database(self) -> object:
        """Return object formatted to fit the database schema."""
        return {
            "href": self.href,
            "linkText": self.link_text,
            "extraText": self.extra_text,
            "archiveHref": self.archive_href,
        }
