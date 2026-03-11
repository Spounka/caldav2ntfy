import json
import logging
import pathlib
from datetime import datetime, timezone
from typing import cast

import icalendar
import inotify.adapters
import inotify.constants as constants
import requests
from icalendar.cal import Event

from caldav2ntfy.config import APP_NAME

logger = logging.getLogger(APP_NAME)

TOKEN = ""
SERVER = ""
TOPIC = ""


def create_calendar(file_path: pathlib.Path) -> icalendar.Calendar | None:
    if not file_path.exists():
        logger.error(f"Provided path {file_path.as_posix()} does not exist")
        return None
    component = icalendar.Calendar.from_ical(file_path.as_posix())
    return cast(icalendar.Calendar, component)


def get_timestamp_from_cal(event: Event) -> str:
    dt = event.decoded("DTSTART")

    # If it's an all-day event, convert date -> datetime
    if not isinstance(dt, datetime):
        dt = datetime.combine(dt, datetime.min.time())

    # Make it timezone-aware if needed
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)  # or your local tz

    return str(int(dt.timestamp()))  # Unix timestamp


def post_request(data: dict[str, str]) -> None:
    response = requests.post(
        f"{SERVER}", data=json.dumps(data), headers={"Authorization": f"Bearer {TOKEN}"}
    )
    logger.info(f"{response.status_code=}, id={data['sequence_id']}")
    if response.status_code >= 400:
        logger.error(response.text)


def get_notification_data(event: Event) -> dict[str, str]:
    summary = str(event.get("summary", ""))
    description = str(event.get("description", ""))
    return {
        "topic": TOPIC,
        "title": summary,
        "sequence_id": event.uid,
        "delay": get_timestamp_from_cal(event),
        "message": description,
    }


def cancel_notification(uuid: str) -> None:
    status = requests.delete(
        f"{SERVER}/{TOPIC}/{uuid}",
        headers={
            "Authorization": f"Bearer {TOKEN}",
        },
    )
    logging.info(f"Deleting notification {uuid}")
    logging.info(f"{status.status_code=}")


def main(server: str, token: str, topic: str, dir_path: str):
    global TOPIC
    global SERVER
    global TOKEN

    TOPIC = topic or ""
    SERVER = server or ""
    TOKEN = token or ""

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
                cal = create_calendar(file / filename)
                if cal is None:
                    logging.warning(f"No valid calendar under {file/filename}")
                    continue
                for e in cal.events:
                    data = get_notification_data(e)
                    post_request(data)

            elif type_name in ["IN_DELETE"]:
                logger.info(
                    f"Deleting notification with uid: {pathlib.Path(filename).stem}"
                )
                cancel_notification(
                    uuid=pathlib.Path(filename).stem,
                )
