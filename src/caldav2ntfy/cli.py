#!/bin/env python3

import logging
from argparse import ArgumentParser, Namespace
from copy import deepcopy
from typing import Any

from caldav2ntfy import app
from caldav2ntfy.config import APP_NAME, find_config, load_config, setup_logger

config: dict = {}


def parse_arguments() -> Namespace:
    parser = ArgumentParser()

    parser.add_argument("--config", help="Path to custom configuration file")
    parser.add_argument("--ntfy-server", help="Override ntfy url")
    parser.add_argument("--token", help="Override ntfy token")
    parser.add_argument("--topic", help="Override ntfy topic")
    return parser.parse_args()


def override_config_from_cli_params(
    args: Namespace, defaults: dict[str, Any]
) -> dict[str, str]:
    if args.ntfy_server:
        defaults["ntfy"]["server"] = args.ntfy_server
    if args.token:
        defaults["ntfy"]["token"] = args.token
    if args.topic:
        defaults["ntfy"]["topic"] = args.topic
    return defaults


def main():
    setup_logger()
    logger = logging.getLogger(APP_NAME)

    args = parse_arguments()

    config_path = find_config(args.config)

    config = load_config(config_path) if config_path else {}
    config = override_config_from_cli_params(args, config)

    print_config = deepcopy(config)
    print_config["ntfy"]["token"] = "****"
    logger.info(f"Loaded Config with the following params: {print_config}")
    app.main(
        server=config.get("ntfy", {}).get("server", ""),
        token=config.get("ntfy", {}).get("token", ""),
        topic=config.get("ntfy", {}).get("topic", ""),
        dir_path=config.get("app", {}).get("default_watch_dir", ""),
    )
