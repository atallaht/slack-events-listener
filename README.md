# Hermes Slack Events Listener

Receives Slack DMs and app-mention events, verifies signatures, and writes
them to `inbox.jsonl` so Hermes can read your replies on the next run.

## Files

- `slack_events_server.py` — Flask/Gunicorn event receiver.
- `Dockerfile` — container image.
- `hermes-slack-events.xml` — Unraid Docker template.
- `nginx-slack.conf` — nginx location fragment to proxy `/slack/events`.
- `run.sh` — local manual run wrapper (not needed in production).

## Setup

1. In Slack app settings, add bot scopes:
   - `app_mentions:read`
   - `im:history`
   - `im:read`
   - `chat:write`

2. Subscribe to bot events:
   - `message.im`
   - `app_mention`

3. Create the signing-secret file on Unraid:
   ```bash
   echo -n 'YOUR_SIGNING_SECRET' > /opt/data/.slack-signing-secret
   chmod 600 /opt/data/.slack-signing-secret
   ```

4. Build the image and create the container from the Unraid template.

5. Add the nginx location from `nginx-slack.conf` to your public Hermes host.

6. Set the Slack Request URL to:
   ```
   https://yourdomain/slack/events
   ```

7. Slack will send a URL-verification challenge; the server responds automatically.

## Hermes pickup

Hermes reads `/opt/data/projects/sysdash/slack/inbox.jsonl` at startup and can
act on queued messages. After processing, it should clear or rotate the file.
