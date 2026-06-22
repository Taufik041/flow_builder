![GitHub all releases](https://img.shields.io/github/downloads/Taufik041/flow_builder/total)
![GitHub language count](https://img.shields.io/github/languages/count/Taufik041/flow_builder)
![GitHub top language](https://img.shields.io/github/languages/top/Taufik041/flow_builder?color=yellow)
![GitHub issues](https://img.shields.io/github/issues/Taufik041/flow_builder)
![GitHub forks](https://img.shields.io/github/forks/Taufik041/flow_builder?style=social)
![GitHub Repo stars](https://img.shields.io/github/stars/Taufik041/flow_builder?style=social)

# WhatsApp Flow Builder

An AI-powered tool that generates [WhatsApp Flows](https://developers.facebook.com/docs/whatsapp/flows) JSON via a chat interface. Describe what you want, and the system generates valid Flow JSON, auto-validates it against Meta's validator, self-repairs errors, and produces webhook boilerplate — all in one go.

> Live demo: [flows.taufikkhan.me](https://flows.taufikkhan.me) (currently unavailable)

## Architecture

```
frontend (Next.js 16, :3000)
    └── api-gateway (FastAPI, :8000)
            ├── auth-service      (:8001)  — JWT auth, PostgreSQL
            ├── rag-service       (:8002)  — Qdrant vector search, WA Flows knowledge base
            └── generation-service(:8003)  — GPT-4o, two-phase generation, AiSensy
```

| Service | Port | Description |
|---|---|---|
| `frontend` | 3000 | Next.js 16 / React 19 / Tailwind CSS chat UI |
| `api-gateway` | 8000 | Auth middleware, request routing |
| `auth-service` | 8001 | Register / login / JWT verification |
| `rag-service` | 8002 | WhatsApp Flows spec indexing + retrieval (Qdrant) |
| `generation-service` | 8003 | Flow JSON generation, validation loop, AiSensy integration |
| `postgres` | 5432 | User accounts and sessions |
| `qdrant` | 6333 | Vector embeddings for RAG |

## How It Works

1. The user describes a flow in natural language via the chat UI.
2. The gateway forwards the request to the generation service.
3. **Phase 1 — JSON:** The generation service retrieves relevant WhatsApp Flows spec chunks from the RAG service, then streams a GPT-4o response. The resulting JSON is uploaded to AiSensy and validated by Meta's validator. If there are errors, the model repairs the JSON (up to `MAX_REPAIR_ATTEMPTS` times).
4. **Phase 2 — Backend:** Once valid JSON exists, a second GPT-4o call generates webhook handler boilerplate.
5. The finished flow is available for preview and publishing via AiSensy.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- An [OpenAI API key](https://platform.openai.com/api-keys)
- An [AiSensy](https://aisensy.com) account and API token

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/Taufik041/flow_builder.git
cd flow_builder
```

### 2. Configure environment variables

Copy the table below into a `.env` file at the project root and fill in your values:

```env
# PostgreSQL
POSTGRES_USER=postgres
POSTGRES_PASSWORD=yourpassword
POSTGRES_DB=flowbuilder
DATABASE_URL=postgresql+asyncpg://postgres:yourpassword@postgres:5432/flowbuilder

# Qdrant
QDRANT_URL=http://qdrant:6333

# Auth
JWT_SECRET=your-secret-key
JWT_EXPIRE_MINUTES=10080

# Internal service URLs (used inside Docker network)
AUTH_SERVICE_URL=http://auth-service:8001
RAG_SERVICE_URL=http://rag-service:8002
GENERATION_SERVICE_URL=http://generation-service:8003

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000

# File storage
UPLOAD_DIR=/uploads
GENERATED_DIR=/generated

# AI
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...   # optional

# AiSensy
AISENSY_TOKEN=your-aisensy-token
AISENSY_BASE_URL=https://apis.aisensy.com

# Flow endpoint (webhook host for generated flows)
FLOW_ENDPOINT_HOST=https://your-backend.example.com
FLOW_ENDPOINT_PREFIX=/flow

# Generation settings
MAX_REPAIR_ATTEMPTS=4
COOKIE_SECURE=false
```

### 3. Start the stack

```bash
docker compose up --build
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Development (without Docker)

### Backend services

Each service is a standard FastAPI app. From any service directory:

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port <PORT>
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend expects `NEXT_PUBLIC_API_URL=http://localhost:8000` in `frontend/.env.local`.

## Contributing

1. Use the Docker Compose stack for local testing.
2. Run linting before committing: `ruff check .`
3. Update this README whenever the architecture or setup steps change.

> [!IMPORTANT]
> You will need an OpenAI API key and an AiSensy token to run the backend. The `AISENSY_TOKEN` is required for flow validation and publishing.

> [!NOTE]
> WhatsApp Flow components reference: [Meta Developer Docs](https://developers.facebook.com/docs/whatsapp/flows/reference/components)

