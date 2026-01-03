# Cortex - Enterprise Intelligence Platform

## Project Overview

Cortex is a unified enterprise intelligence platform that combines:

1. **BI Platform** - Traditional Business Intelligence with dashboards, self-service analytics, and report generation
2. **AI Platform** - Smart services including document routing, RAG-powered chat, summarization, and data quality assessment

The platform delivers comprehensive data and intelligence capabilities for modern enterprises.

## Tech Stack

### Backend
- **Framework**: FastAPI with async support
- **AI/ML**: LangChain, LangGraph, Sentence Transformers, ChromaDB
- **Database**: PostgreSQL (metadata), MinIO (data lake), Redis (caching/jobs)
- **Package Manager**: UV

### Frontend
- **Framework**: React 18 with Vite
- **Styling**: Tailwind CSS
- **Routing**: React Router v6

## Project Structure

```
src/cortex/
├── main.py                    # FastAPI application entry
├── startup.py                 # Context seeding on startup
├── agents/
│   └── smart_router/          # LangGraph document classification agent
│       ├── graph.py           # Main agent graph
│       ├── config.py          # 100 routing categories
│       ├── state.py           # Agent state management
│       └── nodes/             # Graph nodes (classify, extract, route)
├── database/
│   ├── connection.py          # PostgreSQL connection
│   └── models.py              # SQLAlchemy models
├── services/
│   ├── minio/                 # Data lake (Bronze/Silver/Gold layers)
│   ├── document_service.py    # Document processing
│   ├── qa_service.py          # RAG Q&A service
│   ├── summarization_service.py
│   ├── comparison_service.py
│   ├── report_service.py
│   └── data_quality_service.py
├── routers/                   # FastAPI routers
│   ├── upload.py              # File upload with smart routing
│   ├── chat.py                # RAG chat endpoints
│   ├── documents.py           # Document management
│   ├── health.py              # Health checks
│   ├── summarization.py       # Document summarization
│   ├── comparison.py          # Document comparison
│   ├── reports.py             # Report generation
│   └── data_quality.py        # Data quality assessment
├── jobs/                      # Background job processing
└── models/                    # Pydantic request/response models

frontend/
├── src/
│   ├── components/            # React components
│   ├── pages/                 # Page components
│   └── hooks/                 # Custom hooks
└── ...config files
```

## Development Commands

### Backend

```bash
# Install dependencies
uv sync

# Run development server
uv run uvicorn cortex.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
uv run pytest src/cortex/ -v

# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Type checking
uv run mypy src/
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build
```

### Docker

```bash
# Start all services
docker compose up -d

# Start with Neo4j (optional)
docker compose --profile full up -d

# View logs
docker compose logs -f backend

# Stop services
docker compose down
```

## API Endpoints

### Core
- `POST /api/upload` - Upload and process documents
- `POST /api/chat` - RAG-powered chat
- `GET /api/documents` - List documents
- `GET /health` - Health check

### Phase 2 Services
- `POST /api/summarize` - Document summarization
- `POST /api/compare` - Document comparison
- `POST /api/reports/generate` - Report generation
- `POST /api/quality/assess` - Data quality assessment

## Architecture Patterns

### Medallion Architecture (Data Lake)
- **Bronze**: Raw uploaded files
- **Silver**: Processed/extracted content with metadata
- **Gold**: Enriched, analysis-ready data

### Smart Router Agent
- Embedding-based pre-filtering
- LLM ensemble classification (100 categories)
- Confidence scoring with fallback routing

### Service Pattern
- `pydantic-settings` for configuration with `@lru_cache()`
- Singleton services via `get_*_service()` functions
- Async methods for I/O operations

## Code Standards

- **Line length**: 100 characters max
- **Type hints**: Required for all function signatures
- **Docstrings**: Google-style for public functions
- **Imports**: Absolute imports from `cortex.*`
- **Models**: Pydantic v2 with strict validation

## Environment Variables

See `.env.example` for all configuration options:

```bash
# LLM
OLLAMA_URL=http://localhost:11434
OLLAMA_DEFAULT_MODEL=qwen2.5:14b

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=cortex_db

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123

# Redis
REDIS_URL=redis://localhost:6379/0
```

## Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/cortex --cov-report=html

# Run specific test file
uv run pytest src/cortex/services/tests/test_qa_service.py -v
```
