import logging
import tomllib
from pathlib import Path

APP_NAME = "caldav2ntfy"

_log_dir = Path.home() / ".local" / "share" / APP_NAME
_log_file = _log_dir / "output.log"


def setup_logger():
    _log_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(asctime)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S%z",
        handlers=[
            logging.FileHandler(_log_file, encoding="utf-8"),
        ],
    )


def find_config(cli_path: str | None = None) -> Path | None:
    candidates = []

    if cli_path:
        candidates.append(Path(cli_path).expanduser())

    xdg_config_home = Path.home() / ".config"
    candidates.append(xdg_config_home / APP_NAME / "config.toml")
    candidates.append(Path("/etc") / APP_NAME / "config.toml")

    for path in candidates:
        if path.is_file():
            return path
    return None


def load_config(path: Path) -> dict:
    with path.open("rb") as f:
        return tomllib.load(f)
