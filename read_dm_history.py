#!/usr/bin/env python3
"""Read DM history from Slack. Reads bot token from /opt/data/.slack."""
import re
import subprocess
from pathlib import Path

TOKEN_FILE = Path("/opt/data/.slack")
text = TOKEN_FILE.read_text()
tokens = re.findall(r"xoxb-[A-Za-z0-9_-]+", text)
if not tokens:
    print("No xoxb token found")
    raise SystemExit(1)
token = tokens[0]
channel = "D0C1NF6HRL1"

r = subprocess.run(
    [
        "curl", "-s", "-X", "POST", "https://slack.com/api/conversations.history",
        "-H", f"Authorization: Bearer {token}",
        "-H", "Content-Type: application/x-www-form-urlencoded",
        "-d", f"channel={channel}&limit=10",
    ],
    capture_output=True,
    text=True,
)
print("HTTP exit:", r.returncode)
print(r.stdout[:3000])
