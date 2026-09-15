#!/bin/sh
# Quick local run wrapper for the Slack events receiver.
# In production, use the Unraid Docker container.
set -e

SOCKET_DIR="/opt/data/projects/sysdash/slack"
mkdir -p "$SOCKET_DIR"

export SLACK_SOCKET_PATH="${SOCKET_DIR}/events.sock"
export SLACK_INBOX_PATH="/opt/data/projects/hermes-slack-events/inbox.jsonl"

# Load secrets from disk if env vars are not set
[ -z "$SLACK_SIGNING_SECRET" ] && [ -f /opt/data/.slack-signing-secret ] && export SLACK_SIGNING_SECRET=$(cat /opt/data/.slack-signing-secret)
# Make the file available at the path the code expects when running locally
[ -f /opt/data/.slack-signing-secret ] && cp /opt/data/.slack-signing-secret /run/secrets/slack_signing_secret 2>/dev/null || true

cd /opt/data/projects/sysdash/slack
python3 slack_events_server.py
