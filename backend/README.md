# DevInsight Backend

## Overview
FastAPI-based backend for AI-powered GitHub analytics. Integrates with Fivetran, BigQuery, Elasticsearch, and Vertex AI Gemini.

## Setup

### Prerequisites
- Python 3.9+
- Google Cloud Platform account with:
  - BigQuery API enabled
  - Vertex AI API enabled
  - Service account with appropriate permissions
- Elasticsearch instance (local or cloud)

### Installation

1. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   - Copy `.env` and update with your credentials
   - Add service account JSON to `config/service_account.json`

4. **Initialize BigQuery tables:**
   ```bash
   python -m src.bigquery_loader
   ```

5. **Set up Elasticsearch indices:**
   ```bash
   python -m src.elasticsearch_indexer
   ```

## Running

### Development Server
```bash
python -m src.main
```

API will be available at `http://localhost:8000`

### API Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing

```bash
# Test Fivetran connector
python -m src.fivetran_connector

# Test AI agent
python -m src.ai_agent
```

## Project Structure
```
backend/
├── src/
│   ├── main.py                  # FastAPI app
│   ├── fivetran_connector.py    # GitHub data sync
│   ├── bigquery_loader.py       # BigQuery operations
│   ├── elasticsearch_indexer.py # Search indexing
│   ├── ai_agent.py              # RAG system with Gemini
│   └── utils.py                 # Helper functions
├── config/
│   ├── service_account.json     # GCP credentials
│   └── config.yaml              # App configuration
├── tests/
├── requirements.txt
└── .env
```

## API Endpoints

- `GET /` - Health check
- `GET /health` - Detailed health status
- `POST /query` - AI-powered analytics query
- `POST /sync` - Trigger GitHub data sync

## Environment Variables

See `.env` for required configuration.
