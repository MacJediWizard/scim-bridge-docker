# SCIM Bridge Docker

A lightweight SCIM 2.0 bridge built with FastAPI and Docker.

**Created for Authentik ➔ Mailcow mailbox provisioning.**  
Built by MacJediWizard 🚀

---

## Features
- FastAPI SCIM 2.0 Server
- Automatic mailbox creation in Mailcow
- Dockerized for easy deployment
- Secure SCIM token authentication
- Healthcheck endpoint
- Minimal dependencies, fast performance

---

## Getting Started

### 1. Clone and Build

\`\`\`bash
git clone https://github.com/YOURUSERNAME/scim-bridge-docker.git
cd scim-bridge-docker
cp .env.example .env
# Edit the .env file with your secrets
docker compose up -d
\`\`\`

---

## Environment Variables

| Variable        | Purpose |
|:----------------|:--------|
| `SCIM_TOKEN`    | Bearer token that Authentik will use to authenticate SCIM requests |
| `MAILCOW_API_URL` | URL to your Mailcow API endpoint (e.g., `https://mail.example.com/api/v1/`) |
| `MAILCOW_API_KEY` | API key generated from Mailcow Admin UI |
| `API_PORT`      | (Optional) Port to expose SCIM server (default: 8484) |

---

## API Endpoints

| Path     | Method | Purpose |
|:---------|:------:|:--------|
| `/`      | `GET`  | Healthcheck (`{"status": "running"}`) |
| `/Users` | `POST` | Create a new Mailcow mailbox based on SCIM user |

SCIM `/Users` POST will:
- Create a new Mailcow mailbox
- Set a temporary password
- Force password update on first login

---

## How it Works

1. Authentik SCIM provider calls `/Users` with a SCIM payload.
2. The FastAPI app validates the SCIM token.
3. The app sends a request to Mailcow Admin API to create the user mailbox.

---

## Requirements

- Docker
- Docker Compose
- Git (to clone)

---

## License

MIT License

---

> Made with ❤️ by [MacJediWizard Consulting, Inc.](https://macjediwizard.com)