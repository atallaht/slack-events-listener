#!/usr/bin/env python3
"""Slack Events receiver for Hermes.

Listens on a Unix socket for Slack push events, verifies signatures,
and writes DM/mention replies to an inbox file for later pickup.
"""
import hashlib
import hmac
import json
import os
import stat
import time
from pathlib import Path

from flask import Flask, request, jsonify

from admin_ui import register_admin_routes

app = Flask(__name__)
register_admin_routes(app)

SOCKET_PATH = Path(os.environ.get("SLACK_SOCKET_PATH", "/data-socket/events.sock"))
INBOX_PATH = Path(os.environ.get("SLACK_INBOX_PATH", "/data/inbox.jsonl"))
ALLOWED_USER_ID = os.environ.get("SLACK_ALLOWED_USER_ID", "")
BOT_USER_ID = os.environ.get("SLACK_BOT_USER_ID", "")


def _load_secret(name: str, env_var: str, *candidate_paths: str) -> str:
    """Load a secret from env var or the first readable file path."""
    value = os.environ.get(env_var, "").strip()
    if value:
        return value
    for raw in candidate_paths:
        path = Path(raw)
        if path.exists() and path.is_file():
            try:
                return path.read_text().strip()
            except Exception:  # noqa: BLE001
                continue
    return ""


SLACK_SIGNING_SECRET = _load_secret(
    "signing secret",
    "SLACK_SIGNING_SECRET",
    "/run/secrets/slack_signing_secret",
    "/data/slack_signing_secret",
    "/config/slack_signing_secret",
)


def _log(msg: str) -> None:
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)


def _verify_slack_signature(request_body: bytes, timestamp: str, signature: str) -> bool:
    if not SLACK_SIGNING_SECRET:
        _log("WARNING: no Slack signing secret configured; accepting event unsigned")
        return True
    if not timestamp or not signature:
        return False
    basestring = f"v0:{timestamp}:{request_body.decode('utf-8')}".encode("utf-8")
    mac = hmac.new(SLACK_SIGNING_SECRET.encode("utf-8"), basestring, hashlib.sha256).hexdigest()
    expected = f"v0={mac}"
    return hmac.compare_digest(expected, signature)


def _append_inbox(record: dict) -> None:
    INBOX_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(INBOX_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


@app.route("/slack/events", methods=["POST"])
def slack_events():
    body = request.get_data()
    timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
    signature = request.headers.get("X-Slack-Signature", "")

    if not _verify_slack_signature(body, timestamp, signature):
        _log("Rejected event: invalid Slack signature")
        return jsonify({"error": "invalid signature"}), 403

    try:
        data = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError:
        return jsonify({"error": "bad json"}), 400

    # URL verification handshake
    if data.get("type") == "url_verification":
        challenge = data.get("challenge", "")
        _log("URL verification challenge received")
        return challenge, 200, {"Content-Type": "text/plain"}

    event = data.get("event", {})
    event_type = event.get("type")
    user = event.get("user", "")
    text = event.get("text", "")
    channel = event.get("channel", "")
    event_ts = event.get("event_ts", str(time.time()))
    subtype = event.get("subtype", "")

    # Ignore bot's own messages and message subtypes like message_changed/deleted
    if subtype or user == BOT_USER_ID:
        return jsonify({"ok": True}), 200

    if event_type == "message" and event.get("channel_type") == "im":
        if not ALLOWED_USER_ID or user == ALLOWED_USER_ID:
            _log(f"DM from {user}: {text[:80]!r}")
            _append_inbox({
                "ts": time.time(),
                "source": "dm",
                "user": user,
                "channel": channel,
                "text": text,
                "event_ts": event_ts,
            })
        else:
            _log(f"Ignored DM from {user}")

    elif event_type == "app_mention":
        _log(f"Mention in {channel} from {user}: {text[:80]!r}")
        _append_inbox({
            "ts": time.time(),
            "source": "mention",
            "user": user,
            "channel": channel,
            "text": text,
            "event_ts": event_ts,
        })

    return jsonify({"ok": True}), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "inbox": str(INBOX_PATH),
        "secret_loaded": bool(SLACK_SIGNING_SECRET),
    }), 200


def _cleanup_socket() -> None:
    if SOCKET_PATH.exists():
        SOCKET_PATH.unlink()


def _ensure_socket_parent() -> None:
    SOCKET_PATH.parent.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    bind_addr = os.environ.get("SLACK_BIND")
    if not bind_addr:
        bind_addr = f"unix:{SOCKET_PATH}"
        _ensure_socket_parent()
        _cleanup_socket()
    else:
        _log(f"Using TCP bind: {bind_addr} (socket setup skipped)")

    _log(f"Starting Slack events receiver on {bind_addr}")
    _log(f"Inbox: {INBOX_PATH}")
    _log(f"Signing secret loaded: {bool(SLACK_SIGNING_SECRET)}")

    try:
        from gunicorn.app.base import BaseApplication

        class UnixSocketApplication(BaseApplication):
            def __init__(self, app, options=None):
                self.options = options or {}
                self.application = app
                super().__init__()

            def load_config(self):
                for key, value in self.options.items():
                    self.cfg.set(key.lower(), value)

            def load(self):
                return self.application

        options = {
            "bind": bind_addr,
            "workers": 1,
            "worker_class": "sync",
            "timeout": 30,
            "accesslog": "-",
            "errorlog": "-",
        }

        # Post-fork: ensure the socket is world-writable so nginx can connect
        def post_fork(server, worker):
            if SOCKET_PATH.exists():
                os.chmod(SOCKET_PATH, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH)

        options["post_fork"] = post_fork

        UnixSocketApplication(app, options).run()
    finally:
        _cleanup_socket()
