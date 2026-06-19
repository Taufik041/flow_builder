import os

import httpx
from fastapi import APIRouter, Request, Response, status
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/auth")

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")

COOKIE_NAME = "access_token"
COOKIE_MAX_AGE = 7 * 24 * 3600
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"


def _set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=COOKIE_MAX_AGE,
        path="/",
    )


@router.post("/register", status_code=status.HTTP_200_OK)
async def register(body: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{AUTH_SERVICE_URL}/register", json=body)
    data = response.json()
    out = JSONResponse(status_code=response.status_code, content=data)
    if response.status_code == 200 and "access_token" in data:
        _set_auth_cookie(out, data["access_token"])
    return out


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(body: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{AUTH_SERVICE_URL}/login", json=body)
    data = response.json()
    out = JSONResponse(status_code=response.status_code, content=data)
    if response.status_code == 200 and "access_token" in data:
        _set_auth_cookie(out, data["access_token"])
    return out


@router.get("/me", status_code=status.HTTP_200_OK)
async def me(request: Request):
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{AUTH_SERVICE_URL}/me", params={"token": token})
    return JSONResponse(status_code=response.status_code, content=response.json())


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout():
    out = JSONResponse(status_code=status.HTTP_200_OK, content={"ok": True})
    out.delete_cookie(key=COOKIE_NAME, path="/")
    return out
