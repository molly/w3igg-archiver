import concurrent.futures
from google.cloud import storage
import os

from constants import *


class Storage:
    client = None
    bucket = None

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

    def _upload_asset(self, paths):
        blob = self.bucket.blob(paths["remote"])
        blob.upload_from_filename(paths["local"])
        return paths["id"]

    def upload_files(self, unique_path, link_index):
        result = {}

        local_path = os.path.join(OUTPUT_DIR, link_index)
        if not os.path.exists(local_path):
            print("No assets have been saved at {}".format(local_path))
            return None

        # Upload screenshot
        screenshot_blob_path = os.path.join(unique_path, "screenshot.png")
        screenshot_blob = self.bucket.blob(screenshot_blob_path)
        screenshot_blob.upload_from_filename(os.path.join(local_path, "screenshot.png"))
        result["screenshot"] = screenshot_blob_path

        # Upload all assets
        asset_local_filenames = os.listdir(os.path.join(local_path, "assets"))
        asset_filenames = [
            {
                "id": local_filename,
                "local": os.path.join(local_path, "assets", local_filename),
                "remote": os.path.join(unique_path, "assets", local_filename),
            }
            for local_filename in asset_local_filenames
        ]
        if len(asset_filenames):
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=len(asset_filenames)
            ) as executor:
                filenames = list(executor.map(self._upload_asset, asset_filenames))
                result["assets"] = filenames

        return result
