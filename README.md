# slack-events-listener

A lightweight, containerized Slack Events API receiver. It listens for direct
messages and app mentions, verifies Slack request signatures, and writes events
to a JSONL inbox that any downstream service can read.

Use it as:

- A Slack-to-queue bridge for an autonomous agent such as Hermes.
- A webhook sink that turns Slack push events into structured local records.
- A starting point for a Slack bot backend.

## What it does

- Receives Slack events at `/slack/events`.
- Verifies the `X-Slack-Signature` header using your Slack signing secret.
- Handles the Slack URL-verification handshake automatically.
- Records accepted events to a JSONL file (`inbox.jsonl`) with metadata:
  `source`, `user`, `channel`, `text`, `event_ts`, and `ts`.
- Exposes a `/health` endpoint for container orchestration.
- Serves an `/admin` page to view and edit configuration.

## Supported events

| Slack event | Recorded as | Filter |
|-------------|-------------|--------|
| `message.im` | `source: dm` | Ignores bot messages and subtypes; optionally restricted to a single allowed user. |
| `app_mention` | `source: mention` | Ignores bot messages. |

## Files

- `slack_events_server.py` — Flask/Gunicorn receiver with signature verification.
- `admin_ui.py` — self-contained admin page and API.
- `config_store.py` — config file read/write.
- `Dockerfile` — production container image (Alpine Python 3.12).
- `hermes-slack-events.xml` — Unraid Docker template (example deployment).
- `nginx-slack.conf` — nginx location fragment to proxy `/slack/events`.
- `run.sh` — local development wrapper.
- `tests/` — pytest suite.

## Quick start

1. Create a Slack app and enable **Event Subscriptions**.
2. Add bot token scopes:
   - `app_mentions:read`
   - `im:history`
   - `im:read`
   - `chat:write` (only if your downstream service replies)
3. Subscribe to bot events:
   - `message.im`
   - `app_mention`
4. Set the Slack Request URL to:
   ```
   https://yourdomain/slack/events
   ```
5. Provide your Slack signing secret:
   ```bash
   export SLACK_SIGNING_SECRET='your-signing-secret'
   ```
6. Run locally:
   ```bash
   pip install -r requirements.txt
   python3 slack_events_server.py
   ```
   By default the server binds to a Unix socket at `/data-socket/events.sock`.
7. Send a test DM or mention; events appear in `inbox.jsonl`.

## Configuration

All values are optional unless marked required.

| Variable | Default | Purpose |
|----------|---------|---------|
| `SLACK_SIGNING_SECRET` *(required)* | — | Slack app signing secret. Also loaded from `/run/secrets/slack_signing_secret`, `/data/slack_signing_secret`, or `/config/slack_signing_secret` if not in env. |
| `SLACK_INBOX_PATH` | `/data/inbox.jsonl` | Destination JSONL file. |
| `SLACK_SOCKET_PATH` | `/data-socket/events.sock` | Unix socket path when no `SLACK_BIND` is set. |
| `SLACK_BIND` | `unix:{SLACK_SOCKET_PATH}` | Bind address, e.g. `0.0.0.0:3010` for TCP. |
| `SLACK_ALLOWED_USER_ID` | *(empty)* | If set, only DMs from this Slack user ID are recorded. |
| `SLACK_BOT_USER_ID` | *(empty)* | Your bot's user ID; its own messages are ignored. |

| `SLACK_CONFIG_PATH` | `/data/config.env` | Path to the admin-managed config file. |

## Admin UI

Open `/admin` in a browser to view and edit configuration. Values are saved to
`SLACK_CONFIG_PATH`. Environment variables still take precedence over the file.
Restart the container after saving for changes to take effect.

## Docker

Build and run with TCP:

```bash
docker build -t slack-events-listener .
docker run -d \
  -e SLACK_SIGNING_SECRET="$SLACK_SIGNING_SECRET" \
  -e SLACK_INBOX_PATH=/data/inbox.jsonl \
  -v "$(pwd)/data:/data" \
  -p 3010:3010 \
  slack-events-listener
```

Or mount a secrets file instead of exposing the secret in env:

```bash
docker run -d \
  -v "/path/to/slack_signing_secret:/run/secrets/slack_signing_secret:ro" \
  -v "$(pwd)/data:/data" \
  -p 3010:3010 \
  slack-events-listener
```

## Sample consumer

Read the inbox from a script:

```python
import json
from pathlib import Path

for line in Path("inbox.jsonl").read_text().splitlines():
    event = json.loads(line)
    print(event["source"], event["user"], event["text"])
```

Clear or rotate the file after processing to avoid duplicate handling.

## Hermes integration

For Hermes Agent specifically:

- Point `SLACK_INBOX_PATH` to a path Hermes can read on startup.
- `SLACK_ALLOWED_USER_ID` — set to your own Slack member ID so only your DMs
  become agent tasks.
- Use the included `nginx-slack.conf` to route public HTTPS traffic to the
  container's Unix socket, keeping the listener port-unbound on the host.

## Security

- Always configure the Slack signing secret in production. Without it, the
  server accepts unsigned events (useful only for local testing).
- Run the container as a non-root user in production.
- Keep `inbox.jsonl` on a volume restricted to the services that need it.

## License

MIT
