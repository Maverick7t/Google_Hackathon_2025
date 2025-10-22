"""
FastAPI backend for DevInsight - GitHub Analytics with LangChain RAG
"""
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from google.cloud import bigquery

from .langchain_query import query_github_analytics
from .credentials_helper import get_google_credentials_path

load_dotenv()

# ==================== BigQuery Client ====================
SERVICE_ACCOUNT_PATH = get_google_credentials_path()
bq_client = bigquery.Client.from_service_account_json(SERVICE_ACCOUNT_PATH)

PROJECT_ID = os.getenv("GCP_PROJECT_ID", "hackathon-github-ai")
DATASET_ID = "github_analytics"
TABLE_ID = f"{PROJECT_ID}.{DATASET_ID}.github_issues"

# ==================== Initialize FastAPI ====================

app = FastAPI(
    title="DevInsight API",
    description="GitHub Analytics powered by LangChain + Elasticsearch + Vertex AI",
    version="1.0"
)

# ==================== CORS Configuration ====================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== Request/Response Models ====================

class QueryRequest(BaseModel):
    question: str = None
    query: str = None
    max_sources: int = 10


class SourceDocument(BaseModel):
    title: str
    repo: str
    contributor: str
    commit_count: int
    created_at: str
    state: str


class QueryResponse(BaseModel):
    answer: str
    sources: list = []
    num_sources: int = 0


# ==================== Root Endpoint ====================

@app.get("/")
def root():
    """API info"""
    return {
        "name": "DevInsight API",
        "version": "1.0",
        "status": "running"
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "DevInsight API"}


# ==================== Chat/Query Endpoints ====================

@app.post("/ask")
def ask_endpoint(request: QueryRequest):
    """
    Main chat endpoint used by frontend
    Accepts either 'question' or 'query' field
    """
    user_input = request.question or request.query
    
    if not user_input or len(user_input.strip()) == 0:
        raise HTTPException(status_code=400, detail="Question/query cannot be empty")
    
    try:
        result = query_github_analytics(user_input)
        return {
            "answer": result["answer"],
            "sources": result.get("sources", []),
            "num_sources": result.get("num_sources", 0)
        }
    except Exception as e:
        print(f"Error in /ask: {e}")
        return {
            "answer": f"Error processing query: {str(e)}",
            "sources": [],
            "num_sources": 0
        }


@app.post("/query")
def query_endpoint(request: QueryRequest):
    """Alias for /ask"""
    return ask_endpoint(request)


@app.post("/chat")
def chat_endpoint(request: QueryRequest):
    """Alias for /ask"""
    return ask_endpoint(request)


# ==================== Reports Endpoints ====================

@app.get("/reports")
def get_reports():
    """
    Get GitHub analytics reports
    Returns: { issues, contributors, blockers }
    """
    try:
        # Issue statistics
        stats_query = f"""
        SELECT 
            COUNT(CASE WHEN state = 'closed' THEN 1 END) as closed,
            COUNT(CASE WHEN state = 'open' THEN 1 END) as open,
            ROUND(AVG(

                CASE 

                    WHEN closed_at IS NOT NULL 

                    THEN TIMESTAMP_DIFF(SAFE_CAST(closed_at AS TIMESTAMP), SAFE_CAST(created_at AS TIMESTAMP), HOUR) 

                END

            ), 1) AS avg_resolution_hrs
        FROM `{TABLE_ID}`
        """
        stats_result = list(bq_client.query(stats_query).result())
        stats = stats_result[0] if stats_result else None
        
        # Top contributors
        contrib_query = f"""
        SELECT 
            contributor_login as name,
            MAX(commit_count) as commits
        FROM `{TABLE_ID}`
        WHERE contributor_login IS NOT NULL AND contributor_login != ''
        GROUP BY contributor_login
        ORDER BY commits DESC
        LIMIT 5
        """
        contrib_results = [dict(row) for row in bq_client.query(contrib_query).result()]
        
        # Blockers (open issues)
        blocker_query = f"""
        SELECT 
            title,
            repo_name,
            state,
            created_at
        FROM `{TABLE_ID}`
        WHERE state = 'open'
        ORDER BY created_at DESC
        LIMIT 5
        """
        blocker_results = [dict(row) for row in bq_client.query(blocker_query).result()]
        
        return {
            "issues": {
                "closed": int(stats.closed) if stats else 0,
                "open": int(stats.open) if stats else 0,
                "avg_resolution_hrs": float(stats.avg_resolution_hrs) if stats and stats.avg_resolution_hrs else 0
            },
            "contributors": contrib_results,
            "blockers": blocker_results
        }
    
    except Exception as e:
        print(f"Error in /reports: {e}")
        return {
            "issues": {"closed": 0, "open": 0, "avg_resolution_hrs": 0},
            "contributors": [],
            "blockers": []
        }


@app.get("/issues/recent")
def get_recent_issues(limit: int = 20):
    """
    Get the most recent issues (created_at descending).
    Returns: { recent_issues }
    """
    try:
        query = f"""
        SELECT
            issue_id,
            number,
            title,
            body,
            repo_name,
            state,
            contributor_login,
            commit_count,
            created_at,
            closed_at
        FROM `{TABLE_ID}`
        ORDER BY created_at DESC
        LIMIT {limit}
        """
        results = [dict(row) for row in bq_client.query(query).result()]

        # Format data for frontend
        formatted_results = []
        for row in results:
            formatted_results.append({
                "issue_id": row.get("issue_id"),
                "number": row.get("number"),
                "title": row.get("title"),
                "body": row.get("body"),
                "repo_name": row.get("repo_name"),
                "state": row.get("state").lower() if row.get("state") else "unknown",
                "contributor_login": row.get("contributor_login"),
                "commit_count": row.get("commit_count") or 0,
                "created_at": row.get("created_at").isoformat() if row.get("created_at") else None,
                "closed_at": row.get("closed_at").isoformat() if row.get("closed_at") else None,
            })

        return {"recent_issues": formatted_results}

    except Exception as e:
        print(f"Error in /issues/recent: {e}")
        return {"recent_issues": []}



# ==================== Run Server ====================

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("API_PORT", 8000))
    host = os.getenv("API_HOST", "0.0.0.0")
    
    print(f"\n🚀 Starting DevInsight API on {host}:{port}")
    uvicorn.run(app, host=host, port=port)