# Production LangGraph API

A production-oriented LLM chat API built with **FastAPI, LangGraph, LangChain, Groq, Google Gemini, and LangSmith**.

The project is designed around production engineering concerns rather than a simple LLM wrapper. It includes an input/output security pipeline, prompt-injection filtering, PII detection and masking, response caching, rate limiting, model fallback handling, structured logging, application metrics, health checks, Docker support, and Render deployment.

## Live API

**Production URL:**  
https://langchain-production-api-uxxc.onrender.com/

### API Documentation

FastAPI automatically exposes interactive API documentation:

- `/docs` — Swagger UI
- `/openapi.json` — OpenAPI schema

For the deployed service:

- https://langchain-production-api-uxxc.onrender.com/docs
- https://langchain-production-api-uxxc.onrender.com/openapi.json

## Key Features

### 1. Production FastAPI Service

The API is implemented with FastAPI and uses a modern application lifespan to initialize and shut down production components cleanly.

The service exposes:

- `POST /chat`
- `GET /health`
- `GET /metrics`
- `GET /cache/stats`

### 2. LangGraph Agent Architecture

The LLM execution flow is modeled as a LangGraph state machine.

The graph contains:

```text
START
  │
  ▼
Primary Model
  │
  ├── success ───────────────► END
  │
  └── failure
        │
        ▼
   Fallback Model
        │
        ├── success ─────────► END
        │
        └── failure
              │
              ▼
         Error Handler
              │
              ▼
             END
```

This separates model execution, fallback behavior, and graceful error handling into explicit graph nodes.

### 3. Multi-Model Resilience

The service uses two LLM providers:

- **Primary:** Groq
- **Fallback:** Google Gemini

The primary and fallback models are configurable through environment variables.

If the primary model fails, the LangGraph workflow can route the request to the fallback model. Model-level automatic retries are disabled so that retry/fallback behavior remains explicitly controlled by the application graph.

### 4. Security Pipeline

Every chat request passes through a dedicated security pipeline before reaching the LLM.

The input security flow includes:

1. Prompt-injection detection
2. Input sanitization
3. PII detection
4. PII masking

The output is also validated before it is returned to the client.

#### Prompt Injection Detection

The security layer checks for common instruction-manipulation patterns such as attempts to:

- Ignore previous instructions
- Replace system instructions
- Reveal system prompts
- Bypass restrictions
- Impersonate or force a new assistant identity

Suspicious inputs are rejected before model invocation.

#### PII Protection

The application detects and masks several PII categories:

- Email addresses
- Phone numbers
- SSN-like values
- Credit-card-like values

PII masking is performed on input before the text reaches the LLM and is also applied to model output before the response is returned.

#### Output Validation

The output security layer checks for:

- PII leakage
- Selected harmful patterns
- Password/API-key style leakage patterns

Detected PII is masked and selected unsafe output patterns are blocked.

### 5. Rate Limiting

The API uses **SlowAPI** for request rate limiting.

The default application limit is:

```text
20 requests/minute
```

The limit is configurable with:

```env
RATE_LIMIT=20/minute
```

Requests exceeding the configured limit receive HTTP `429 Too Many Requests`.

### 6. Response Caching

A lightweight in-memory response cache is implemented with TTL support.

Cache characteristics:

- SHA-256 cache keys
- Case/whitespace normalization
- Configurable TTL
- Cache hit/miss counters
- Hit-rate calculation

Default TTL:

```text
300 seconds
```

Configuration:

```env
CACHE_TTL_SECONDS=300
```

The cache is intentionally simple and application-local. For a multi-instance production deployment, the implementation can be replaced with Redis so that cached responses are shared between instances and survive application restarts.

### 7. Observability

The application includes structured JSON logging and application-level metrics.

Logged information includes:

- Timestamp
- Log level
- Module
- Function
- Request latency
- Request status/error information
- Thread ID
- Model used
- Security events

The application also tracks:

- Total requests
- Total errors
- Error rate
- Average latency
- Estimated input tokens
- Estimated output tokens
- Cache hits
- Cache misses
- Cache hit rate

### 8. LangSmith Tracing

LangSmith tracing is integrated into the security and agent execution paths.

The project uses traceable operations for:

- Chat endpoint execution
- Security input checks
- Security output checks
- Production agent invocation

Configure LangSmith with:

```env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_PROJECT=production-api
```

This allows LLM/application execution to be inspected through LangSmith when tracing is enabled.

---

## API Endpoints

### `POST /chat`

Main conversational endpoint.

#### Request

```json
{
  "message": "What is LangGraph?",
  "thread_id": "demo-thread"
}
```

#### Response

```json
{
  "response": "LangGraph is ...",
  "thread_id": "demo-thread",
  "model_used": "primary",
  "cached": false,
  "processing_time_ms": 1234.56,
  "timestamp": "2026-09-14T00:00:00Z"
}
```

The `message` field is validated with:

- Minimum length: `1`
- Maximum length: `10000`

`thread_id` defaults to:

```text
default
```

### `GET /health`

Health endpoint used to verify that the application's core components have been initialized.

Example:

```json
{
  "status": "healthy",
  "environment": "production",
  "version": "1.0.0",
  "checks": {
    "agent": true,
    "security": true,
    "cache": true
  }
}
```

### `GET /metrics`

Returns application-level runtime metrics such as request count, error rate, average latency, token estimates, and cache performance.

### `GET /cache/stats`

Returns cache-specific statistics including:

- Hits
- Misses
- Hit rate
- Cached entries

---

## Request Processing Pipeline

A typical `/chat` request follows this sequence:

```text
Client
  │
  ▼
FastAPI /chat
  │
  ▼
Rate Limiter
  │
  ▼
Input Security Pipeline
  ├── Prompt Injection Check
  ├── Input Sanitization
  └── PII Masking
  │
  ▼
Response Cache
  │
  ├── Cache Hit ─────────────► Return Cached Response
  │
  └── Cache Miss
          │
          ▼
      LangGraph Agent
          │
          ▼
      Primary LLM
          │
          ├── Success
          │
          └── Failure
                │
                ▼
           Fallback LLM
          │
          ▼
      Output Validation
          ├── PII Masking
          └── Output Safety Checks
          │
          ▼
      Cache Response
          │
          ▼
      Metrics + Structured Logs
          │
          ▼
        Client
```

---

## Project Structure

```text
production_level_project/
│
├── app/
│   ├── __init__.py
│   ├── agent.py
│   ├── cache.py
│   ├── config.py
│   ├── main.py
│   ├── models.py
│   ├── monitoring.py
│   └── security.py
│
├── tests/
│   ├── __init__.py
│   ├── test_api.py
│   ├── test_cache.py
│   └── test_security.py
│
├── src/
│   └── production_level_project/
│       └── __init__.py
│
├── Dockerfile
├── docker-compose.yml
├── render.yml
├── pyproject.toml
├── requirements.txt
├── uv.lock
├── .gitignore
└── README.md
```

### Core modules

| File | Responsibility |
|---|---|
| `app/main.py` | FastAPI application, endpoints, rate limiting, request orchestration |
| `app/agent.py` | LangGraph state machine and multi-model execution |
| `app/security.py` | Prompt-injection checks, sanitization, PII masking, output validation |
| `app/cache.py` | In-memory response cache and TTL management |
| `app/config.py` | Environment-based application configuration |
| `app/models.py` | Pydantic request/response schemas |
| `app/monitoring.py` | Structured logging, metrics, and request timing |
| `tests/test_security.py` | Security-layer tests |
| `Dockerfile` | Containerized production runtime |
| `render.yml` | Render deployment configuration |

---

## Technology Stack

### Backend

- Python 3.12
- FastAPI
- Uvicorn
- Pydantic / Pydantic Settings

### LLM / Agent Layer

- LangChain
- LangGraph
- Groq
- Google Gemini
- LangSmith

### Reliability & Security

- SlowAPI
- Custom prompt-injection detection
- PII detection and masking
- Output validation
- Model fallback handling
- TTL response caching

### Deployment

- Docker
- Docker Compose
- Render

### Dependency Management

- `uv`
- `uv.lock`

---

## Environment Variables

Create a local `.env` file for development.

Example:

```env
# LLM providers
GROQ_API_KEY=your_groq_api_key
GOOGLE_API_KEY=your_google_api_key

# Models
PRIMARY_MODEL=openai/gpt-oss-120b
FALLBACK_MODEL=gemini-3.8-flash

# LangSmith
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key
LANGCHAIN_PROJECT=production-api

# Application
APP_ENV=development
LOG_LEVEL=INFO

# Reliability
RATE_LIMIT=20/minute
CACHE_TTL_SECONDS=300
MAX_RETRIES=3
```

**Never commit real API keys or secrets to Git.**

---

## Local Development

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd production_level_project
```

### 2. Create and activate a virtual environment

Using Python:

```bash
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source .venv/bin/activate
```

### 3. Install dependencies

Using `uv`:

```bash
uv sync
```

### 4. Configure environment variables

Create `.env` and provide the required API keys.

### 5. Start the API

```bash
uv run uvicorn app.main:app --reload
```

The API will be available at:

```text
http://localhost:8000
```

Swagger UI:

```text
http://localhost:8000/docs
```

---

## Docker

The project includes a production-oriented Dockerfile.

### Build

```bash
docker compose build
```

### Run

```bash
docker compose up -d
```

### Check logs

```bash
docker compose logs -f
```

### Stop

```bash
docker compose down
```

The container exposes port `8000`.

The Docker image:

- Uses Python 3.12 slim
- Installs dependencies with `uv`
- Uses the lockfile for reproducible dependency installation
- Runs as a non-root `appuser`
- Includes a container health check
- Starts FastAPI with Uvicorn

---

## Testing

The project includes tests for the security layer.

Run:

```bash
uv run pytest
```

The security tests cover areas such as:

- Safe input handling
- Prompt-injection detection
- Input sanitization
- Email detection
- Phone detection
- SSN-like value detection
- Credit-card-like value detection
- PII masking
- Output PII validation

The security tests are designed to run without making LLM calls, keeping them fast and deterministic.

---

## Deployment

The API is deployed as a web service on **Render**.

Production configuration includes:

- Python runtime
- Singapore region
- Free plan
- Production environment variables
- Health check at `/health`
- Automatic deployment from the configured repository

### Production startup

The service runs FastAPI through Uvicorn:

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

The production application should receive secrets through Render environment variables rather than committing them to the repository.

---

## Production Design Decisions

### Explicit retry/fallback control

Instead of relying entirely on provider-level retries, model clients are configured with zero automatic retries and the application controls failure handling through LangGraph.

This makes the execution path easier to reason about and allows a primary-model failure to transition to the fallback model.

### Security before LLM invocation

Input validation and PII masking happen before the message is passed to the model.

This creates a security boundary between untrusted client input and the LLM.

### Output validation

The model response is not returned directly to the client. It passes through output validation first.

### Cache before model invocation

The cache is checked before invoking an LLM. This can reduce repeated model calls for identical normalized queries and reduce unnecessary latency and provider usage.

### Health endpoint

The `/health` endpoint checks whether the application's main runtime components have been initialized:

```text
agent
security
cache
```

This provides a simple readiness signal for container and hosting environments.

---

## Security Considerations

This project implements application-level security controls, but these should not be treated as a complete security solution for every production workload.

Current protections include:

- Prompt-injection pattern detection
- Input sanitization
- PII masking
- Output PII masking
- Selected harmful-output filtering
- API rate limiting
- Secret configuration through environment variables

For a larger production deployment, additional controls can be added, such as:

- Authentication and authorization
- API keys or OAuth/JWT
- Persistent distributed rate limiting
- Redis-backed caching
- External secrets management
- Centralized metrics with Prometheus/OpenTelemetry
- WAF/API gateway protection
- More comprehensive content-safety policies
- Database-backed conversation persistence

---

## Scaling Considerations

The current cache and metrics implementations are **in-memory**.

That means each running process/instance maintains its own state.

For horizontal scaling, the natural next step is:

```text
Current
FastAPI
 ├── In-memory cache
 └── In-memory metrics

Scalable
FastAPI instances
 ├── Redis
 │    ├── Shared cache
 │    └── Distributed rate limiting
 │
 └── Prometheus/OpenTelemetry
      └── Centralized metrics
```

This project therefore provides a strong production-oriented application foundation while keeping the infrastructure lightweight enough for deployment on a free hosting platform.

---

## API Example

Using `curl`:

```bash
curl -X POST "https://langchain-production-api-uxxc.onrender.com/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explain what LangGraph is",
    "thread_id": "demo-thread"
  }'
```

Health check:

```bash
curl "https://langchain-production-api-uxxc.onrender.com/health"
```

Metrics:

```bash
curl "https://langchain-production-api-uxxc.onrender.com/metrics"
```

Cache statistics:

```bash
curl "https://langchain-production-api-uxxc.onrender.com/cache/stats"
```

---

## Future Improvements

Potential next-stage enhancements include:

- Persistent conversation/thread memory
- Redis-backed distributed cache
- Distributed rate limiting
- Authentication and authorization
- Vector database integration for retrieval
- Hybrid search and reranking
- Document ingestion pipelines
- Streaming responses
- Prometheus/OpenTelemetry observability
- Automated CI/CD
- More comprehensive integration and load testing
- Provider health checks and smarter model routing

---

## Author

**Tayyab Siddique**

Built as a production-oriented LLM API project demonstrating practical AI engineering, agent orchestration, security, reliability, observability, caching, containerization, and cloud deployment.

---


