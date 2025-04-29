# Deploying SCIM Bridge in Portainer

This guide explains how to deploy the SCIM Bridge Docker container into Portainer.

---

## Prerequisites

- A working Portainer instance (tested with CE 2.x / Business Edition)
- Docker Engine installed on the target node
- Access to the SCIM Bridge Docker image
- Your `.env` file ready (or environment variables filled manually)

---

## Steps

### 1. Create a New Stack

- In Portainer, go to **Stacks**
- Click **Add Stack**
- Name it something like:  
  `scim-bridge-docker`

---

### 2. Docker Compose YAML

Paste this `docker-compose.yml` in the editor:

```yaml
version: "3.9"

services:
  scim-bridge:
    image: scim-bridge-docker:latest
    container_name: scim-bridge
    ports:
      - "8484:8484"
    env_file:
      - .env
    restart: unless-stopped
```

**Important:**  
Make sure your `.env` file is uploaded and available to Portainer, or manually input the variables in the UI.

---

### 3. Environment Variables (Manual Alternative)

If you choose **not to use `.env`**, add the following manually in Portainer:

| Variable                    | Example Value                      |
|-----------------------------|------------------------------------|
| `SCIM_TOKEN`                | your-secure-token                  |
| `MAILCOW_API_URL`           | https://mail.example.com/api/v1/   |
| `MAILCOW_API_KEY`           | your-mailcow-api-key               |
| `DEFAULT_DOMAIN`            | example.com                        |
| `API_PORT`                  | 8484                               |
| `DEFAULT_DOMAIN_ADMIN_PASSWORD` | TempPass1234!                 |
| `DOMAIN_ADMIN_GROUP_NAME`   | Mailcow Domain Admins              |

---

### 4. Deploy the Stack

- Click **Deploy the stack**
- Wait for the container to become healthy
- Visit: `http://your-server:8484/healthz`

You should see:

```json
{"status": "running"}
```

---

### 5. Prometheus Monitoring (Optional)

You can configure Prometheus to scrape metrics from:

```
http://your-server:8484/metrics
```

This exposes metrics like:

- `users_synced_total`
- `groups_synced_total`
- `domain_admins_created_total`
- `domain_admins_deleted_total`

---

## Notes

- Ensure port `8484` is open in your firewall for SCIM/Prometheus access.
- Use a reverse proxy (e.g. Nginx, Traefik) for HTTPS termination in production.
- Protect the `/metrics` endpoint behind basic auth or firewall if needed.
- Keep your API token and Mailcow credentials secure!

---

> Built with ❤️ by [MacJediWizard Consulting, Inc.](https://macjediwizard.com)