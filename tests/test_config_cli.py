import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

from caldav2ntfy import cli, config


class TestConfig(unittest.TestCase):
    def test_load_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config.toml"
            path.write_text(
                """
[ntfy]
server = "https://ntfy.example.com"
token = "abc"
topic = "demo"

[app]
default_watch_dir = "/tmp/watch"
""".strip(),
                encoding="utf-8",
            )

            data = config.load_config(path)

            self.assertEqual(data["ntfy"]["server"], "https://ntfy.example.com")
            self.assertEqual(data["ntfy"]["token"], "abc")
            self.assertEqual(data["ntfy"]["topic"], "demo")
            self.assertEqual(data["app"]["default_watch_dir"], "/tmp/watch")

    def test_find_config_uses_cli_path_first(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config.toml"
            path.write_text("[ntfy]\nserver='x'\n", encoding="utf-8")

            result = config.find_config(str(path))

            self.assertEqual(result, path)


class TestCli(unittest.TestCase):
    def test_override_config_from_cli_params(self):
        defaults = {
            "ntfy": {
                "server": "old-server",
                "token": "old-token",
                "topic": "old-topic",
            }
        }
        args = Namespace(
            ntfy_server="new-server",
            token="new-token",
            topic="new-topic",
            config=None,
        )

        result = cli.override_config_from_cli_params(args, defaults)

        self.assertEqual(result["ntfy"]["server"], "new-server")
        self.assertEqual(result["ntfy"]["token"], "new-token")
        self.assertEqual(result["ntfy"]["topic"], "new-topic")

    @patch("caldav2ntfy.cli.app.main")
    @patch("caldav2ntfy.cli.load_config")
    @patch("caldav2ntfy.cli.find_config")
    @patch("caldav2ntfy.cli.parse_arguments")
    @patch("caldav2ntfy.cli.setup_logger")
    def test_main_wires_config_into_app(
        self,
        mock_setup_logger,
        mock_parse_arguments,
        mock_find_config,
        mock_load_config,
        mock_app_main,
    ):
        mock_parse_arguments.return_value = Namespace(
            config=None,
            ntfy_server=None,
            token=None,
            topic=None,
        )
        mock_find_config.return_value = Path("/fake/config.toml")
        mock_load_config.return_value = {
            "ntfy": {
                "server": "https://ntfy.example.com",
                "token": "secret",
                "topic": "demo",
            },
            "app": {
                "default_watch_dir": "/tmp/watch",
            },
        }

        cli.main()

        mock_setup_logger.assert_called_once()
        mock_app_main.assert_called_once_with(
            server="https://ntfy.example.com",
            token="secret",
            topic="demo",
            dir_path="/tmp/watch",
        )
