import os

from fastapi import Request
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware

JWT_SECRET = os.getenv("JWT_SECRET", "test_secret_for_testing_only")
JWT_ALGORITHM = "HS256"

PUBLIC_ROUTES = {
    "/health",
    "/auth/register",
    "/auth/login",
}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in PUBLIC_ROUTES:
            return await call_next(request)

        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            return JSONResponse(status_code=401, content={"detail": "Missing token"})

        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            request.state.user_id = payload["sub"]
            request.state.email = payload["email"]
        except JWTError:
            return JSONResponse(status_code=401, content={"detail": "Invalid token"})
        return await call_next(request)
