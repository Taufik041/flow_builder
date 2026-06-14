# API Contract — WA Flow Generator

Derived from reading the actual source files on 2026-06-14. Every claim here maps to
a specific line of code. Anything that is **not yet implemented** is explicitly flagged.

---

## Service topology (from docker-compose.yaml)

| Service | Internal port | Host port |
|---|---|---|
| api-gateway | 8000 | **8000** |
| auth-service | 8001 | 8001 |
| rag-service | 8002 | 8002 |
| generation-service | 8003 | 8003 |
| postgres | 5432 | 5432 |
| qdrant | 6333 | 6333 |

**Frontend env var:** point `NEXT_PUBLIC_API_URL` (or equivalent) at `http://localhost:8000`.

> Note: `generation-service` is commented out of `api-gateway`'s `depends_on` list in
> docker-compose.yaml. The gateway does **not** proxy to it — see §5 below.

---

## CORS (api-gateway/main.py:21-27)

```
allow_origins:      ["http://localhost:3000"]
allow_credentials:  true
allow_methods:      ["*"]
allow_headers:      ["*"]
```

Only `http://localhost:3000` is whitelisted. Any other origin will be blocked.

---

## Auth middleware (api-gateway/middleware/auth.py)

**Public routes** (no token required):
```
GET  /health
POST /auth/register
POST /auth/login
```

Every other route requires:
```
Authorization: Bearer <jwt>
```

On success the middleware sets `request.state.user_id` (UUID as string) and
`request.state.email` on the request object. Downstream route handlers read from
`request.state`, not from Depends.

On failure:
- Missing header → `401 {"detail": "Missing token"}`
- Invalid / expired JWT → `401 {"detail": "Invalid token"}`

---

## Auth flow (proxy to auth-service:8001)

The gateway's `/auth` router blindly proxies the raw request body via httpx; it does
**not** validate the Pydantic schemas — that happens inside auth-service.

### POST /auth/register

**Request body** (validated by auth-service):
```json
{
  "email": "user@example.com",   // EmailStr
  "password": "plaintextpassword"
}
```

**Response 200:**
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

**Response 400** (email already exists):
```json
{ "detail": "Email already registered" }
```

### POST /auth/login

**Request body:**
```json
{
  "email": "user@example.com",
  "password": "plaintextpassword"
}
```

**Response 200:**
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

**Response 401** (wrong credentials):
```json
{ "detail": "Invalid credentials" }
```

### GET /auth/me  _(auth required)_

The gateway reads `Authorization: Bearer <jwt>` from the incoming request, strips the
prefix, and forwards the raw token as a **query parameter** to auth-service:
`GET http://auth-service:8001/me?token=<jwt>`

**Response 200:**
```json
{
  "id": "uuid-string",
  "email": "user@example.com"
}
```

**Response 401** (invalid token):
```json
{ "detail": "Invalid or expired token" }
```

### JWT claims (auth-service/auth.py:24-30)

| Claim | Value |
|---|---|
| `sub` | `str(user.id)` — UUID as string |
| `email` | user's email address |
| `exp` | `utcnow + JWT_EXPIRE_MINUTES` (default **10080 min = 7 days**) |

Algorithm: `HS256`. Key: env var `JWT_SECRET`.

> There is **no `tier` claim**. The middleware only extracts `sub` and `email`.

---

## Sessions (api-gateway/routers/sessions.py) — all auth required

### GET /sessions/

Returns all sessions for the authenticated user, ordered by `updated_at` descending.

**Response 200:**
```json
[
  {
    "id": "uuid",
    "user_id": "uuid",
    "title": "New Session",
    "created_at": "2026-06-14T10:00:00+00:00",
    "updated_at": "2026-06-14T10:00:00+00:00"
  }
]
```

Returns `[]` if the user has no sessions.

### POST /sessions/

**Request body:**
```json
{ "title": "My session" }   // optional; defaults to "New Session" if omitted
```

**Response 200:**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "title": "My session",
  "created_at": "2026-06-14T10:00:00+00:00",
  "updated_at": "2026-06-14T10:00:00+00:00"
}
```

### GET /sessions/{session_id}

Returns the session **and** all messages ordered by `created_at` ascending. Returns
404 if the session belongs to a different user.

**Response 200:**
```json
{
  "session": {
    "id": "uuid",
    "user_id": "uuid",
    "title": "My session",
    "created_at": "...",
    "updated_at": "..."
  },
  "messages": [
    {
      "id": "uuid",
      "session_id": "uuid",
      "role": "user",       // "user" | "assistant"
      "content": "...",
      "created_at": "..."
    }
  ]
}
```

**Response 404:**
```json
{ "detail": "Session not found" }
```

### DELETE /sessions/{session_id}

**Response 200:**
```json
{ "deleted": "uuid-string" }
```

**Response 404:**
```json
{ "detail": "Session not found" }
```

---

## Health check

### GET /health  _(public)_

**Response 200:**
```json
{ "status": "ok" }
```

---

## NOT IMPLEMENTED IN GATEWAY — generate / chat endpoint

**There is no `/generate`, `/chat`, or generation proxy route in the gateway.**

The generation-service (`POST /generate` on port 8003) exists and works, but the
gateway does **not** expose or proxy it. The gateway's `main.py` only registers
`auth.router` and `sessions.router`.

The generation-service must currently be called **directly** at
`http://localhost:8003/generate`.

### generation-service POST /generate (direct, not through gateway)

**Request body** (`generation-service/main.py` Pydantic model):
```json
{
  "user_message": "Create a registration form with name, phone, email",
  "extracted_text": null,          // optional — text extracted from uploaded PDF/image
  "chat_history": [],              // optional — [{"role": "user"|"assistant", "content": "..."}]
  "version": "7.3",                // optional — "7.3" (default) or "7.1"
  "top_k": 8,                      // optional — number of RAG chunks to retrieve
  "model": "gpt-4o"               // optional — see supported models below
}
```

Supported `model` values (`generation-service/generator.py`):
- `"gpt-4o"` (default) → `gpt-4o`
- `"gpt-4o-mini"` → `gpt-4o-mini`
- `"claude-sonnet"` → `claude-sonnet-4-20250514`
- `"claude-haiku"` → `claude-haiku-4-5-20251001`

**Response:** SSE stream (`text/event-stream`)

Each event:
```
data: {"token": "partial text here"}\n\n
```

Terminal event:
```
data: [DONE]\n\n
```

Response headers:
```
Cache-Control: no-cache
X-Accel-Buffering: no
```

**`chat_history` format** — the frontend must build and send this; the gateway does
**not** auto-inject it from the database:
```json
[
  {"role": "user", "content": "Previous user turn"},
  {"role": "assistant", "content": "Previous assistant turn"}
]
```

**`version` behaviour:** if `"7.1"` is passed, the user message is prefixed with
`[Use version 7.1]` before being sent to the LLM. Version `"7.3"` is the default and
sends the message unmodified.

---

## NOT IMPLEMENTED — file upload / download endpoints

The gateway database schema defines `UploadedFile` and `GeneratedFile` tables
(`api-gateway/models.py:54-81`), but **there are no `/files` routes registered
anywhere**. No upload endpoint, no download endpoint.

`requirements.txt` includes `python-multipart` (needed for `UploadFile`), but it is
unused.

---

## Database schema (api-gateway, SQLModel / PostgreSQL)

### sessions

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | uuid4 default |
| user_id | UUID | foreign key concept only (no FK constraint to auth-service) |
| title | str | default `"New Session"` |
| created_at | DateTime(tz) | UTC now |
| updated_at | DateTime(tz) | UTC now (not auto-updated on writes) |

### messages

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| session_id | UUID FK → sessions.id | |
| role | enum | `"user"` or `"assistant"` |
| content | str | |
| created_at | DateTime(tz) | |

### uploaded_files _(table exists, no endpoints)_

| Column | Type |
|---|---|
| id | UUID PK |
| session_id | UUID FK → sessions.id |
| file_name | str |
| file_path | str |
| file_type | enum: `"pdf"` \| `"image"` \| `"text"` |
| created_at | DateTime(tz) |

### generated_files _(table exists, no endpoints)_

| Column | Type |
|---|---|
| id | UUID PK |
| session_id | UUID FK → sessions.id |
| message_id | UUID FK → messages.id |
| file_type | enum: `"flow_json"` \| `"handler_py"` |
| file_path | str |
| version | str (default `"7.3"`) |
| created_at | DateTime(tz) |

---

## Environment variables (consumed by the stack)

| Var | Consumed by | Purpose |
|---|---|---|
| `DATABASE_URL` | api-gateway, auth-service | PostgreSQL DSN (`postgresql+asyncpg://...`) |
| `JWT_SECRET` | auth-service (sign), api-gateway (verify) | Must match in both services |
| `JWT_EXPIRE_MINUTES` | auth-service | Default 10080 (7 days) |
| `AUTH_SERVICE_URL` | api-gateway | Default `http://localhost:8001` |
| `RAG_SERVICE_URL` | generation-service | Default `http://rag-service:8002` |
| `OPENAI_API_KEY` | generation-service | Required for gpt-4o / gpt-4o-mini |
| `ANTHROPIC_API_KEY` | generation-service | Required for claude-sonnet / claude-haiku |
| `POSTGRES_USER` | docker-compose (postgres) | |
| `POSTGRES_PASSWORD` | docker-compose (postgres) | |
| `POSTGRES_DB` | docker-compose (postgres) | |

---

## Summary of gaps the frontend must account for

| Gap | Detail |
|---|---|
| No generate proxy in gateway | Call `http://localhost:8003/generate` directly, or add a proxy route to the gateway first |
| No file upload endpoint | `UploadedFile` table exists but no route; `extracted_text` must be extracted client-side or via a new endpoint |
| No generated file download | `GeneratedFile` table exists but no route; frontend must parse the SSE stream directly |
| `updated_at` not refreshed | Session `updated_at` is set on creation only — not updated when messages are added |
| `chat_history` not auto-injected | Gateway does not read message history from DB before forwarding to generation-service; frontend must send it |
| `tier` claim absent | JWT has no tier/plan field; no rate limiting or tier gating in current code |
