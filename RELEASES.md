# Release Notes

## v0.1.0 — First published image

### What's new

- **GitHub Container Registry publishing.** The repository now builds and pushes a Docker image automatically on every pushed tag and commit to `main`.
  - Image: `ghcr.io/atallaht/slack-events-listener`
  - Tags include semantic versions, branch names, and short SHA.
  - Images are signed with GitHub artifact attestations.
- **Unraid template updated.** `hermes-slack-events.xml` now references the published `ghcr.io/atallaht/slack-events-listener` image instead of the local-only `local/slack-events-listener` placeholder.
- **No runtime changes.** The container still listens on `0.0.0.0:3010` by default, verifies Slack signatures, and writes DMs/mentions to `/data/inbox.jsonl`.

### Upgrade from a local build

1. Stop the existing `slack-events-listener` container on Unraid.
2. In the Unraid Docker page, click the container ▼ → **Edit**.
3. Change **Repository** to:
   ```
   ghcr.io/atallaht/slack-events-listener
   ```
   Change **Registry** to:
   ```
   ghcr.io
   ```
4. Apply and start the container.
5. Docker will pull the latest `main` image. If the local image already exists with the same name, Unraid will use it unless you force a fresh pull via **Check for Updates** or `docker pull ghcr.io/atallaht/slack-events-listener` from the Unraid terminal.

### Private registry notes

This repository and its container registry are currently **private**. GitHub still allows pulling the image as long as the pull request is authenticated. On Unraid, authenticate once:

```bash
docker login ghcr.io -u atallaht -p <GITHUB_TOKEN>
```

Use a classic GitHub personal access token with `read:packages` scope. Store it in Unraid's Docker login or in `/root/.docker/config.json`. The GitHub Actions `GITHUB_TOKEN` used during publishing has package write access by default.

### Migrating to public for Community Apps

Before submitting to Unraid Community Applications:

1. Make the GitHub repository public (Settings → Change visibility).
2. In GitHub Package settings, change the `slack-events-listener` package visibility from **Private** to **Public**.
3. Update `hermes-slack-events.xml` if needed for the CA store (hosted template URL, author, support link).
4. Host the XML template on a public URL and submit it to the Unraid CA moderation thread.

### Full changelog

- Added `.github/workflows/docker-publish.yml` for automated ghcr.io builds.
- Updated `hermes-slack-events.xml` to use the ghcr.io image.
- Created this `RELEASES.md`.

### Known limitations

- The admin UI and config store are present in the image but the Dockerfile only copies `slack_events_server.py`. If you need the admin UI in the published image, the Dockerfile must also copy `admin_ui.py`, `config_store.py`, and any templates. That is intentionally left for a future release.
