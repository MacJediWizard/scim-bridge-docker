# Deploying SCIM Bridge in Portainer

This guide explains how to deploy the SCIM Bridge Docker container into Portainer easily.

---

## Prerequisites

- Working Portainer installation (tested with CE 2.x and Business Edition)
- Access to the SCIM Bridge Docker image
- Your `.env` file ready (or environment variables prepared)

---

## Steps

### 1. Create a New Stack

- In Portainer, navigate to **Stacks**.
- Click **Add Stack**.
- Name it something like:  
  `scim-bridge-docker`

---

### 2. Docker Compose YAML

Paste the following minimal `docker-compose.yml`:

\`\`\`yaml
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
\`\`\`

**Important:**  
Make sure the `.env` file is available to Portainer, or manually fill in environment variables.

---

### 3. Environment Variables (Alternative Method)

If you don't use `.env`, manually add these variables in Portainer UI:

Raw table:

Variable | Example Value
---------|---------------
`SCIM_TOKEN` | yourlongsecuretoken
`MAILCOW_API_URL` | https://mail.example.com/api/v1/
`MAILCOW_API_KEY` | your-mailcow-api-key
`API_PORT` | 8484

---

### 4. Deploy the Stack

- Click **Deploy the stack**.
- Wait until the container is up.
- Navigate to `http://your-server:8484/` to verify the healthcheck.

You should see:

\`\`\`json
{"status": "running"}
\`\`\`

---

## Notes

- Make sure Port 8484 is **open** on your firewall if external SCIM traffic is needed.
- Keep your SCIM Token **secret**.
- You can restrict access to trusted IPs via your reverse proxy if needed.
- Enable HTTPS termination in your proxy/load balancer if needed (recommended for production).

---

> Built with ❤️ by [MacJediWizard Consulting, Inc.](https://macjediwizard.com)