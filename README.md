# Wafaa AI Concierge

Multi-tenant AI chatbot platform with RAG-powered responses for WhatsApp, Instagram, TikTok, and Snapchat.

## Features

- **Multi-tenant Architecture**: Row-level security with complete tenant isolation
- **RAG-Powered Responses**: Context-aware AI responses using vector search
- **Multi-Channel Support**: WhatsApp, Instagram, TikTok, Snapchat integrations
- **Knowledge Base Management**: Upload and index PDF, DOCX, TXT documents
- **Conversation Management**: Session handling with Redis caching
- **Enterprise Security**: JWT authentication, webhook signature verification

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy 2.0
- **Database**: PostgreSQL 15+ with async support
- **Cache**: Redis 7+
- **Vector DB**: Pinecone or Weaviate
- **AI**: OpenAI GPT-4o, Claude 3.5, Llama 3

## Quick Start

### 1. Prerequisites

- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+

### 2. Setup

```bash
# Clone and enter project
cd Wafaa-Project

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r backend/requirements.txt

# Copy environment template
copy backend\.env.example backend\.env
# Edit .env with your credentials

# Start databases (Docker)
docker-compose up -d postgres redis

# Run migrations
cd backend
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --port 8000
```

### 3. Setup Vector Database

```bash
# Pinecone (cloud)
python scripts/setup_vector_db.py --provider pinecone

# OR Weaviate (local)
docker-compose up -d weaviate
python scripts/setup_vector_db.py --provider weaviate
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/register` - Register
- `GET /api/v1/auth/me` - Current user

### Clients (Tenants)
- `POST /api/v1/clients` - Create client
- `GET /api/v1/clients` - List clients
- `GET /api/v1/clients/{id}` - Get client
- `PUT /api/v1/clients/{id}` - Update client

### Knowledge Base
- `POST /api/v1/clients/{id}/knowledge/upload` - Upload document
- `GET /api/v1/clients/{id}/knowledge/documents` - List documents
- `DELETE /api/v1/clients/{id}/knowledge/documents/{doc_id}` - Delete

### Chat
- `POST /api/v1/clients/{id}/chat` - Send message
- `GET /api/v1/clients/{id}/chat/conversations` - List conversations

### Webhooks
- `GET/POST /api/v1/webhook/whatsapp/{slug}` - WhatsApp webhook
- `GET/POST /api/v1/webhook/instagram/{slug}` - Instagram webhook

## Project Structure

```
backend/
├── app/
│   ├── api/v1/endpoints/   # API routes
│   ├── core/               # Config, database, security
│   ├── models/             # SQLAlchemy models
│   ├── schemas/            # Pydantic schemas
│   └── services/
│       ├── ai/             # LLM, RAG, embeddings
│       ├── channels/       # WhatsApp, Instagram
│       ├── knowledge/      # Indexing, retrieval
│       └── orchestrator/   # Chat coordination
├── migrations/             # Alembic migrations
├── tests/                  # pytest tests
└── main.py                 # FastAPI app
```

## Environment Variables

See `backend/.env.example` for all required variables:

- `DATABASE_URL` - PostgreSQL connection
- `REDIS_URL` - Redis connection
- `OPENAI_API_KEY` - OpenAI API key
- `PINECONE_API_KEY` - Pinecone API key
- `META_APP_ID` / `META_APP_SECRET` - Meta (WhatsApp/Instagram)

## Testing

```bash
cd backend

# Run all tests
pytest -v

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific tests
pytest tests/unit -v
pytest tests/integration -v
```

## Docker

```bash
# Build and run all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop all services
docker-compose down
```

## License

MIT
