#!/usr/bin/env python3
"""Send a test Slack DM. Reads bot token from /opt/data/.slack."""
import re
import subprocess
from pathlib import Path

TOKEN_FILE = Path("/opt/data/.slack")
text = TOKEN_FILE.read_text()
tokens = re.findall(r"xoxb-[A-Za-z0-9_-]+", text)
if not tokens:
    print("No xoxb token found in /opt/data/.slack")
    raise SystemExit(1)
token = tokens[0]

payload = '{"channel":"U0C1NA8SQTT","text":"Hermes Slack test: I can send you messages. Reply here and I will read it."}'
r = subprocess.run(
    [
        "curl", "-s", "-X", "POST", "https://slack.com/api/chat.postMessage",
        "-H", f"Authorization: Bearer {token}",
        "-H", "Content-Type: application/json; charset=utf-8",
        "-d", payload,
    ],
    capture_output=True,
    text=True,
)
print("HTTP exit:", r.returncode)
print(r.stdout[:1200])
