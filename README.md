# SCIM Bridge Docker

A lightweight SCIM 2.0 bridge built with FastAPI and Docker.

**Created for Authentik ➔ Mailcow mailbox provisioning.**  
Built by MacJediWizard 🚀

---

## Features
- FastAPI SCIM 2.0 Server
- Automatic mailbox creation in Mailcow
- Automatic mailbox custom attribute updates (groups)
- Automatic promotion to Mailcow Domain Admins (based on SCIM group membership)
- Dockerized for easy deployment
- Secure SCIM token authentication
- Healthcheck endpoint
- Minimal dependencies, fast performance

---

## Getting Started

### 1. Clone and Build

```bash
git clone https://github.com/YOURUSERNAME/scim-bridge-docker.git
cd scim-bridge-docker
cp .env.example .env
# Edit the .env file with your secrets
docker compose up -d
```

---

## Environment Variables

| Variable        | Purpose |
|:----------------|:--------|
| `SCIM_TOKEN`    | Bearer token that Authentik will use to authenticate SCIM requests |
| `MAILCOW_API_URL` | URL to your Mailcow API endpoint (e.g., `https://mail.example.com/api/v1/`) |
| `MAILCOW_API_KEY` | API key generated from Mailcow Admin UI |
| `DEFAULT_DOMAIN` | Your primary Mailcow domain (e.g., `example.com`) |
| `API_PORT`      | (Optional) Port to expose SCIM server (default: 8484) |

---

## API Endpoints

| Path     | Method | Purpose |
|:---------|:------:|:--------|
| `/healthz` | `GET` | Healthcheck (`{"status": "running"}`) |
| `/ServiceProviderConfig` | `GET` | SCIM service provider metadata |
| `/Users` | `GET`, `POST`, `PUT` | Manage Mailcow mailbox users |
| `/Groups` | `GET`, `POST`, `PUT`, `PATCH` | Manage Mailcow mailbox group memberships via custom attributes |

---

## How it Works

1. Authentik SCIM provider syncs Users and Groups to the FastAPI SCIM Bridge.
2. The FastAPI app validates the SCIM bearer token.
3. The app creates mailboxes automatically via Mailcow Admin API.
4. Users' `custom-attributes` are updated with their SCIM group memberships.
5. If a user belongs to the special group "Mailcow Domain Admins", they are automatically promoted to a Domain Admin in Mailcow.

---

## Requirements

- Docker
- Docker Compose
- Git (to clone the repository)

---

## License

MIT License

---

> Made with ❤️ by [MacJediWizard Consulting, Inc.](https://macjediwizard.com)