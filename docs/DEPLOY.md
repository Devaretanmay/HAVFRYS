# Deploying the Volf GitHub App Daemon

## 1. GitHub App setup

1. Create a GitHub App with permissions: Contents (read/write), Pull requests
   (read/write), Issues (read/write). Subscribe to `pull_request`,
   `installation`, and `installation_repositories` events.
2. Set the webhook URL to `https://<host>:<port>/webhook` with a secret.
3. Install the App on selected repositories.

## 2. Required environment

| Variable | Required | Purpose |
|---|---|---|
| `VOLF_WEBHOOK_SECRET` | **yes** | HMAC validation. The daemon refuses to serve without it (`--no-secret` is local-debug only). |
| `GITHUB_TOKEN` or App `VOLF_GITHUB_APP_ID` + `VOLF_GITHUB_PRIVATE_KEY` | yes for private repos / PR writes | Clone auth and PR comments. Public repos work anonymously for clones. |
| `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` | only for AI repair | Deterministic repairs and checks run without any key. |
| `PORT` | no (default 8080) | Listen port. |
| `VOLF_REPOS_DIR`, `VOLF_INSTALLATIONS_DIR` | no | Managed checkouts and install records. Persist both (volume `/data`). |

## 3. Run with Docker

```bash
docker build -f docker/Dockerfile.app -t volf-app:1.1.0 .
docker run -d --name volf -p 8080:8080 --env-file .env -v volf-data:/data volf-app:1.1.0
```

With background monitoring (poll READY repos every 5 minutes):

```bash
docker run -d --name volf -p 8080:8080 --env-file .env -v volf-data:/data \
  volf-app:1.1.0 sh -c "volf app serve --port ${PORT:-8080} --watch 300"
```

## 4. Run on bare metal

```bash
pip install volf
export VOLF_WEBHOOK_SECRET=... GITHUB_TOKEN=...
volf app serve --port 8080 --watch 300
```

## 5. Verify

- `GET /health` → `{"status": "healthy"}`.
- `volf doctor` on the host shows GitHub CONNECTED once token env is set.
- Install the App on a test repo: an onboarding issue appears and the repo
  reaches READY; open a PR touching a migrated SDK to see the contract guard.

## 6. Security notes

- Missing webhook secret is a hard startup error, not a warning.
- Git credentials for private clones travel via `http.extraHeader`, never
  written to `.git/config`. AI keys live in 0600 files, never in repo state,
  logs, or knowledge (covered by `tests/test_credential_scoping.py`).
- Plaintext local credential files are operational storage, not enterprise
  encryption — say so in customer docs.
