import os

import httpx
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/auth")

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")


@router.post("/register")
async def register(body: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{AUTH_SERVICE_URL}/register", json=body)
    return JSONResponse(status_code=response.status_code, content=response.json())


@router.post("/login")
async def login(body: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{AUTH_SERVICE_URL}/login", json=body)
    return JSONResponse(status_code=response.status_code, content=response.json())


@router.get("/me")
async def me(request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{AUTH_SERVICE_URL}/me", params={"token": token})
    return JSONResponse(status_code=response.status_code, content=response.json())
