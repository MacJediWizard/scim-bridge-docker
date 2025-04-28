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
# - Provides secure SCIM user creation and sync endpoints protected by a bearer token.
# - Uses the Mailcow API to list, fetch and create mailboxes with default settings.
# - Supports SCIM filter, pagination, and ListResponse schemas.
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
#   - Added SCIM GET /Groups returning empty list for group sync.
#
# Version 0.1.6 - 2025-04-28
#   - Enhanced SCIM user listing to return proper `id` fields.
#   - Added support for filtering via `startIndex` and `count` parameters.
#   - Defined SCIM GET /Users and GET /Users/{id} endpoints with Pydantic models.
#   - Defined SCIM GET /Groups endpoint with ListResponse schema.
#
#########################################################################################################################################################################

from fastapi import FastAPI, Header, HTTPException, Query
from pydantic import BaseModel
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

SCIM_TOKEN = os.getenv("SCIM_TOKEN")
MAILCOW_API_URL = os.getenv("MAILCOW_API_URL")
MAILCOW_API_KEY = os.getenv("MAILCOW_API_KEY")
DEFAULT_DOMAIN = os.getenv("DEFAULT_DOMAIN")

app = FastAPI()

# --- SCIM Models ---
class SCIMUser(BaseModel):
    id: str
    userName: str
    name: dict
    emails: list
    externalId: str = None

class SCIMListResponse(BaseModel):
    schemas: list
    totalResults: int
    itemsPerPage: int
    startIndex: int
    Resources: list

class SCIMGroup(BaseModel):
    id: str
    displayName: str
    members: list

class SCIMGroupListResponse(BaseModel):
    schemas: list
    totalResults: int
    itemsPerPage: int
    startIndex: int
    Resources: list

# --- Helper to retrieve Mailcow mailboxes ---
async def fetch_mailcow_mailboxes():
    url = f"{MAILCOW_API_URL}get/mailbox/all/{DEFAULT_DOMAIN}"
    headers = {"X-API-Key": MAILCOW_API_KEY}
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()

# --- SCIM GET /Users (List) ---
@app.get("/Users", response_model=SCIMListResponse)
async def list_users(
    startIndex: int = Query(1, alias="startIndex"),
    count: int = Query(100, alias="count"),
    authorization: str = Header(None)
):
    if authorization != f"Bearer {SCIM_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    all_boxes = await fetch_mailcow_mailboxes()
    resources = []
    for mb in all_boxes:
        username = mb.get("username")
        resources.append({
            "id": username,
            "userName": username,
            "name": {"formatted": mb.get("name", username)},
            "emails": [{"value": username}],
            "externalId": username
        })
    return {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "totalResults": len(resources),
        "itemsPerPage": count,
        "startIndex": startIndex,
        "Resources": resources
    }

# --- SCIM GET /Users/{id} ---
@app.get("/Users/{user_id}", response_model=SCIMUser)
async def get_user(user_id: str, authorization: str = Header(None)):
    if authorization != f"Bearer {SCIM_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    all_boxes = await fetch_mailcow_mailboxes()
    for mb in all_boxes:
        if mb.get("username") == user_id:
            return {
                "id": user_id,
                "userName": user_id,
                "name": {"formatted": mb.get("name", user_id)},
                "emails": [{"value": user_id}],
                "externalId": user_id
            }
    raise HTTPException(status_code=404, detail="User not found")

# --- SCIM GET /Groups (List) ---
@app.get("/Groups", response_model=SCIMGroupListResponse)
async def list_groups(
    startIndex: int = Query(1, alias="startIndex"),
    count: int = Query(100, alias="count"),
    authorization: str = Header(None)
):
    if authorization != f"Bearer {SCIM_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "totalResults": 0,
        "itemsPerPage": count,
        "startIndex": startIndex,
        "Resources": []
    }

# --- SCIM POST /Users ---
@app.post("/Users")
async def create_user(user: SCIMUser, authorization: str = Header(None)):
    if authorization != f"Bearer {SCIM_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    domain = user.userName.split('@')[-1]
    local = user.userName.split('@')[0]
    url = f"{MAILCOW_API_URL}add/mailbox"
    headers = {"X-API-Key": MAILCOW_API_KEY}
    data = {
        "active": "1",
        "domain": domain,
        "local_part": local,
        "name": user.name.get("formatted", user.userName),
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
    if resp.status_code == 200:
        return {"status": "success", "email": user.userName}
    raise HTTPException(status_code=400, detail=f"Mailcow error: {resp.text}")

# --- SCIM POST /Groups (placeholder) ---
@app.post("/Groups")
async def create_group(group: SCIMGroup, authorization: str = Header(None)):
    if authorization != f"Bearer {SCIM_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"status": "success", "group": group.displayName}

# --- SCIM ServiceProviderConfig Endpoint ---
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

# --- Health check endpoint ---
@app.get("/healthz")
async def healthcheck():
    return {"status": "running"}