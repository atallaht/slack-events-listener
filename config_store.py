"""Configuration store for slack-events-listener.

Reads and writes a simple KEY=VALUE file so the admin UI can edit settings.
Values in the environment always take precedence over the config file.
"""
import os
from pathlib import Path
from typing import Any

CONFIG_PATH = Path(os.environ.get("SLACK_CONFIG_PATH", "/data/config.env"))

DEFAULTS: dict[str, str] = {
    "SLACK_BIND": "",
    "SLACK_SOCKET_PATH": "/data-socket/events.sock",
    "SLACK_INBOX_PATH": "/data/inbox.jsonl",
    "SLACK_SIGNING_SECRET": "",
    "SLACK_ALLOWED_USER_ID": "",
    "SLACK_BOT_USER_ID": "",
}

RESTART_REQUIRED = {
    "SLACK_BIND",
    "SLACK_SOCKET_PATH",
    "SLACK_INBOX_PATH",
    "SLACK_SIGNING_SECRET",
    "SLACK_ALLOWED_USER_ID",
    "SLACK_BOT_USER_ID",
}

CATEGORIES: list[dict[str, Any]] = [
    {
        "name": "Slack App",
        "description": "Credentials and Slack-specific identifiers.",
        "fields": [
            {
                "key": "SLACK_SIGNING_SECRET",
                "label": "Slack signing secret",
                "type": "password",
                "help": "Your Slack app signing secret. Changes require restart.",
            },
            {
                "key": "SLACK_BOT_USER_ID",
                "label": "Bot user ID",
                "type": "text",
                "help": "Optional: your Slack bot's user ID, so it ignores its own messages.",
            },
            {
                "key": "SLACK_ALLOWED_USER_ID",
                "label": "Allowed user ID",
                "type": "text",
                "help": "Optional: only DMs from this Slack user ID are recorded.",
            },
        ],
    },
    {
        "name": "Paths",
        "description": "Filesystem paths for sockets and the event inbox.",
        "fields": [
            {
                "key": "SLACK_SOCKET_PATH",
                "label": "Socket path",
                "type": "text",
                "help": "Unix socket path when SLACK_BIND is not set.",
            },
            {
                "key": "SLACK_INBOX_PATH",
                "label": "Inbox path",
                "type": "text",
                "help": "Destination JSONL file for recorded events.",
            },
        ],
    },
    {
        "name": "Server",
        "description": "Network binding for the receiver.",
        "fields": [
            {
                "key": "SLACK_BIND",
                "label": "Bind address",
                "type": "text",
                "help": "Address to bind, e.g. 0.0.0.0:3010. Leave empty to use the Unix socket.",
            },
        ],
    },
]


def _parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, raw_value = line.partition("=")
        values[key.strip()] = raw_value.strip().strip("'\"")
    return values


def load_config() -> dict[str, str]:
    """Return the effective configuration.

    Environment variables override the config file. Defaults fill any missing keys.
    """
    file_values = _parse_env_file(CONFIG_PATH)
    effective = {}
    for key, default in DEFAULTS.items():
        effective[key] = os.environ.get(key, file_values.get(key, default))
    return effective


def load_file_config() -> dict[str, str]:
    """Return config values stored in the config file only."""
    file_values = _parse_env_file(CONFIG_PATH)
    return {key: file_values.get(key, DEFAULTS[key]) for key in DEFAULTS}


def save_config(values: dict[str, str]) -> None:
    """Write config values to the config file.

    Only keys in DEFAULTS are written. Empty values remove existing file entries
    so environment variables and defaults remain effective. Non-empty values
    override whatever is currently in the file.
    """
    existing = _parse_env_file(CONFIG_PATH)
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# slack-events-listener configuration\n"]
    for key in DEFAULTS:
        new_value = values.get(key)
        if new_value:
            lines.append(f'{key}="{new_value}"\n')
        elif key in existing and existing[key]:
            # Preserve non-empty existing value if user didn't clear it explicitly
            lines.append(f'{key}="{existing[key]}"\n')
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        f.writelines(lines)
