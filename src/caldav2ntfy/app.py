import json
import logging
import pathlib
from datetime import datetime, timezone

import icalendar
import inotify.adapters
import inotify.constants as constants
import requests
from icalendar.cal import Event

from caldav2ntfy.config import APP_NAME

logger = logging.getLogger(APP_NAME)


def create_calendar(file_path: pathlib.Path) -> icalendar.Calendar | None:
    if not file_path.exists():
        logger.error(f"Provided path {file_path.as_posix()} does not exist")
        return None
    return icalendar.Calendar.from_ical(file_path)


def send_notification(event: Event, server: str, topic: str, token: str = "") -> None:
    logging.info(f"Sending notification for {event.summary} {event.description}")
    logging.info(f"Notification date: {str(event.start)}")
    dt = event.decoded("DTSTART").dt

    # If it's an all-day event, convert date -> datetime
    if not isinstance(dt, datetime):
        dt = datetime.combine(dt, datetime.min.time())

    # Make it timezone-aware if needed
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)  # or your local tz

    ntfy_at = str(int(dt.timestamp()))  # Unix timestamp
    response = requests.post(
        f"{server}",
        data=json.dumps(
            {
                "topic": topic,
                "title": event.summary,
                "sequence_id": event.uid,
                "delay": ntfy_at,
                "message": event.description,
            }
        ),
        headers={
            "Authorization": f"Bearer {token}",
        },
        # headers={"At": str(event.start)},
    )
    logger.info(f"{response.status_code=}, id={event.uid}")
    if response.status_code >= 400:
        logger.error(response.text)


def read_calendar_and_send_notification(
    file: pathlib.Path, filename: str, server: str, topic: str, token: str
) -> None:

    cal = create_calendar(file / filename)
    if cal is None:
        logging.warning(f"Calendar none {file/filename}")
        return
    for e in cal.events:
        send_notification(e, server, topic, token)


def cancel_notification(uuid: str, server: str, topic: str, token: str) -> None:
    status = requests.delete(
        f"{server}/{topic}/{uuid}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )
    logging.info(f"Deleting notification {uuid}")
    logging.info(f"{status.status_code=}")


def main(server: str, token: str, topic: str, dir_path: str):
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
                    file, filename, server, topic, token
                )

            elif type_name in ["IN_DELETE"]:
                logger.info(
                    f"Deleting notification with uid: {pathlib.Path(filename).stem}"
                )
                cancel_notification(
                    uuid=pathlib.Path(filename).stem,
                    server=server,
                    topic=topic,
                    token=token,
                )
                logger.info(f"Deleted a file {filename}")
