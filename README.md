# caldav2ntfy

`caldav2ntfy` is a lightweight **Linux CLI utility** that watches local **CalDAV calendar files** and sends **notifications to an ntfy server** when relevant calendar changes are detected.

It is primarily useful in **self-hosted environments** where a CalDAV server (for example **Radicale**) is used together with **ntfy** for push notifications.

The tool relies on **Linux inotify** to watch `.ics` files, parses calendar events, and publishes notifications to a configured **ntfy topic**.

---

## Use Cases

Typical setups where `caldav2ntfy` can be useful:

* Self-hosted **Radicale** calendar server
* **vdirsyncer** syncing CalDAV calendars locally
* Personal **ntfy server** for notifications
* Minimal **Linux automation environments**
* Lightweight **calendar reminder system without heavy clients**

Example workflow:

```
Radicale → calendar file change → caldav2ntfy → ntfy notification
```

---

## Features

* Watches CalDAV `.ics` files using **inotify**
* Sends notifications to an **ntfy topic**
* Configurable through a **TOML configuration file**
* Minimal dependencies
* Designed for **Linux environments**
* Simple CLI interface

---

## Installation

Install from PyPI:

```bash
pip install caldav2ntfy
```

---

## Configuration

`caldav2ntfy` is configured using a **TOML file**.

Example configuration:

```toml
[app]
default_watch_dir="/var/lib/radicale/collections/collection-root/<USER>/<CALENDAR>/"

[ntfy]
server="https://ntfy.sh"
topic="calendar_notif"
token="tk_xyzabc123="
```

---

## Usage

Run the watcher using:

```bash
caldav2ntfy --config config.toml
```

> [!NOTE]
> Alternatively, if you have `config.toml` in `$XDG_CONFIG_HOME/caldav2ntfy/` or `/etc/caldav2ntfy/`,
> you can simply run

```bash
caldav2ntfy
```

The program will monitor the configured calendar directory and send notifications when events are detected.

---

## Overriding the config

You can override parameters from the config before running
use `caldav2ntfy --help` to get a list of all available options

---

## How It Works

1. The program watches the calendar directory using **Linux inotify**.
2. When a calendar file changes, it parses the `.ics` content.
3. Relevant events are extracted.
4. A notification is sent to the configured **ntfy topic**.

---

## Requirements

* Python >= **3.11+**
* Linux (uses `inotify`)
* An **ntfy server**
* A CalDAV setup (Radicale, Nextcloud, etc.)

---

## Related Projects

* <https://ntfy.sh>
* <https://radicale.org>
* <https://vdirsyncer.pimutils.org>

---

## License

MIT License
