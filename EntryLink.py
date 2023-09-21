class EntryLink:
    def __init__(self, link: dict):
        self.href = link["href"]
        self.link_text = link["linkText"]
        self.extra_text = link.get("extraText", None)
        self._index = None
        self._index_str = None

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, value):
        self._index = value
        self._index_str = str(value)

    @property
    def index_str(self):
        return self._index_str

    @index_str.setter
    def index_str(self, value):
        raise Exception("This is a calculated value not intended to be set directly")

    def get_link_for_database(self) -> object:
        """Return object formatted to fit the database schema."""
        return {
            "href": self.href,
            "linkText": self.link_text,
            "extraText": self.extra_text,
        }
