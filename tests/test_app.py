import json
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import icalendar

from caldav2ntfy import app


class TestApp(unittest.TestCase):
    def test_create_calendar_returns_none_if_file_missing(self):
        missing = Path("/definitely/not/here/calendar.ics")
        result = app.create_calendar(missing)
        self.assertIsNone(result)

    @patch("caldav2ntfy.app.icalendar.Calendar.from_ical")
    def test_create_calendar_parses_existing_file(self, mock_from_ical):
        with tempfile.NamedTemporaryFile(suffix=".ics") as tmp:
            expected = object()
            mock_from_ical.return_value = expected

            result = app.create_calendar(Path(tmp.name))

            self.assertIs(result, expected)
            mock_from_ical.assert_called_once()

    def test_get_timestamp_from_cal_with_date(self):
        event = MagicMock()
        event.decoded.return_value = date(2026, 3, 10)

        ts = app.get_timestamp_from_cal(event)

        expected = int(datetime(2026, 3, 10, 0, 0, 0, tzinfo=timezone.utc).timestamp())
        self.assertEqual(ts, str(expected))

    def test_get_notification_data(self):
        event = MagicMock()
        event.summary = "Test title"
        event.uid = "abc-123"
        event.description = "Test body"
        event.decoded.return_value = datetime(2026, 3, 10, 12, 0, tzinfo=timezone.utc)

        app.TOPIC = "my-topic"
        data = app.get_notification_data(event)

        self.assertEqual(data["topic"], "my-topic")
        self.assertEqual(data["title"], "Test title")
        self.assertEqual(data["sequence_id"], "abc-123")
        self.assertEqual(data["message"], "Test body")
        self.assertEqual(
            data["delay"],
            str(int(datetime(2026, 3, 10, 12, 0, tzinfo=timezone.utc).timestamp())),
        )

    @patch("caldav2ntfy.app.requests.post")
    def test_post_request(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.text = ""

        app.SERVER = "https://ntfy.example.com"
        app.TOKEN = "secret"

        payload = {
            "topic": "topic",
            "title": "hello",
            "sequence_id": "id-1",
            "delay": "123456",
            "message": "body",
        }

        app.post_request(payload)

        mock_post.assert_called_once_with(
            "https://ntfy.example.com",
            data=json.dumps(payload),
            headers={"Authorization": "Bearer secret"},
        )

    @patch("caldav2ntfy.app.requests.delete")
    def test_cancel_notification(self, mock_delete):
        mock_delete.return_value.status_code = 200

        app.SERVER = "https://ntfy.example.com"
        app.TOKEN = "secret"
        app.TOPIC = "topic"

        app.cancel_notification("uuid-1")

        mock_delete.assert_called_once_with(
            "https://ntfy.example.com/topic/uuid-1",
            headers={"Authorization": "Bearer secret"},
        )
