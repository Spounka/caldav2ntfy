#!/bin/env python3

import json
import logging
import os
import pathlib
import sys
from datetime import datetime, timezone

import dotenv
import icalendar
import inotify.adapters
import inotify.constants as constants
import requests
from dotenv import dotenv_values

logger = logging.getLogger(__name__)
# import requests

dotenv.load_dotenv()


def create_calendar(file_path: pathlib.Path) -> icalendar.Calendar | None:
    if not file_path.exists():
        logger.error(f"Provided path {file_path.as_posix()} does not exist")
        return None
    return icalendar.Calendar.from_ical(file_path)


def read_calendar_and_send_notification(
    file: pathlib.Path, filename: str, url_root: str, topic: str, token: str
) -> None:

    cal = create_calendar(file / filename)
    if cal is None:
        logging.warning(f"Calendar none {file/filename}")
        return
    for e in cal.events:
        logging.info(f"Sending notification for {e.summary} {e.description}")
        logging.info(f"Notification date: {str(e.start)}")
        dt = e["DTSTART"].dt  # or: e.decoded("DTSTART")

        # If it's an all-day event, convert date -> datetime
        if not isinstance(dt, datetime):
            dt = datetime.combine(dt, datetime.min.time())

        # Make it timezone-aware if needed
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)  # or your local tz

        ntfy_at = str(int(dt.timestamp()))  # Unix timestamp
        response = requests.post(
            f"{url_root}",
            data=json.dumps(
                {
                    "topic": topic,
                    "title": e.summary,
                    "sequence_id": e.uid,
                    "delay": ntfy_at,
                    "message": e.description,
                }
            ),
            headers={
                "Authorization": f"Bearer {token}",
            },
            # headers={"At": str(e.start)},
        )
        logger.info(f"{response.status_code=}, id={e.uid}")
        if response.status_code >= 400:
            logger.error(response.text)


def cancel_notification(uuid: str, url_root: str, topic: str, token: str) -> None:
    status = requests.delete(
        f"{url_root}/{topic}/{uuid}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )
    logging.info(f"Deleting notification {uuid}")
    logging.info(f"{status.status_code=}")


def _main(dir_path: str, url_root: str):
    i = inotify.adapters.Inotify()

    logger.info(f"Dir root: {dir_path}")
    i.add_watch(
        dir_path,
        mask=(
            constants.IN_MOVE
            | constants.IN_MODIFY
            | constants.IN_CREATE
            | constants.IN_DELETE
        ),
    )

    topic = os.getenv("topic", "")
    token = os.getenv("token", "")

    logging.info(f"{topic=} {'TOKEN YES' if token != '' else 'TOKEN NONE'}")

    for event in i.event_gen(yield_nones=False):
        if event is None:
            continue
        _, type_names, file_path, filename = event

        file = pathlib.Path(file_path)
        for type_name in type_names:
            if pathlib.Path(filename).suffix != ".ics":
                continue
            if type_name in ["IN_MOVED_TO"]:
                read_calendar_and_send_notification(
                    file, filename, url_root, topic, token
                )

            elif type_name in ["IN_DELETE"]:
                logger.info(
                    f"Deleting notification with uid: {pathlib.Path(filename).stem}"
                )
                cancel_notification(
                    uuid=pathlib.Path(filename).stem,
                    url_root=url_root,
                    topic=topic,
                    token=token,
                )
                logger.info(f"Deleted a file {filename}")


def print_usage():
    print("Usage: <program> </path/to/dir> https://url_to_ntfy_server/")


def main():
    logging.basicConfig(filename="app.log", level=logging.INFO)
    if len(sys.argv) < 3:
        print("[ERROR]: Wrong number of arguments provided", file=sys.stderr)
        print_usage()
        exit(1)
    if len(sys.argv) > 3:
        print("[ERROR]: Extra arguments provided", file=sys.stderr)
        print_usage()
        exit(1)

    if not pathlib.Path(sys.argv[1]).exists():
        print(f"[ERROR]: Provided dir {sys.argv[1]} does not exist", file=sys.stderr)
        exit(1)

    dir_path = sys.argv[1]
    site_url = sys.argv[2]
    _main(dir_path, site_url)
    return 0


if __name__ == "__main__":
    main()
