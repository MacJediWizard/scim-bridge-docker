# SCIM Bridge Docker

A lightweight SCIM 2.0 bridge built with FastAPI and Docker.

**Created for Authentik ➔ Mailcow mailbox provisioning.**  
Built by MacJediWizard 🚀

---

## Features

- 🔐 Secure SCIM 2.0 Server using FastAPI
- 📬 Automatic mailbox provisioning in Mailcow
- 🧠 SCIM group → Mailcow mailbox custom attribute mapping (`groups`)
- 🛡️ Auto-promotion/removal to/from Mailcow Domain Admins via SCIM group membership
- 📈 Built-in `/metrics` endpoint for Prometheus / Grafana monitoring
- 🐳 Dockerized for fast, reproducible deployment
- ✅ SCIM standard support: `GET`, `POST`, `PUT`, `PATCH`
- 🔄 Sync-ready with Authentik SCIM provider

---

## Getting Started

### 1. Clone and Deploy

```bash
git clone https://github.com/YOURUSERNAME/scim-bridge-docker.git
cd scim-bridge-docker
cp .env.example .env
# Edit the .env file with your API keys, domain, and token
docker compose up -d
```

---

## Environment Variables

| Variable           | Description |
|--------------------|-------------|
| `SCIM_TOKEN`       | Bearer token used to authenticate SCIM requests |
| `MAILCOW_API_URL`  | Base URL of the Mailcow Admin API (e.g. `https://mail.example.com/api/v1/`) |
| `MAILCOW_API_KEY`  | Mailcow API Key with admin privileges |
| `DEFAULT_DOMAIN`   | Default domain for mailbox provisioning |
| `API_PORT`         | (Optional) Port to expose the FastAPI server (default: `8484`) |

---

## API Endpoints

| Path                      | Method(s)              | Description |
|---------------------------|------------------------|-------------|
| `/healthz`                | `GET`                  | Healthcheck endpoint |
| `/metrics`                | `GET`                  | Prometheus metrics (for Grafana) |
| `/ServiceProviderConfig`  | `GET`                  | SCIM metadata |
| `/Users`                  | `GET`, `POST`, `PUT`   | Sync and provision Mailcow users |
| `/Groups`                 | `GET`, `POST`, `PUT`, `PATCH` | Sync SCIM groups → Mailcow custom attributes |

---

## How It Works

1. Authentik SCIM sends a sync request to the FastAPI SCIM server.
2. The server authenticates via the provided SCIM bearer token.
3. SCIM `/Users` → Mailcow mailbox creation (with strong defaults).
4. SCIM `/Groups` → Mailcow mailbox `custom-attributes.groups` assignment.
5. If a user is added to the SCIM group **"Mailcow Domain Admins"**, the server will:
   - Automatically promote them via Mailcow's `/add/domain-admin`.
6. If the user is later removed from that group, they are demoted via `/delete/domain-admin`.

---

## Requirements

- 🐳 Docker + Docker Compose
- 🧠 Basic knowledge of SCIM and Mailcow API
- 🔐 A valid Mailcow admin API key
- ⚙️ Authentik instance or SCIM-compatible identity provider

---

## Monitoring

Export metrics to Prometheus:

```text
GET /metrics
```

Sample output:
```text
users_synced_total 42
groups_synced_total 17
domain_admins_created_total 4
domain_admins_deleted_total 2
```

---

## License

MIT License

---

> Made with ❤️ by [MacJediWizard Consulting, Inc.](https://macjediwizard.com)