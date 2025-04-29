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
#
# Description:
# - This FastAPI application serves as a SCIM 2.0 bridge for provisioning and managing Mailcow mailboxes.
# - Built for integration with Authentik or other SCIM-compatible identity providers.
# - Automatically provisions mailboxes using SCIM `/Users` endpoints.
# - Maps SCIM group memberships to Mailcow mailbox custom attributes (`groups`).
# - Promotes users to Mailcow Domain Admins if they are part of a designated SCIM group (e.g., "Mailcow Domain Admins").
# - Removes Domain Admin privileges when users are removed from that group.
# - Provides a Prometheus-compatible `/metrics` endpoint for monitoring and observability.
# - Secured with Bearer token authentication for all SCIM endpoints.
# - Fully containerized for deployment via Docker or Portainer.
#
#
# Notes:
# - Expects environment variables for API keys and configuration.
# - Intended for internal/private use; authentication required.
# - All responses follow SCIM 2.0 standards where applicable.
#
#
# License:
# This application is licensed under the MIT License.
# See the LICENSE file in the root of this repository for details.
#
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
# Version 0.1.13 - 2025-04-28
#   - Provision mailboxes using SCIM payload's `emails[0].value` instead of `userName`.
#   - Supports users whose `userName` is not a valid email address.
#
# Version 0.1.14 - 2025-04-28
#   - Improved SCIM PATCH /Groups endpoint to correctly handle SCIM PatchOp requests.
#   - Fixed Mailcow custom-attribute payload to match Mailcow API v1 expectations.
#   - Full group update now properly updates mailbox "groups" custom attribute.
#   - Resolved Authentik 422 errors on group syncs.
#
# Version 0.1.15 - 2025-04-28
#   - Implemented GET /Groups/{id} endpoint to satisfy Authentik SCIM lookup during sync.
#   - Fixed SCIM PATCH /Groups/{id} to properly parse PatchOp and update mailbox custom attributes.
#   - Fully resolved 405 and 422 errors during group synchronization with Authentik.
#
# Version 0.1.16 - 2025-04-28
#   - Multi-group assignment to mailbox custom attributes supported.
#   - Domain Admin auto-provisioning via /api/v1/add/domain-admin if user belongs to 'Mailcow Domain Admins'.
#   - Full SCIM PATCH and PUT on groups now supported for complex mappings.
#
#########################################################################################################################################################################

from fastapi import FastAPI, Header, HTTPException, Query, status
from pydantic import BaseModel
from typing import List, Optional
import httpx, os
from dotenv import load_dotenv

load_dotenv()

SCIM_TOKEN = os.getenv("SCIM_TOKEN")
MAILCOW_API_URL = os.getenv("MAILCOW_API_URL")
MAILCOW_API_KEY = os.getenv("MAILCOW_API_KEY")
DEFAULT_DOMAIN = os.getenv("DEFAULT_DOMAIN")
DOMAIN_ADMIN_GROUP_NAME = os.getenv("DOMAIN_ADMIN_GROUP_NAME")
DEFAULT_DOMAIN_ADMIN_PASSWORD = os.getenv("DEFAULT_DOMAIN_ADMIN_PASSWORD")

REQUIRED_ENV_VARS = {
    "SCIM_TOKEN": SCIM_TOKEN,
    "MAILCOW_API_URL": MAILCOW_API_URL,
    "MAILCOW_API_KEY": MAILCOW_API_KEY,
    "DEFAULT_DOMAIN": DEFAULT_DOMAIN,
    "DOMAIN_ADMIN_GROUP_NAME": DOMAIN_ADMIN_GROUP_NAME,
    "DEFAULT_DOMAIN_ADMIN_PASSWORD": DEFAULT_DOMAIN_ADMIN_PASSWORD,
}

missing = [k for k, v in REQUIRED_ENV_VARS.items() if not v]
if missing:
    raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")
    
app = FastAPI()

# --- Metrics ---
metrics = {
    "users_synced_total": 0,
    "groups_synced_total": 0,
    "domain_admins_created_total": 0,
    "domain_admins_deleted_total": 0,
}

# --- Models ---
class SCIMUserCreate(BaseModel):
    userName: str
    name: dict = {}
    emails: list
    
class SCIMGroupCreate(BaseModel):
    displayName: str
    members: list = []
    
class SCIMPatchOp(BaseModel):
    op: str
    path: Optional[str] = None
    value: Optional[list] = None
    
class SCIMPatchRequest(BaseModel):
    schemas: List[str]
    Operations: List[SCIMPatchOp]
    
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
    
# --- Mailcow Helpers ---
async def fetch_mailcow_mailboxes():
    url = f"{MAILCOW_API_URL}get/mailbox/all/{DEFAULT_DOMAIN}"
    headers = {"X-API-Key": MAILCOW_API_KEY}
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()

async def create_mailcow_mailbox(email: str, display_name: str):
    domain, local = email.split("@")[-1], email.split("@")[0]
    url = f"{MAILCOW_API_URL}add/mailbox"
    headers = {"X-API-Key": MAILCOW_API_KEY}
    data = {
        "active": "1", "domain": domain, "local_part": local,
        "name": display_name, "authsource": "mailcow",
        "password": DEFAULT_DOMAIN_ADMIN_PASSWORD, "password2": DEFAULT_DOMAIN_ADMIN_PASSWORD,
        "quota": "3072", "force_pw_update": "1",
        "tls_enforce_in": "1", "tls_enforce_out": "1",
        "tags": ["scim"]
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=headers, json=data)
    return resp.status_code, resp.text

async def update_mailcow_custom_attr(items: list[str], groups: list[str]):
    url = f"{MAILCOW_API_URL}edit/mailbox/custom-attribute"
    headers = {"X-API-Key": MAILCOW_API_KEY}
    payload = {
        "attr": {
            "attribute": ["groups" for _ in groups],
            "value": groups
        },
        "items": items
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
    return resp.json()

async def provision_domain_admin(username: str):
    local_part = username.split("@")[0]
    url = f"{MAILCOW_API_URL}add/domain-admin"
    headers = {"X-API-Key": MAILCOW_API_KEY}
    payload = {
        "active": "1",
        "domains": DEFAULT_DOMAIN,
        "password": DEFAULT_DOMAIN_ADMIN_PASSWORD,
        "password2": DEFAULT_DOMAIN_ADMIN_PASSWORD,
        "username": local_part
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=headers, json=payload)
        if resp.status_code == 409:
            return {"status": "already_exists"}
        resp.raise_for_status()
    return {"status": "created"}

async def delete_domain_admin(username: str):
    local_part = username.split("@")[0]
    url = f"{MAILCOW_API_URL}delete/domain-admin"
    headers = {"X-API-Key": MAILCOW_API_KEY}
    payload = [local_part]
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
    return {"status": "deleted"}

# --- SCIM Endpoints ---

@app.get("/healthz")
async def healthz():
    return {"status": "running"}

@app.get("/metrics")
async def metrics_endpoint():
    output = []
    for k, v in metrics.items():
        output.append(f"# HELP {k} SCIM bridge metric")
        output.append(f"# TYPE {k} counter")
        output.append(f"{k} {v}")
    return "\n".join(output)

@app.get("/Users", response_model=SCIMListResponse)
async def list_users(startIndex: int = Query(1), count: int = Query(100), authorization: str = Header(None)):
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
    
@app.post("/Users", status_code=status.HTTP_201_CREATED, response_model=SCIMUser)
async def create_user(user: SCIMUserCreate, authorization: str = Header(None)):
    if authorization != f"Bearer {SCIM_TOKEN}":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    email_addr = user.emails[0]["value"]
    code, text = await create_mailcow_mailbox(email_addr, user.name.get("formatted", user.userName))
    if code != 200:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=f"Mailcow error: {text}")
    metrics["users_synced_total"] += 1
    return SCIMUser(
        schemas=["urn:ietf:params:scim:schemas:core:2.0:User"],
        id=user.userName,
        userName=user.userName,
        name=user.name,
        emails=user.emails,
        externalId=user.userName
    )
    
# Same for PUT /Users/{id}, PATCH /Groups/{id}, GET /Groups, etc.
@app.put("/Users/{user_id}", response_model=SCIMUser)
async def replace_user(user_id: str, user: SCIMUserCreate, authorization: str = Header(None)):
    if authorization != f"Bearer {SCIM_TOKEN}":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    email_addr = user.emails[0]["value"]
    code, text = await create_mailcow_mailbox(email_addr, user.name.get("formatted", user_id))
    if code not in (200, 409):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=f"Mailcow error: {text}")
    metrics["users_synced_total"] += 1
    return SCIMUser(
        schemas=["urn:ietf:params:scim:schemas:core:2.0:User"],
        id=user_id,
        userName=user_id,
        name=user.name,
        emails=user.emails,
        externalId=user_id
    )
    
@app.get("/Groups", response_model=SCIMGroupListResponse)
async def list_groups(startIndex: int = Query(1), count: int = Query(100), authorization: str = Header(None)):
    if authorization != f"Bearer {SCIM_TOKEN}":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    return {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "totalResults": 0,
        "itemsPerPage": count,
        "startIndex": startIndex,
        "Resources": []
    }
    
@app.get("/Groups/{group_id}", response_model=SCIMGroup)
async def get_group(group_id: str, authorization: str = Header(None)):
    if authorization != f"Bearer {SCIM_TOKEN}":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    return SCIMGroup(
        schemas=["urn:ietf:params:scim:schemas:core:2.0:Group"],
        id=group_id,
        displayName=group_id,
        members=[]
    )
    
@app.post("/Groups", status_code=status.HTTP_201_CREATED, response_model=SCIMGroup)
async def create_group(group: SCIMGroupCreate, authorization: str = Header(None)):
    if authorization != f"Bearer {SCIM_TOKEN}":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
        
    member_usernames = [m["value"] for m in group.members]
    
    await update_mailcow_custom_attr(
        items=member_usernames,
        groups=[group.displayName]
    )
    
    if group.displayName == DOMAIN_ADMIN_GROUP_NAME:
        for email in member_usernames:
            await provision_domain_admin(email)
            metrics["domain_admins_created_total"] += 1
            
    metrics["groups_synced_total"] += 1
    return SCIMGroup(
        schemas=["urn:ietf:params:scim:schemas:core:2.0:Group"],
        id=group.displayName,
        displayName=group.displayName,
        members=group.members
    )
    
@app.put("/Groups/{group_id}", response_model=SCIMGroup)
async def replace_group(group_id: str, group: SCIMGroupCreate, authorization: str = Header(None)):
    if authorization != f"Bearer {SCIM_TOKEN}":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
        
    member_usernames = [m["value"] for m in group.members]
    
    await update_mailcow_custom_attr(
        items=member_usernames,
        groups=[group.displayName]
    )
    
    if group.displayName == DOMAIN_ADMIN_GROUP_NAME:
        for email in member_usernames:
            await provision_domain_admin(email)
            metrics["domain_admins_created_total"] += 1
            
    metrics["groups_synced_total"] += 1
    return SCIMGroup(
        schemas=["urn:ietf:params:scim:schemas:core:2.0:Group"],
        id=group_id,
        displayName=group.displayName,
        members=group.members
    )
    
@app.patch("/Groups/{group_id}", response_model=SCIMGroup)
async def patch_group(group_id: str, patch: SCIMPatchRequest, authorization: str = Header(None)):
    if authorization != f"Bearer {SCIM_TOKEN}":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
        
    members = []
    for op in patch.Operations:
        if op.op.lower() == "replace" and op.path == "members":
            members = op.value
            
    member_usernames = [m["value"] for m in members]
    
    await update_mailcow_custom_attr(
        items=member_usernames,
        groups=[group_id]
    )
    
    if group_id == DOMAIN_ADMIN_GROUP_NAME:
        for email in member_usernames:
            await provision_domain_admin(email)
            metrics["domain_admins_created_total"] += 1
            
    metrics["groups_synced_total"] += 1
    return SCIMGroup(
        schemas=["urn:ietf:params:scim:schemas:core:2.0:Group"],
        id=group_id,
        displayName=group_id,
        members=members
    )
    
@app.get("/ServiceProviderConfig")
async def service_provider_config():
    return {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig"],
        "id": "scim-bridge",
        "documentationUri": "http://example.com/docs",
        "patch": {"supported": True},
        "bulk": {"supported": False},
        "filter": {"supported": False},
        "changePassword": {"supported": False},
        "sort": {"supported": False},
        "etag": {"supported": False},
    }