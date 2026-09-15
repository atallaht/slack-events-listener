"""Admin UI for slack-events-listener.

Self-contained HTML/JS served from /admin. Editing and saving uses the
/admin/api/config endpoints.
"""
from flask import Response, request, jsonify

from config_store import CATEGORIES, RESTART_REQUIRED, load_file_config, save_config

ADMIN_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>slack-events-listener admin</title>
  <style>
    :root {
      --bg: #0f172a;
      --card: #1e293b;
      --text: #e2e8f0;
      --muted: #94a3b8;
      --accent: #38bdf8;
      --border: #334155;
      --danger: #f87171;
      --ok: #34d399;
    }
    * { box-sizing: border-box; }
    body {
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
      margin: 0;
      padding: 2rem;
    }
    h1 { margin: 0 0 0.25rem; }
    .subtitle { color: var(--muted); margin-bottom: 1.5rem; }
    .notice {
      background: rgba(248, 113, 113, 0.15);
      border: 1px solid var(--danger);
      color: var(--danger);
      padding: 0.75rem 1rem;
      border-radius: 0.5rem;
      margin-bottom: 1.5rem;
    }
    .card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 0.75rem;
      padding: 1.25rem;
      margin-bottom: 1.5rem;
    }
    .card h2 { margin: 0 0 0.25rem; font-size: 1.1rem; }
    .card p { margin: 0 0 1rem; color: var(--muted); }
    label {
      display: block;
      margin-bottom: 0.25rem;
      font-size: 0.9rem;
      font-weight: 600;
    }
    .field {
      margin-bottom: 1rem;
    }
    input[type="text"], input[type="password"] {
      width: 100%;
      padding: 0.5rem 0.75rem;
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 0.375rem;
      color: var(--text);
      font: inherit;
    }
    input[type="password"] { font-family: monospace; }
    .help {
      font-size: 0.8rem;
      color: var(--muted);
      margin-top: 0.25rem;
    }
    .badge {
      display: inline-block;
      font-size: 0.7rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      padding: 0.15rem 0.4rem;
      border-radius: 999px;
      margin-left: 0.5rem;
      vertical-align: middle;
    }
    .badge-restart { background: rgba(56, 189, 248, 0.15); color: var(--accent); }
    .actions {
      display: flex;
      gap: 0.75rem;
      margin-top: 1rem;
    }
    button {
      padding: 0.6rem 1.2rem;
      border: none;
      border-radius: 0.5rem;
      font: inherit;
      font-weight: 600;
      cursor: pointer;
    }
    .primary { background: var(--accent); color: #0f172a; }
    .secondary { background: var(--border); color: var(--text); }
    #status {
      margin-top: 1rem;
      font-size: 0.9rem;
      min-height: 1.5rem;
    }
    .ok { color: var(--ok); }
    .error { color: var(--danger); }
  </style>
</head>
<body>
  <h1>slack-events-listener admin</h1>
  <p class="subtitle">Configure the Slack events receiver. Most values require a container restart after saving.</p>
  <div class="notice">
    This page is not password protected. Run it only on a trusted network.
  </div>
  <div id="cards"></div>
  <div class="actions">
    <button class="primary" onclick="save()">Save configuration</button>
    <button class="secondary" onclick="reset()">Reset to saved values</button>
  </div>
  <div id="status"></div>

  <script>
    let categories = [];

    async function init() {
      const res = await fetch('/admin/api/config');
      const data = await res.json();
      categories = data.categories;
      render(data.values);
    }

    function render(values) {
      const container = document.getElementById('cards');
      container.innerHTML = categories.map(cat => `
        <div class="card">
          <h2>${escapeHtml(cat.name)}</h2>
          <p>${escapeHtml(cat.description)}</p>
          ${cat.fields.map(field => `
            <div class="field">
              <label for="${field.key}">
                ${escapeHtml(field.label)}
                ${field.restart ? '<span class="badge badge-restart">Restart required</span>' : ''}
              </label>
              <input type="${field.type}" id="${field.key}" name="${field.key}"
                value="${escapeHtml(values[field.key] || '')}">
              <div class="help">${escapeHtml(field.help)}</div>
            </div>
          `).join('')}
        </div>
      `).join('');
    }

    function escapeHtml(text) {
      const div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML;
    }

    function collectValues() {
      const values = {};
      categories.forEach(cat => {
        cat.fields.forEach(field => {
          values[field.key] = document.getElementById(field.key).value;
        });
      });
      return values;
    }

    async function save() {
      const status = document.getElementById('status');
      status.textContent = 'Saving...';
      status.className = '';
      try {
        const res = await fetch('/admin/api/config', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(collectValues())
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Save failed');
        status.textContent = 'Saved. Restart the container for changes to take effect.';
        status.className = 'ok';
      } catch (err) {
        status.textContent = 'Error: ' + err.message;
        status.className = 'error';
      }
    }

    async function reset() {
      await init();
      document.getElementById('status').textContent = 'Reloaded saved configuration.';
      document.getElementById('status').className = 'ok';
    }

    init();
  </script>
</body>
</html>
"""


def register_admin_routes(app):
    """Attach /admin routes to a Flask app."""

    @app.route("/admin", methods=["GET"])
    def admin_page():
        return Response(ADMIN_HTML, mimetype="text/html")

    @app.route("/admin/api/config", methods=["GET"])
    def admin_config_get():
        values = load_file_config()
        enriched_categories = []
        for cat in CATEGORIES:
            fields = []
            for field in cat["fields"]:
                enriched = dict(field)
                enriched["restart"] = field["key"] in RESTART_REQUIRED
                fields.append(enriched)
            enriched_categories.append({
                "name": cat["name"],
                "description": cat["description"],
                "fields": fields,
            })
        return jsonify({"categories": enriched_categories, "values": values})

    @app.route("/admin/api/config", methods=["POST"])
    def admin_config_post():
        data = request.get_json(silent=True) or {}
        # Only accept known keys
        cleaned = {key: data.get(key, "") for key in load_file_config()}
        save_config(cleaned)
        return jsonify({"ok": True})
