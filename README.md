# caldav2ntfy

This is a simple utility that lets you send notifications to an ntfy server on new caldav events

## Configuration

The cli utility expects config file in:

- $XDG_CONFIG_HOME/caldav2ntfy/config.toml
- /etc/caldav2ntfy/config.toml

> [!NOTE]
> You can pass a custom config file with `--config` flag

### Template Configuration file

```toml
[app]
default_watch_dir="/path/to/caldav/calendar/to/watch"

[ntfy]
server="https://ntfy.sh/"
topic="your_topic"
token="access_token_if_private"
```

## Run

`caldav2ntfy --config ~/.config/caldav2ntfy/config.toml --ntfy-server https://ntfy.sh/ --topic test_topic`
