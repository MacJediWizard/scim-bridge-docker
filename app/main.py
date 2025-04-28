#!/usr/bin/env python3
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
# - Provides secure SCIM user and group provisioning endpoints protected by a bearer token.
# - Uses the Mailcow API to create mailboxes with default settings and to manage custom attributes.
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
#   - SCIM POST /Users now returns full SCIM User resource and HTTP 201.
#   - SCIM POST /Groups now returns full SCIM Group resource and HTTP 201.
#
# Version 0.1.7 - 2025-04-28
#   - Added SCIM PUT /Users/{id} to support Authentik full-sync updates.
#   - Added SCIM PUT /Groups/{id} and PATCH /Groups/{id} to avoid 404/405 during group sync.
#
# Version 0.1.8 - 2025-04-28
#   - Split SCIMUser/SCIMGroup into Create vs Resource models.
#   - POST /Users and PUT /Users/{id} now accept minimal payloads.
#   - No-op PUT/PATCH on Groups to satisfy Authentik sync.
#
# Version 0.1.9 - 2025-04-28
#   - Ensured mailbox provisioning on PUT /Users/{id} by calling Mailcow API.
#   - Added error handling for Mailcow API failures during full-sync updates.
#
# Version 0.1.10 - 2025-04-28
#   - Split SCIMUser/SCIMGroup into Create vs Resource models.
#   - POST & PUT /Users now accept minimal payloads and provision mailboxes.
#   - Error on Mailcow failure is surfaced as HTTP 400.
#
# Version 0.1.11 - 2025-04-28
#   - Introduced helper to update Mailcow mailbox custom attributes.
#   - Wire up Mailcow custom-attribute endpoint in all SCIM group operations.
#
# Version 0.1.12 - 2025-04-28
#   - Automatically set `groups` custom-attribute on mailboxes when SCIM POST/PUT/PATCH /Groups is invoked.
#   - Consolidated custom-attribute logic into `update_mailcow_custom_attr`.
#
#########################################################################################################################################################################

from fastapi import FastAPI, Header, HTTPException, Query, status
from pydantic import BaseModel
import httpx, os
from dotenv import load_dotenv

load_dotenv()

SCIM_TOKEN      = os.getenv("SCIM_TOKEN")
MAILCOW_API_URL = os.getenv("MAILCOW_API_URL")
MAILCOW_API_KEY = os.getenv("MAILCOW_API_KEY")
DEFAULT_DOMAIN  = os.getenv("DEFAULT_DOMAIN")

app = FastAPI()

# --- SCIM input models (minimal) ---
class SCIMUserCreate(BaseModel):
    userName: str
    name: dict = {}
    emails: list

class SCIMGroupCreate(BaseModel):
    displayName: str
    members: list = []

# --- SCIM output models (full) ---
class SCIMUser(BaseModel):
    schemas: list
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
    schemas: list
    id: str
    displayName: str
    members: list

class SCIMGroupListResponse(BaseModel):
    schemas: list
    totalResults: int
    itemsPerPage: int
    startIndex: int
    Resources: list

# --- Mailcow helpers ---
async def fetch_mailcow_mailboxes():
    url = f"{MAILCOW_API_URL}get/mailbox/all/{DEFAULT_DOMAIN}"
    headers = {"X-API-Key": MAILCOW_API_KEY}
    async with httpx.AsyncClient() as c:
        resp = await c.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()

async def create_mailcow_mailbox(email: str, display_name: str):
    domain, local = email.split("@")[-1], email.split("@")[0]
    url = f"{MAILCOW_API_URL}add/mailbox"
    headers = {"X-API-Key": MAILCOW_API_KEY}
    data = {
        "active": "1", "domain": domain, "local_part": local,
        "name": display_name, "authsource": "mailcow",
        "password": "TempPass1234!", "password2": "TempPass1234!",
        "quota": "3072", "force_pw_update": "1",
        "tls_enforce_in": "1", "tls_enforce_out": "1",
        "tags": ["scim"]
    }
    async with httpx.AsyncClient() as c:
        resp = await c.post(url, headers=headers, json=data)
    return resp.status_code, resp.text

async def update_mailcow_custom_attr(items: list[str], attribute_name: str, values: list[str]):
    """
    Call Mailcow custom-attribute endpoint to set attributes for given mailboxes.
    """
    url = f"{MAILCOW_API_URL}edit/mailbox/custom-attribute"
    headers = {"X-API-Key": MAILCOW_API_KEY}
    payload = {
        "attr": {"attribute": [attribute_name], "value": values},
        "items": items
    }
    async with httpx.AsyncClient() as c:
        resp = await c.post(url, headers=headers, json=payload)
    resp.raise_for_status()
    return resp.json()

# --- SCIM GET /Users ---
@app.get("/Users", response_model=SCIMListResponse)
async def list_users(
    startIndex: int = Query(1, alias="startIndex"),
    count: int = Query(100, alias="count"),
    authorization: str = Header(None)
):
    if authorization != f"Bearer {SCIM_TOKEN}":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    boxes = await fetch_mailcow_mailboxes()
    resources = [{
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "id": mb["username"],
        "userName": mb["username"],
        "name": {"formatted": mb.get("name", mb["username"])},
        "emails": [{"value": mb["username"]}],
        "externalId": mb["username"]
    } for mb in boxes]
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
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    for mb in await fetch_mailcow_mailboxes():
        if mb["username"] == user_id:
            return SCIMUser(
                schemas=["urn:ietf:params:scim:schemas:core:2.0:User"],
                id=user_id,
                userName=user_id,
                name={"formatted": mb.get("name", user_id)},
                emails=[{"value": user_id}],
                externalId=user_id
            )
    raise HTTPException(status.HTTP_404_NOT_FOUND)

# --- SCIM PUT /Users/{id} ---
@app.put("/Users/{user_id}", response_model=SCIMUser)
async def replace_user(
    user_id: str,
    user: SCIMUserCreate,
    authorization: str = Header(None)
):
    if authorization != f"Bearer {SCIM_TOKEN}":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    code, text = await create_mailcow_mailbox(user_id, user.name.get("formatted", user_id))
    if code not in (200, 409):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=f"Mailcow error: {text}")
    return SCIMUser(
        schemas=["urn:ietf:params:scim:schemas:core:2.0:User"],
        id=user_id,
        userName=user_id,
        name=user.name,
        emails=user.emails,
        externalId=user_id
    )

# --- SCIM POST /Users ---
@app.post("/Users", status_code=status.HTTP_201_CREATED, response_model=SCIMUser)
async def create_user(user: SCIMUserCreate, authorization: str = Header(None)):
    if authorization != f"Bearer {SCIM_TOKEN}":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    code, text = await create_mailcow_mailbox(user.userName, user.name.get("formatted", user.userName))
    if code != 200:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=f"Mailcow error: {text}")
    return SCIMUser(
        schemas=["urn:ietf:params:scim:schemas:core:2.0:User"],
        id=user.userName,
        userName=user.userName,
        name=user.name,
        emails=user.emails,
        externalId=user.userName
    )

# --- SCIM GET /Groups ---
@app.get("/Groups", response_model=SCIMGroupListResponse)
async def list_groups(
    startIndex: int = Query(1, alias="startIndex"),
    count: int = Query(100, alias="count"),
    authorization: str = Header(None)
):
    if authorization != f"Bearer {SCIM_TOKEN}":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    return {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "totalResults": 0,
        "itemsPerPage": count,
        "startIndex": startIndex,
        "Resources": []
    }

# --- SCIM POST /Groups ---
@app.post("/Groups", status_code=status.HTTP_201_CREATED, response_model=SCIMGroup)
async def create_group(group: SCIMGroupCreate, authorization: str = Header(None)):
    if authorization != f"Bearer {SCIM_TOKEN}":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    # Set custom 'groups' attribute on mailboxes
    await update_mailcow_custom_attr(
        items=[m["value"] for m in group.members],
        attribute_name="groups",
        values=[group.displayName]
    )
    return SCIMGroup(
        schemas=["urn:ietf:params:scim:schemas:core:2.0:Group"],
        id=group.displayName,
        displayName=group.displayName,
        members=group.members
    )

# --- SCIM PUT /Groups/{id} ---
@app.put("/Groups/{group_id}", response_model=SCIMGroup)
async def replace_group(group_id: str, group: SCIMGroupCreate, authorization: str = Header(None)):
    if authorization != f"Bearer {SCIM_TOKEN}":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    await update_mailcow_custom_attr(
        items=[m["value"] for m in group.members],
        attribute_name="groups",
        values=[group.displayName]
    )
    return SCIMGroup(
        schemas=["urn:ietf:params:scim:schemas:core:2.0:Group"],
        id=group_id,
        displayName=group.displayName,
        members=group.members
    )

# --- SCIM PATCH /Groups/{id} ---
@app.patch("/Groups/{group_id}", response_model=SCIMGroup)
async def update_group(group_id: str, group: SCIMGroupCreate, authorization: str = Header(None)):
    if authorization != f"Bearer {SCIM_TOKEN}":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    await update_mailcow_custom_attr(
        items=[m["value"] for m in group.members],
        attribute_name="groups",
        values=[group.displayName]
    )
    return SCIMGroup(
        schemas=["urn:ietf:params:scim:schemas:core:2.0:Group"],
        id=group_id,
        displayName=group.displayName,
        members=group.members
    )

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

# --- Health check endpoint ---
@app.get("/healthz")
async def healthz():
    return {"status": "running"}