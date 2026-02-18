# Documentation MCP — Final Implementation Plan

---

## Infra Stack

- **Backend:** FastAPI + FastMCP
- **Queue:** Redis + Celery
- **Database:** Postgres + PGVector (SQLModel as an ORM)
- **Frontend:** Minimal monospace UI (React/Tailwind optional)
- **Package Manager:** **uv**
- **Docker Compose:** Single file orchestrating backend, celery worker, Redis, Postgres, frontend
- **Domains:**
  - `mcp.domain` → MCP server
  - `app.domain` → Dashboard

- **Env Variables:**

```
REDIS_URL=redis://redis:6379/0
POSTGRES_CONNECTION_STRING=postgresql://user:password@db:5432/docmcp
MCP_SERVER_TOKEN=super-secret-token
EMBEDDING_MODEL=bedrock:amazon.titan-embed-text-v2:0
EMBEDDING_DIMENSION=1024
EMBEDDING_BATCH_SIZE=64
EMBEDDING_MAX_RETRIES=3
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=docmcp
```

---

## Phase 0 — Project Structure

```
docmcp/
├─ backend/
│  ├─ app/
│  │  ├─ main.py
│  │  ├─ api/
│  │  ├─ models/
│  │  └─ services/
│  ├─ pyproject.toml
|  ├─ uv.lock
│  └─ Dockerfile
├─ frontend/
│  ├─ src/
│  ├─ uv.toml
│  └─ Dockerfile
├─ docker-compose.yml
└─ .env
```

---

## Phase 1 — Database Schema

```sql
-- Documentation
CREATE TABLE documentation (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url TEXT UNIQUE NOT NULL,
    title TEXT,
    last_synced TIMESTAMP,
    cron_schedule TEXT,
    crawl_depth INT DEFAULT 3,
    include_patterns TEXT[],
    exclude_patterns TEXT[],
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

-- Documentation Sections
CREATE TABLE documentation_section (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    documentation_id UUID REFERENCES documentation(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES documentation_section(id) ON DELETE CASCADE,
    path TEXT NOT NULL,
    title TEXT,
    summary TEXT,
    content TEXT,
    level INT,
    url TEXT,
    token_count INT,
    embedding VECTOR(1536),
    checksum TEXT,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

-- Ingestion Jobs
CREATE TABLE ingestion_job (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    documentation_id UUID REFERENCES documentation(id),
    status TEXT,
    error_message TEXT,
    progress_percent INT DEFAULT 0,
    pages_processed INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

-- Raw Pages (optional)
CREATE TABLE raw_page (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    documentation_id UUID REFERENCES documentation(id),
    url TEXT,
    html_content TEXT,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);
```

---

## Phase 2 — Ingestion Pipeline

### 2.1 Flow

1. POST `/documentation/ingestion`
   - Input: `{ web_url, crawl_depth?, include_patterns?, exclude_patterns? }`
   - Create Documentation & IngestionJob (status `PENDING`)
   - Trigger Celery task

2. Celery Worker:
   - Status `CRAWLING` → Crawl website via crawl4ai
   - Save each page to `raw_page`
   - Status `PARSING` → Parse into hierarchical sections
   - Compute `checksum`, generate `DocumentationSection`
   - Status `EMBEDDING` → Reserved stub in this phase
   - Status `INDEXING` → Reserved stub in this phase
   - Status `COMPLETED` or `FAILED`

3. Delta updates: Only update sections whose checksum changed

4. Stop ingestion: POST `/documentation/ingestion/stop` → cancel Celery task → status `STOPPED`

---

## Phase 3 — Embeddings and Vector Indexing

### 3.1 Goal

Implement production embedding generation and PGVector indexing so semantic search can run on real vectors instead of stubs.

### 3.2 Scope

- Provider-included embedding model string from `.env` (e.g. `bedrock:amazon.titan-embed-text-v2:0`)
- Embedder initialized from config string using Pydantic AI `Embedder(...)`
- Batched embedding generation for changed/new sections only
- Retry/backoff and failure classification for provider errors
- Vector upsert into `documentation_section.embedding`
- Re-embedding strategy on model change (full rebuild trigger)
- Job progress updates for `EMBEDDING` and `INDEXING` stages

### 3.3 Pipeline

1. Read sections changed by checksum in current ingestion run.
2. Chunk changed sections into `EMBEDDING_BATCH_SIZE`.
3. Call provider and capture vectors.
4. Persist vectors to `documentation_section.embedding`.
5. Mark `EMBEDDING` and then `INDEXING` status with progress updates.
6. On transient provider failure, retry up to `EMBEDDING_MAX_RETRIES`.
7. On terminal failure, set job `FAILED` with error details.

### 3.4 Validation

- Similar sections produce closer distances than unrelated sections.
- Re-ingestion without content changes does not regenerate embeddings.
- Model-change workflow can force re-embedding of existing sections.

---

## Phase 4 — API Endpoints

### 4.1 Ingestion Endpoints

```http
POST /documentation/ingestion
GET /documentation/ingestion/:id
POST /documentation/ingestion/stop
```

### 4.2 MCP Tool Endpoints

```http
GET /documentation           -- list_documentations
GET /documentation/:id       -- list_documentation_sections (supports start_path, pagination)
DELETE /documentation/:id
GET /documentation/:id/:section_path  -- get_section_content
GET /documentation/:id/tree  -- full nested tree
GET /documentation/:id/search  -- semantic search by embedding
```

---

## Phase 5 — Dashboard Features

- Listing of ingestions with status & last_synced
- Adjustable frequency (`cron_schedule`)
- Start / Stop ingestion
- Tree view of sections
- Minimal monospace retro/gamified style
- Manual trigger for re-ingestion

---

## Phase 6 — Security & Reliability

- `MCP_SERVER_TOKEN` header for all MCP endpoints
- Rate-limit ingestion (3 jobs at a time- configurable)
- Logging & error tracking in Celery
- Retry on failed tasks

---

## Phase 7 — Dockerization

### Backend Dockerfile

```dockerfile
FROM python:3.13-slim
WORKDIR /app

RUN pip install uv
COPY uv.toml ./
RUN uv install
COPY ./app ./app
EXPOSE 8000
CMD ["uv", "run", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Dockerfile

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY ./src ./src
RUN npm run build
RUN npm install -g serve
EXPOSE 3000
CMD ["serve", "-s", "build", "-l", "3000"]
```

### Docker Compose

```yaml
version: "3.9"

services:
  backend:
    build: ./backend
    env_file: .env
    ports:
      - "8000:8000"
    depends_on:
      - redis
      - db
    volumes:
      - ./backend/app:/app/app
    command: uv run app.main:app --host 0.0.0.0 --port 8000

  celery_worker:
    build: ./backend
    env_file: .env
    depends_on:
      - redis
      - db
    command: celery -A app.tasks worker --loglevel=info

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  frontend:
    build: ./frontend
    env_file: .env
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  pgdata:
```

---

## Phase 8 — Acceptance Criteria

1. Ingest **FastAPI docs**
2. Verify:
   - Tree structure matches navigation
   - Sections accessible via MCP tools
   - Semantic search queries return correct sections
   - Embeddings exist for indexed sections and search is vector-backed

3. Re-ingestion updates only changed sections
4. Unchanged sections skip embedding regeneration
5. Stop ingestion works mid-job

---

## Phase 9 — Step-by-Step Implementation

1. Setup Docker + uv + env
2. Implement database schema & migrations
3. Implement ingestion endpoints & Celery tasks (crawl + parse + checksum delta)
4. Implement embeddings + vector indexing stage
5. Implement MCP tool endpoints: tree, search, get section
6. Build frontend dashboard
7. Add security & logging
8. Manual testing on FastAPI docs
9. Optimize delta updates + embedding throughput
