from datetime import datetime, timedelta
from waybackpy import WaybackMachineSaveAPI, WaybackMachineCDXServerAPI
from waybackpy.exceptions import (
    WaybackError,
    NoCDXRecordFound,
    MaximumSaveRetriesExceeded,
)

USER_AGENT = "Web3 is Going Great archiver: https://github.com/molly/w3igg-archiver"


def save_url(link):
    url = link["href"]
    try:
        print("Trying to save a new copy of link {}: {}".format(link["index"], url))
        save_api = WaybackMachineSaveAPI(url, user_agent=USER_AGENT)
        link = save_api.save()
        print("Saved copy of link {}".format(link["index"]))
        return {"href": link, "type": "wayback"}
    except MaximumSaveRetriesExceeded as e:
        print(
            "Archive link {} ({}) exceeded max retries. {}".format(
                link["index"], url, e
            )
        )
    return None


def archive_url(link):
    """
    Get an archive link, either by retrieving a recently archived copy or creating one.

    :param link:  Dictionary of link details, including:
        link.url: String URL of the link to archive
        link.index: Index of this link in the links list
        (other parameters are unused)
    :return: String: Archive link, or None if save failed
    """
    url = link["href"]
    try:
        # Try to get a recent archived copy
        print("Looking for recent archive of link {}: {}".format(link["index"], url))
        cdx = WaybackMachineCDXServerAPI(
            url, user_agent=USER_AGENT, filters=["statuscode:200"], limit=1
        )
        newest = cdx.newest()
        expiry = datetime.now() - timedelta(days=30)
        if newest.datetime_timestamp < expiry:
            print("Found an archive of link {} but it's too old.".format(link["index"]))
            # Archived copy is >30d old, make a new copy
            return save_url(link)
        else:
            print("Found a recent archive of link {}.".format(link["index"]))
            return {"href": newest.archive_url, "type": "wayback"}
    except NoCDXRecordFound:
        print("Link {} has no archived copies.".format(link["index"]))
        return save_url(link)
    except WaybackError as e:
        print(e)
    return None
