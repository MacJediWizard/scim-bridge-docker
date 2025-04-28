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
# Version 0.1.3 - 2025-04-28
#   - Updated Mailcow API integration to correctly create mailboxes.
#   - Updated SCIM User creation endpoint to handle mailbox creation with proper parameters.
#   - Updated user creation logic to handle Mailcow API's expected mailbox fields.
#
# Version 0.1.4 - 2025-04-28
#   - Added SCIM ServiceProviderConfig endpoint to provide metadata for SCIM integrations.
#   - Added SCIM Groups endpoint for group creation (currently returns a mock success response).
#
# Version 0.1.5 - 2025-04-28
#   - Implemented SCIM GET /Users and GET /Users/{id} for full sync support.
#   - Added SCIM GET /Groups for full sync (returns empty list by default).
#
#########################################################################################################################################################################

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
import httpx, os
from dotenv import load_dotenv

load_dotenv()

SCIM_TOKEN = os.getenv("SCIM_TOKEN")
MAILCOW_API_URL = os.getenv("MAILCOW_API_URL")
MAILCOW_API_KEY = os.getenv("MAILCOW_API_KEY")
DEFAULT_DOMAIN = os.getenv("DEFAULT_DOMAIN")

app = FastAPI()

# --- Models for SCIM ---
class SCIMUser(BaseModel):
    userName: str
    name: dict
    emails: list
    
class SCIMGroup(BaseModel):
    displayName: str
    members: list
    
# --- Helper to create Mailcow mailbox ---
async def create_mailcow_mailbox(email: str, display_name: str):
    domain = email.split('@')[-1]
    local_part = email.split('@')[0]
    url = f"{MAILCOW_API_URL}add/mailbox"
    headers = {"X-API-Key": MAILCOW_API_KEY}
    data = {
        "active": "1",
        "domain": domain,
        "local_part": local_part,
        "name": display_name,
        "authsource": "mailcow",
        "password": "TempPass1234!",
        "password2": "TempPass1234!",
        "quota": "3072",
        "force_pw_update": "1",
        "tls_enforce_in": "1",
        "tls_enforce_out": "1",
        "tags": ["scim"]
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=headers, json=data)
    return resp.status_code, resp.text

# --- SCIM User creation endpoint ---
@app.post("/Users")
async def create_user(user: SCIMUser, authorization: str = Header(None)):
    if authorization != f"Bearer {SCIM_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    status, text = await create_mailcow_mailbox(user.userName, user.name.get("formatted", user.userName))
    if status == 200:
        return {"status": "success", "email": user.userName}
    raise HTTPException(status_code=400, detail=f"Mailcow error: {text}")
    
# --- SCIM list users for full sync ---
@app.get("/Users")
async def list_users(authorization: str = Header(None)):
    if authorization != f"Bearer {SCIM_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{MAILCOW_API_URL}get/mailbox/all/{DEFAULT_DOMAIN}", headers={"X-API-Key": MAILCOW_API_KEY})
    mailboxes = resp.json()
    resources = []
    for m in mailboxes:
        resources.append({
            "id": m["username"],
            "userName": m["username"],
            "name": {"formatted": m.get("name", m["username"])},
            "emails": [{"value": m["username"]}]
        })
    return {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "totalResults": len(resources),
        "startIndex": 1,
        "itemsPerPage": len(resources),
        "Resources": resources
    }
    
# --- SCIM get single user ---
@app.get("/Users/{user_id}")
async def get_user(user_id: str, authorization: str = Header(None)):
    if authorization != f"Bearer {SCIM_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    resp = await httpx.AsyncClient().get(f"{MAILCOW_API_URL}get/mailbox/{user_id}", headers={"X-API-Key": MAILCOW_API_KEY})
    m = resp.json()[0]
    return {
        "id": m["username"],
        "userName": m["username"],
        "name": {"formatted": m.get("name", m["username"])},
        "emails": [{"value": m["username"]}]
    }
    
# --- Health check ---
@app.get("/healthz")
async def healthcheck():
    return {"status": "running"}

# --- SCIM ServiceProviderConfig ---
@app.get("/ServiceProviderConfig")
async def service_provider_config():
    return {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig"],
        "id": "scim-bridge",
        "documentationUri": "http://example.com/docs",
        "patch": {"supported": True},
        "bulk": {"supported": True},
        "filter": {"supported": True},
        "changePassword": {"supported": False},
        "sort": {"supported": True},
        "etag": {"supported": True},
    }
    
# --- SCIM Groups endpoint (empty list) ---
@app.get("/Groups")
async def list_groups(authorization: str = Header(None)):
    if authorization != f"Bearer {SCIM_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "totalResults": 0,
        "startIndex": 1,
        "itemsPerPage": 0,
        "Resources": []
    }
    
# --- SCIM placeholder group create ---
@app.post("/Groups")
async def create_group(group: SCIMGroup, authorization: str = Header(None)):
    if authorization != f"Bearer {SCIM_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"status": "success", "group": group.displayName}
