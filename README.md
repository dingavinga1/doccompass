# DocCompass 🚀

DocCompass is a powerful, modular platform designed to **ingest, index, and serve** documentation for multiple frameworks. It leverages the **Model Context Protocol (MCP)** to provide intelligent, structured knowledge access for developers, teams, and AI agents.

Think of it as your "Personal Documentation Concierge"—automatically crawling complex documentation sites, parsing them into high-quality semantic sections, and making them instantly searchable via vector embeddings.

---

## 🌟 Key Features

- **Adaptive Documentation Ingestion**: Automatically crawls and ingest documentation from any provided base URL with configurable depth using [Crawl4AI](https://crawl4ai.com/).
- **Intelligent Hierarchical Parsing**: Breaks down documentation into logical sections while maintaining parent-child relationships, ensuring context is preserved.
- **Semantic & Keyword Search**: Optimized search using PGVector for semantic retrieval with keyword fallback.
- **Delta Sync & Deduplication**: Smart ingestion that only updates changed sections, minimizing overhead and embedding costs.
- **Robust MCP Integration**: Full compatibility with the Model Context Protocol, allowing IDEs like VS Code and Cursor to "read" documentation through your local gateway.
- **Operator Dashboard**: A sleek, monospace UI to track ingestion jobs, browse indexed documentation, and manage resources.

---

## 🏗️ Architecture & Technology Stack

The gateway is built with a modern, high-performance stack:

- **Backend**: [FastAPI](https://fastapi.tiangolo.com/) with [FastMCP](https://github.com/jlowin/fastmcp) for the core service.
- **Database**: [PostgreSQL](https://www.postgresql.org/) with [PGVector](https://github.com/pgvector/pgvector) for vector storage.
- **Task Queue**: [Celery](https://docs.celeryq.dev/) + [Redis](https://redis.io/) for robust asynchronous ingestion pipelines.
- **ORM**: [SQLModel](https://sqlmodel.tiangolo.com/) for type-safe database interactions.
- **Ingestion**: [Crawl4AI](https://crawl4ai.com/) for high-fidelity web scraping.
- **Package Manager**: [uv](https://github.com/astral-sh/uv) for blazing-fast Python dependency management.

### Data Flow
`User triggers url` -> `Crawl4AI fetches pages` -> `Hierarchical Parser chunks content` -> `Provider (Bedrock/OpenAI) generates embeddings` -> `PGVector stores indices` -> `MCP Server serves content`.

---

## 🚦 Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) + [Docker Compose](https://docs.docker.com/compose/)
- `uv` (optional, for local development)

### Quick Start (Docker Compose)

1. **Clone the repository**
2. **Setup Environment Variables**:
   ```bash
   cp .env.example .env
   ```
   *Edit `.env` to configure your embedding provider (AWS Bedrock or OpenAI).*
3. **Start the Stack**:
   ```bash
   docker compose up --build -d
   ```
   *This will start the Database, Redis, Migrations (one-shot), Backend, Celery Worker, and Frontend.*

### Verify Services

| Service | URL | Description |
| :--- | :--- | :--- |
| **Backend Health** | `http://localhost:8000/health` | Service status & dependency check |
| **Interactive Docs** | `http://localhost:8000/docs` | Swagger UI for API exploration |
| **MCP Endpoint** | `http://localhost:8000/mcp` | The transport URL for MCP clients |
| **Dashboard** | `http://localhost:3000` | Management UI |

---

## 🛠️ Configuration Guide (`.env`)

| Variable | Default | Description |
| :--- | :--- | :--- |
| `MCP_SERVER_TOKEN` | `super-secret-token` | Bearer token for MCP authentication |
| `EMBEDDING_MODEL` | `bedrock:...` | Model for vectorization (Bedrock or OpenAI) |
| `EMBEDDING_TOKEN_LIMIT` | `8192` | Max tokens your embedding model accepts |
| `AWS_REGION` | `us-east-1` | AWS region for Bedrock (if used) |
| `POSTGRES_CONNECTION_STRING` | `postgresql+psycopg://...` | DB connection string |

> [!TIP]
> To use **OpenAI**, uncomment `OPENAI_API_KEY` in your `.env` and update `EMBEDDING_MODEL` to a valid OpenAI model string (e.g., `openai:text-embedding-3-small`).

---

## 🔌 MCP Integration

### VS Code / AntiGravity
Add the following to your MCP settings (e.g., `~/.../mcp_settings.json` or equivalent):

```json
{
  "mcpServers": {
      "framework-documentations-mcp-server": {
        "serverUrl": "http://localhost:8000/mcp",
        "headers": {
        "Authorization": "Bearer super-secret-token"
      }
    }
  }
}
```
*Note: The exact configuration depending on your client's transport support. The gateway supports HTTP transport.*

---

## 🖥️ Local Development

If you prefer to run services outside of Docker for development:

### Backend
1. `cd backend`
2. `uv sync`
3. `uv run alembic upgrade head`
4. `uv run python -m app.main`

### Frontend
1. `cd frontend`
2. `npm install`
3. `npm start`

### Celery Worker
1. `uv run celery -A app.tasks worker --loglevel=info`

---

## 🧪 Testing

We use `pytest` for backend verification.

```bash
cd backend
uv run pytest
```

## Implementation Roadmap/Todo List
- [ ] CLI tool for DocCompass
- [ ] Cronjobs for existing documentations, for periodic fetching and syncing.
- [ ] Better user experience for the progress indicator. Currently, there's a weight assigned to each stage, which makes it difficult for the end user to predict the ETA.
- [ ] Implement a tool to allow agents to get sections by URLs for easier backtracking based on links provided within certain sections.

> For any suggestions, feel free to create Issues within the repository!
