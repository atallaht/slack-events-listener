#!/bin/sh
# Quick local run wrapper for the Slack events receiver.
# In production, use the Docker container or the Unraid template.
set -e

# Directory for the Unix socket. Change to match your environment.
SOCKET_DIR="${SOCKET_DIR:-/tmp/slack-events-listener}"
mkdir -p "$SOCKET_DIR"

export SLACK_SOCKET_PATH="${SLACK_SOCKET_PATH:-${SOCKET_DIR}/events.sock}"
export SLACK_INBOX_PATH="${SLACK_INBOX_PATH:-${SOCKET_DIR}/inbox.jsonl}"

# Load the signing secret from disk if the env var is not set.
if [ -z "$SLACK_SIGNING_SECRET" ] && [ -f "$HOME/.slack-signing-secret" ]; then
    export SLACK_SIGNING_SECRET=$(cat "$HOME/.slack-signing-secret")
fi

python3 slack_events_server.py
