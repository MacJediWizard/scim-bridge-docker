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

# --- Basic health check ---
@app.get("/")
async def healthcheck():
    return {"status": "running"}

# --- Future: SCIM Group handlers (optional) ---