# search_api.py
import os
import math
import traceback
from typing import Optional
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from elasticsearch import Elasticsearch
from google import genai

load_dotenv()

# ---------- Config from .env ----------
PROJECT = os.getenv("PROJECT_ID", "hackathon-github-ai")
LOCATION = os.getenv("LOCATION", "us-central1")
VERTEX_MODEL = os.getenv("VERTEX_MODEL", "gemini-embedding-001")
ES_CLOUD_ID = os.getenv("YOUR_CLOUD_ID")
ES_USERNAME = os.getenv("YOUR_USERNAME", "elastic")
ES_PASSWORD = os.getenv("YOUR_PASSWORD")
ES_INDEX = os.getenv("ELASTIC_INDEX", "github_issues")

if not ES_CLOUD_ID or not ES_PASSWORD:
    raise RuntimeError("Set ELASTIC_CLOUD_ID and ELASTIC_PASSWORD in .env")

# ---------- Initialize Elasticsearch ----------
es = Elasticsearch(cloud_id=ES_CLOUD_ID, basic_auth=(ES_USERNAME, ES_PASSWORD))

# ---------- Initialize GenAI (Vertex) ----------
# Ensure GOOGLE_APPLICATION_CREDENTIALS env var points to service account JSON
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
client = genai.Client(vertexai=True, project=PROJECT, location=LOCATION)

# ---------- FastAPI app ----------
app = FastAPI(title="DevInsight Semantic Search API")

# Allow React dev server (adjust the origins for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Vite defaults
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Request / Response models ----------
class SearchRequest(BaseModel):
    q: str
    top_k: Optional[int] = 5
    # optional filter dates (ISO format), empty means no filter
    created_after: Optional[str] = None
    created_before: Optional[str] = None
    closed_after: Optional[str] = None
    closed_before: Optional[str] = None

# Helper: truncate text for preview/snippet
def snippet(text: str, length: int = 400):
    if not text:
        return ""
    return (text[:length] + "...") if len(text) > length else text

# ---------- Utility: generate query embedding ----------
def make_query_embedding(query_text: str):
    # Use genai Client to call Vertex embeddings
    response = client.models.embed_content(
        model=VERTEX_MODEL,
        contents=query_text
    )
    # response.embeddings[0].values -> list of floats
    return response.embeddings[0].values

# ---------- API route ----------
@app.post("/search")
def search(req: SearchRequest):
    """
    Hybrid semantic + keyword search endpoint.
    Returns top_k results with: title, snippet(body), repo_name, created_at, closed_at, score.
    """
    if not req.q or not req.q.strip():
        raise HTTPException(status_code=400, detail="Query 'q' is required")

    try:
        # 1) get embedding for the user query
        query_vec = make_query_embedding(req.q)

        # 2) build ES query: script_score wrapping a bool that matches keywords
        #    We boost title matches over body to favor direct matches
        must_filters = []
        # optional date filters (simple range filters)
        if req.created_after or req.created_before:
            range_obj = {}
            if req.created_after:
                range_obj["gte"] = req.created_after
            if req.created_before:
                range_obj["lte"] = req.created_before
            must_filters.append({"range": {"created_at": range_obj}})
        if req.closed_after or req.closed_before:
            range_obj = {}
            if req.closed_after:
                range_obj["gte"] = req.closed_after
            if req.closed_before:
                range_obj["lte"] = req.closed_before
            must_filters.append({"range": {"closed_at": range_obj}})

        # Construct core query
        es_query = {
            "size": req.top_k,
            "query": {
                "script_score": {
                    "query": {
                        "bool": {
                            "must": must_filters,
                            "should": [
                                {"match": {"title": {"query": req.q, "boost": 3}}},
                                {"match": {"body": {"query": req.q, "boost": 1}}},
                            ],
                            # require at least one should to influence score but not mandatory
                            "minimum_should_match": 0
                        }
                    },
                    "script": {
                        # cosineSimilarity returns [-1,1]; add 1.0 to make positive scores
                        "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                        "params": {"query_vector": query_vec}
                    }
                }
            },
            "_source": ["title", "body", "repo_name", "created_at", "closed_at", "state"]
        }

        # 3) execute search
        resp = es.search(index=ES_INDEX, body=es_query)

        results = []
        for hit in resp["hits"]["hits"]:
            src = hit["_source"]
            results.append({
                "id": hit.get("_id"),
                "title": src.get("title"),
                "repo_name": src.get("repo_name"),
                "created_at": src.get("created_at"),
                "closed_at": src.get("closed_at"),
                "state": src.get("state"),
                "score": hit.get("_score"),
                "body_snippet": snippet(src.get("body", ""), 450)
            })

        return {"query": req.q, "top_k": req.top_k, "results": results}

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")
