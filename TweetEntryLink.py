import re
from EntryLink import EntryLink


class TweetEntryLink(EntryLink):
    def __init__(self, link: dict):
        super().__init__(link)
        self.archive_bucket_path = link.get("archiveTweetPath")
        self.archive_tweet_alt = link.get("archiveTweetAlt")
        self._archive_tweet_assets = link.get("archiveTweetAssets", {})

        # Used to construct archiveTweetAssets field
        self.archive_tweet_assets_paths = []
        self.archive_tweet_assets_alt = {}
        self.archive_tweet_links = {}

    @property
    def archive_tweet_assets(self):
        return self._archive_tweet_assets

    @archive_tweet_assets.setter
    def archive_tweet_assets(self, value):
        raise Exception("This is a calculated value not intended to be set directly")

    def format_archive_data_for_upload(self) -> None:
        """
        Merge data about tweet archives for storage in the database.

        Creates an object keyed by the index of the tweet in the screenshot, containing the image count, list of links,
        and alt text.

        For example:
            {
              "0": {
                "images": 2,
                "links": ["http://example.com"],
                "alt": {
                  "0": "Alt text for first image",
                  "1": "Alt text for second image"
                }
              }
            }
        """
        if self.archive_tweet_assets_paths:
            for filepath in self.archive_tweet_assets_paths:
                filename = filepath.split("/")[-1]
                match = re.split(r"-|\.webp", filename)
                tweet_index_str = match[0]
                tweet_index = int(tweet_index_str)
                image_index_str = match[1]
                image_index = int(image_index_str)
                image_count = image_index + 1
                if tweet_index_str not in self._archive_tweet_assets:
                    self._archive_tweet_assets.setdefault(
                        tweet_index_str, {"images": 1}
                    )
                if image_count > self._archive_tweet_assets[tweet_index_str]["images"]:
                    self._archive_tweet_assets[tweet_index_str]["images"] = image_count
                if self.archive_tweet_assets_alt is not None and len(
                    self.archive_tweet_assets_alt
                ):
                    alt = self.archive_tweet_assets_alt.get(tweet_index, {}).get(
                        image_index
                    )
                    if alt:
                        if "alt" not in self._archive_tweet_assets[tweet_index_str]:
                            self._archive_tweet_assets[tweet_index_str]["alt"] = {}
                        self._archive_tweet_assets[tweet_index_str]["alt"][
                            image_index_str
                        ] = alt

        if self.archive_tweet_links:
            for key in self.archive_tweet_links.keys():
                key_str = str(key)
                if len(self.archive_tweet_links[key]):
                    if key_str in self._archive_tweet_assets:
                        self._archive_tweet_assets[key_str][
                            "links"
                        ] = self.archive_tweet_links[key]
                    else:
                        self._archive_tweet_assets[key_str] = {
                            "links": self.archive_tweet_links[key]
                        }

    def get_link_for_database(self) -> object:
        """Return object formatted to fit the database schema."""
        db_data = {
            "href": self.href,
            "linkText": self.link_text,
            "extraText": self.extra_text,
            "archiveTweetAlt": self.archive_tweet_alt,
            "archiveTweetPath": self.archive_bucket_path,
        }
        if self.archive_tweet_assets:
            db_data["archiveTweetAssets"] = self.archive_tweet_assets
        return db_data

    def clear_old_archive_data(self) -> None:
        """Clear old archive data to avoid accidentally keeping outdated info if we're going to re-archive."""
        self.archive_bucket_path = None
        self.archive_tweet_alt = None
        self._archive_tweet_assets = {}
        self.archive_tweet_assets_paths = []
        self.archive_tweet_assets_alt = {}
        self.archive_tweet_links = {}
