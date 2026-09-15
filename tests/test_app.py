import json
import os
import tempfile
from pathlib import Path

import pytest

import config_store
from slack_events_server import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture
def tmp_config(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        config_path = Path(tmp) / "config.env"
        monkeypatch.setattr(config_store, "CONFIG_PATH", config_path)
        monkeypatch.setenv("SLACK_CONFIG_PATH", str(config_path))
        yield config_path


class TestConfigStore:
    def test_load_default_config(self, tmp_config):
        values = config_store.load_file_config()
        assert values["SLACK_SOCKET_PATH"] == "/data-socket/events.sock"
        assert values["SLACK_INBOX_PATH"] == "/data/inbox.jsonl"

    def test_save_and_load_config(self, tmp_config):
        config_store.save_config({
            "SLACK_BIND": "0.0.0.0:3010",
            "SLACK_ALLOWED_USER_ID": "U123",
            "SLACK_SIGNING_SECRET": "shhh",
        })
        values = config_store.load_file_config()
        assert values["SLACK_BIND"] == "0.0.0.0:3010"
        assert values["SLACK_ALLOWED_USER_ID"] == "U123"
        assert values["SLACK_SIGNING_SECRET"] == "shhh"

    def test_environment_overrides_file(self, tmp_config, monkeypatch):
        config_store.save_config({"SLACK_INBOX_PATH": "/file/inbox.jsonl"})
        monkeypatch.setenv("SLACK_INBOX_PATH", "/env/inbox.jsonl")
        values = config_store.load_config()
        assert values["SLACK_INBOX_PATH"] == "/env/inbox.jsonl"


    def test_save_preserves_existing_values(self, tmp_config):
        config_store.save_config({
            "SLACK_BIND": "0.0.0.0:3010",
            "SLACK_ALLOWED_USER_ID": "U123",
        })
        config_store.save_config({"SLACK_SIGNING_SECRET": "secret"})
        values = config_store.load_file_config()
        assert values["SLACK_BIND"] == "0.0.0.0:3010"
        assert values["SLACK_ALLOWED_USER_ID"] == "U123"
        assert values["SLACK_SIGNING_SECRET"] == "secret"


class TestAdminAPI:
    def test_admin_page_loads(self, client):
        response = client.get("/admin")
        assert response.status_code == 200
        assert b"slack-events-listener admin" in response.data

    def test_admin_api_config_get(self, client, tmp_config):
        response = client.get("/admin/api/config")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "categories" in data
        assert "values" in data
        assert data["values"]["SLACK_SOCKET_PATH"] == "/data-socket/events.sock"

    def test_admin_api_config_post(self, client, tmp_config):
        payload = {
            "SLACK_BIND": "0.0.0.0:3010",
            "SLACK_ALLOWED_USER_ID": "U123",
            "SLACK_SIGNING_SECRET": "secret",
        }
        response = client.post(
            "/admin/api/config",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert json.loads(response.data)["ok"] is True

        # Read back from file
        values = config_store.load_file_config()
        assert values["SLACK_BIND"] == "0.0.0.0:3010"
        assert values["SLACK_ALLOWED_USER_ID"] == "U123"
        assert values["SLACK_SIGNING_SECRET"] == "secret"


class TestSlackEventsEndpoint:
    def test_url_verification(self, client):
        response = client.post(
            "/slack/events",
            data=json.dumps({"type": "url_verification", "challenge": "hello"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.data == b"hello"

    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "ok"
