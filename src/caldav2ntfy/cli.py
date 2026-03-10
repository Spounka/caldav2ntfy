import logging
from argparse import ArgumentParser

from caldav2ntfy.config import APP_NAME, find_config, load_config, setup_logger

config: dict = {}


def main():
    setup_logger()
    logger = logging.getLogger(APP_NAME)

    parser = ArgumentParser()

    parser.add_argument("--config", help="Path to custom configuration file")
    parser.add_argument("--ntfy-server", help="Override ntfy url")
    parser.add_argument("--token", help="Override ntfy token")
    parser.add_argument("--topic", help="Override ntfy topic")
    args = parser.parse_args()

    config_path = find_config(args.config)

    config = load_config(config_path) if config_path else {}
    if args.ntfy_server:
        config["ntfy"]["server"] = args.ntfy_server
    if args.token:
        config["ntfy"]["token"] = args.token
    if args.topic:
        config["ntfy"]["topic"] = args.topic
    logger.info(f"Loaded Config with the following params: {config}")
