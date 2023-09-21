import concurrent.futures
from google.cloud import storage
import os

from constants import *
from TweetEntryLink import TweetEntryLink


class Storage:
    _instance = None
    client = None
    bucket = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Storage, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if Storage.client is None:
            try:
                Storage.client = storage.Client(project="web3-334501")
            except Exception as error:
                print("Error connecting to storage: {}".format(error))
            else:
                print("Storage connected.")
        self.client = Storage.client
        self.bucket = self.client.get_bucket(BUCKET_NAME)

    def _upload_asset(self, paths: object) -> str:
        """
        Helper to pass to thread pool executor to upload a file to GCS.
        :param paths: Object containing id, local, and remote
        :return: Remote path of uploaded file
        """
        blob = self.bucket.blob(paths["remote"])
        blob.upload_from_filename(paths["local"])
        return paths["remote"]

    def upload_files(self, link: TweetEntryLink) -> None:
        """
        Upload screenshot and any asset images to bucket.
        :param link: Link with the screenshot and assets.
        :return: None
        """
        local_path = os.path.join(OUTPUT_DIR, link.index_str)
        if not os.path.exists(local_path):
            print("No assets have been saved at {}".format(local_path))
            return None

        # Upload screenshot
        screenshot_blob_path = os.path.join(link.archive_bucket_path, "screenshot.webp")
        screenshot_blob = self.bucket.blob(screenshot_blob_path)
        screenshot_blob.upload_from_filename(
            os.path.join(local_path, "screenshot.webp")
        )

        # Upload all assets
        asset_local_filenames = os.listdir(os.path.join(local_path, "assets"))
        asset_local_filenames.sort()
        asset_filenames = [
            {
                "id": local_filename,
                "local": os.path.join(local_path, "assets", local_filename),
                "remote": os.path.join(
                    link.archive_bucket_path, "assets", local_filename
                ),
            }
            for local_filename in asset_local_filenames
        ]
        if len(asset_filenames):
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=len(asset_filenames)
            ) as executor:
                remote_filenames = list(
                    executor.map(self._upload_asset, asset_filenames)
                )

            link.archive_tweet_assets_paths = remote_filenames
