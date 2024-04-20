from datetime import datetime, timedelta
from typing import Optional
from waybackpy import WaybackMachineSaveAPI, WaybackMachineCDXServerAPI
from waybackpy.exceptions import (
    WaybackError,
    NoCDXRecordFound,
    MaximumSaveRetriesExceeded,
    TooManyRequestsError
)

from ArchivableEntryLink import ArchivableEntryLink

USER_AGENT = "Web3 is Going Great archiver: https://github.com/molly/w3igg-archiver"


def save_url(link: ArchivableEntryLink) -> Optional[str]:
    """
    Save a new archived copy of the specified link.
    :param link: Link to archive
    :return: Archive URL, or None if archiving fails
    """
    try:
        print("Trying to save a new copy of link {}: {}".format(link.index, link.href))
        save_api = WaybackMachineSaveAPI(link.href, user_agent=USER_AGENT)
        archive_href = save_api.save()
        print("Saved copy of link {}".format(link.index))
        return archive_href
    except (MaximumSaveRetriesExceeded, TooManyRequestsError) as e:
        print(
            "Archive link {} ({}) exceeded max retries. {}".format(
                link.index, link.href, e
            )
        )
    return None


def archive_url(link: ArchivableEntryLink) -> None:
    """
    Get an archive link, either by retrieving a recently archived copy or creating one, and record its URL in the link
    instance.

    :param link: Link details for this given link
    :return: None
    """
    url = link.href
    try:
        # Try to get a recent archived copy
        print("Looking for recent archive of link {}: {}".format(link.index, url))
        cdx = WaybackMachineCDXServerAPI(
            url, user_agent=USER_AGENT, filters=["statuscode:200"], limit=1
        )
        newest = cdx.newest()
        expiry = datetime.now() - timedelta(days=30)
        if newest.datetime_timestamp < expiry:
            print("Found an archive of link {} but it's too old.".format(link.index))
            # Archived copy is >30d old, make a new copy
            link.archive_href = save_url(link)
        else:
            print("Found a recent archive of link {}.".format(link.index))
            link.archive_href = newest.archive_url
    except NoCDXRecordFound:
        print("Link {} has no archived copies.".format(link.index))
        link.archive_href = save_url(link)
    except WaybackError as e:
        print(e)
    return None
