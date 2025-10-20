# DevInsight Architecture

## System Overview

DevInsight is an AI-powered GitHub analytics platform that helps teams understand productivity, blockers, and development patterns through natural language queries.

## Architecture Diagram

```
┌─────────────────┐
│  GitHub API     │
│  (Public Repos) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Fivetran SDK    │ ◄── Incremental data sync
│   Connector     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   BigQuery      │ ◄── Structured storage
│  (Data Lake)    │     Issues, Commits, PRs
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Elasticsearch   │ ◄── Hybrid search index
│  (Search Index) │     Keyword + Vector
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│      RAG Pipeline           │
│  ┌─────────────────────┐    │
│  │ 1. Retrieve Context │    │
│  │    (Elasticsearch)  │    │
│  └──────────┬──────────┘    │
│             ▼               │
│  ┌─────────────────────┐    │
│  │ 2. Generate Answer  │    │
│  │   (Vertex AI        │    │
│  │    Gemini Pro)      │    │
│  └─────────────────────┘    │
└──────────────┬──────────────┘
               │
               ▼
┌──────────────────────────┐
│    FastAPI Backend       │
│  (REST API Endpoints)    │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│   React + Vite Frontend  │
│   (Chat Interface)       │
└──────────────────────────┘
```

## Data Flow

### 1. **Data Ingestion**
- Fivetran connector pulls GitHub data (issues, commits, PRs)
- Incremental sync using `since` parameter
- Raw data stored in BigQuery tables

### 2. **Indexing**
- BigQuery data indexed into Elasticsearch
- Text fields analyzed for keyword search
- Optional: Vector embeddings for semantic search

### 3. **Query Processing**
- User asks natural language question via UI
- Backend receives query, sanitizes input
- Elasticsearch retrieves relevant context (top 5-10 docs)
- Context passed to Vertex AI Gemini Pro

### 4. **Answer Generation**
- Gemini Pro generates answer based on context
- Response includes answer, confidence, and sources
- Frontend displays result in chat interface

## Technology Stack

### Backend
- **Python 3.11**: Core language
- **FastAPI**: REST API framework
- **Google Cloud BigQuery**: Data warehouse
- **Elasticsearch**: Search and retrieval
- **Vertex AI Gemini Pro**: AI generation
- **Fivetran SDK**: Data connector

### Frontend
- **React 18**: UI framework
- **Vite**: Build tool
- **Tailwind CSS**: Styling
- **Axios**: HTTP client
- **Recharts**: Data visualization

### Infrastructure
- **GCP**: Cloud platform (BigQuery, Vertex AI)
- **Vercel**: Frontend deployment
- **Docker**: Containerization

## Key Design Decisions

### Why Elasticsearch?
- Hybrid search (keyword + semantic)
- Fast retrieval for RAG pipeline
- Flexible indexing and query DSL

### Why Gemini Pro?
- Native GCP integration
- Strong reasoning capabilities
- Cost-effective for hackathon scale

### Why BigQuery?
- Structured data storage
- SQL interface for analytics
- Scalable to large datasets

### Why FastAPI?
- Modern Python framework
- Auto-generated API docs
- Fast and async-ready

## Scalability Considerations

### Current (MVP)
- Single repository
- Local/trial Elasticsearch
- Manual sync triggers

### Future (Production)
- Multi-repository support
- Elasticsearch cluster
- Automated sync schedules
- Rate limiting and caching
- User authentication

## Security

- Environment variables for secrets
- Service account with minimal permissions
- No private repo access (public data only)
- Input sanitization for queries

## Monitoring

- Logging at INFO level
- API call metrics
- Error tracking
- Query performance monitoring
