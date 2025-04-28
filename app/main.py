#########################################################################################################################################################################
#
# MacJediWizard Consulting, Inc.
# Copyright (c) 2025 MacJediWizard Consulting, Inc.
# All rights reserved.
# Created by: William Grzybowski
#
# Script: main.py
#
# Description:
# - This FastAPI application serves as a SCIM 2.0 bridge for provisioning Mailcow mailboxes.
# - Designed for integration with Authentik or other SCIM-compatible identity providers.
# - Provides secure SCIM user creation endpoint protected by a bearer token.
# - Uses the Mailcow API to create mailboxes with default settings.
# - Supports containerized deployment via Docker for ease of management.
#
# Notes:
# - Expects environment variables for API keys and configuration.
# - Intended for internal/private use; authentication required.
# - All responses follow SCIM 2.0 standards where applicable.
#
# License:
# This application is licensed under the MIT License.
# See the LICENSE file in the root of this repository for details.
#
# Change Log:
# Version 0.1.0 - 2025-04-27
#   - Initial creation of SCIM bridge FastAPI application.
#
# Version 0.1.1 - 2025-04-28
#   - Updated documentation and added Portainer deployment instructions.
#   - Updated health check endpoint to /healthz.
#
# Version 0.1.2 - 2025-04-28
#   - Added curl installation to Dockerfile for health check functionality.
#   - Updated Dockerfile to install necessary dependencies.
#   - Updated health check in container to ensure service is running correctly.
#
#########################################################################################################################################################################


from fastapi import FastAPI, Request, Header, HTTPException
from pydantic import BaseModel
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

SCIM_TOKEN = os.getenv("SCIM_TOKEN")
MAILCOW_API_URL = os.getenv("MAILCOW_API_URL")
MAILCOW_API_KEY = os.getenv("MAILCOW_API_KEY")

app = FastAPI()

# --- Models for SCIM ---
class SCIMUser(BaseModel):
    userName: str
    name: dict
    emails: list

# --- Helper to create Mailcow mailbox ---
async def create_mailcow_mailbox(email: str, display_name: str):
    url = f"{MAILCOW_API_URL}admin/mailbox/add"
    headers = {"X-API-Key": MAILCOW_API_KEY}
    domain = email.split('@')[-1]
    data = {
        "domain": domain,
        "local_part": email.split('@')[0],
        "name": display_name,
        "password": "TempPass1234!",  # (or randomize if you want later)
        "password2": "TempPass1234!",
        "active": 1,
        "force_pw_update": 1
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=data)
    return response.status_code, response.text

# --- SCIM User creation endpoint ---
@app.post("/Users")
async def create_user(user: SCIMUser, authorization: str = Header(None)):
    if authorization != f"Bearer {SCIM_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")

    email = user.userName
    display_name = user.name.get("formatted", email)

    status, text = await create_mailcow_mailbox(email, display_name)

    if status == 200:
        return {"status": "success", "email": email}
    else:
        raise HTTPException(status_code=400, detail=f"Mailcow error: {text}")

# --- Health check endpoint ---
@app.get("/healthz")
async def healthcheck():
    return {"status": "running"}

# --- Future: SCIM Group handlers (optional) ---