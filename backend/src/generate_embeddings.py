"""
Simple embedding generation using Vertex AI SDK.
Fetches issues + contributor info from BigQuery and indexes into Elasticsearch.
"""
import os
from dotenv import load_dotenv
import pandas as pd
from google.cloud import bigquery
from elasticsearch import Elasticsearch, helpers
import vertexai
from vertexai.language_models import TextEmbeddingModel
import time

load_dotenv()
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

PROJECT_ID = os.getenv("GCP_PROJECT_ID", "hackathon-github-ai")
DATASET_ID = "github_analytics"
INDEX_NAME = os.getenv("ELASTIC_INDEX", "github_issues")
LOCATION = "us-central1"

print("=" * 60)
print("Regenerating embeddings with Vertex AI SDK")
print("=" * 60)

# Initialize Vertex AI
vertexai.init(project=PROJECT_ID, location=LOCATION)

# Fetch data from BigQuery
print("\nFetching documents from BigQuery...")
bq_client = bigquery.Client(project=PROJECT_ID)
query = f"SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.github_issues` LIMIT 5000"
df = bq_client.query(query).to_dataframe()
print(f"Fetched {len(df)} documents")

# Initialize embedding model
print("Loading embedding model...")
model = TextEmbeddingModel.from_pretrained("gemini-embedding-001")

def get_embedding(text: str) -> list:
    """Generate embedding for text, return None if text is empty or error occurs."""
    if not text or not text.strip():
        return None  # Skip empty text instead of zero vector
    try:
        embeddings = model.get_embeddings([text])
        return embeddings[0].values
    except Exception as e:
        print(f"⚠️ Embedding error: {e}")
        return None  # Skip on error instead of zero vector

def format_datetime(dt):
    if dt is None or pd.isna(dt):
        return None
    if isinstance(dt, str):
        try:
            parsed = pd.to_datetime(dt, utc=True)
        except:
            return None
    else:
        try:
            parsed = pd.to_datetime(dt)
            if parsed.tzinfo is None:
                parsed = parsed.tz_localize('UTC')
            else:
                parsed = parsed.tz_convert('UTC')
        except:
            return None
    return parsed.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

# Elasticsearch setup
es = Elasticsearch(
    cloud_id=os.getenv("YOUR_CLOUD_ID"),
    basic_auth=("elastic", os.getenv("YOUR_PASSWORD")),
    request_timeout=300
)

# Delete and recreate index
print(f"\nRecreating Elasticsearch index...")
if es.indices.exists(index=INDEX_NAME):
    es.indices.delete(index=INDEX_NAME)

mapping = {
    "mappings": {
        "properties": {
            "issue_id": {"type": "long"},
            "number": {"type": "long"},
            "title": {"type": "text"},
            "body": {"type": "text"},
            "created_at": {"type": "date"},
            "updated_at": {"type": "date"},
            "closed_at": {"type": "date"},
            "state": {"type": "keyword"},
            "repo_name": {"type": "keyword"},
            "creator": {"type": "keyword"},
            "creator_type": {"type": "keyword"},
            "is_pr": {"type": "boolean"},
            "pr_url": {"type": "keyword"},
            "labels": {"type": "keyword"},
            "assignees": {"type": "keyword"},
            "comments_count": {"type": "integer"},
            "html_url": {"type": "keyword"},
            # 🆕 Contributor-related fields
            "contributor_login": {"type": "keyword"},
            "contributor_role": {"type": "keyword"},
            "contributions": {"type": "integer"},
            "commit_count": {"type": "integer"},
            "embedding": {"type": "dense_vector", "dims": 3072, "index": True, "similarity": "cosine"}
        }
    }
}

es.indices.create(index=INDEX_NAME, body=mapping)
print("Index created")

# Generate embeddings
print(f"\nGenerating embeddings for {len(df)} documents...")
docs = []
skipped = 0

for idx, row in df.iterrows():
    title = row.get('title', '') or ''
    body = row.get('body', '') or ''
    text_to_embed = f"{title} {body} repo: {row.get('repo_name', '')} contributor: {row.get('contributor_login', '')}"

    embedding_vector = get_embedding(text_to_embed)
    
    # Skip if embedding generation failed
    if embedding_vector is None:
        skipped += 1
        continue

    doc = {
        "_index": INDEX_NAME,
        "_id": str(int(row['issue_id'])) if not pd.isna(row.get('issue_id')) else None,
        "_source": {
            "issue_id": int(row['issue_id']) if not pd.isna(row.get('issue_id')) else None,
            "number": int(row['number']) if not pd.isna(row.get('number')) else None,
            "title": title,
            "body": body,
            "created_at": format_datetime(row.get('created_at')),
            "updated_at": format_datetime(row.get('updated_at')),
            "closed_at": format_datetime(row.get('closed_at')),
            "state": str(row.get('state', '')) if not pd.isna(row.get('state')) else '',
            "repo_name": str(row.get('repo_name', '')) if not pd.isna(row.get('repo_name')) else '',
            "creator": str(row.get('creator', '')) if not pd.isna(row.get('creator')) else '',
            "creator_type": str(row.get('creator_type', '')) if not pd.isna(row.get('creator_type')) else '',
            "is_pr": bool(row['is_pr']) if not pd.isna(row.get('is_pr')) else False,
            "pr_url": str(row['pr_url']) if not pd.isna(row.get('pr_url')) else None,
            "labels": list(row['labels']) if isinstance(row.get('labels'), (list, tuple)) else [],
            "assignees": list(row['assignees']) if isinstance(row.get('assignees'), (list, tuple)) else [],
            "comments_count": int(row['comments_count']) if not pd.isna(row.get('comments_count')) else 0,
            "html_url": str(row['html_url']) if not pd.isna(row.get('html_url')) else '',
            # 🆕 Contributor-related fields
            "contributor_login": str(row['contributor_login']) if pd.notna(row.get('contributor_login')) else "",
            "contributor_role": str(row['contributor_role']) if pd.notna(row.get('contributor_role')) else "",
            "contributions": int(row['contributions']) if pd.notna(row.get('contributions')) else 0,
            "commit_count": int(row['commit_count']) if pd.notna(row.get('commit_count')) else 0,
            # 🆕 Embedding vector (CRITICAL - must be included!)
            "embedding": embedding_vector
        }
    }

    docs.append(doc)

    if (idx + 1) % 25 == 0:
        print(f"  Processed {idx + 1}/{len(df)}")

# Index documents
print(f"\n✅ Successfully generated {len(docs)} embeddings")
if skipped > 0:
    print(f"⚠️ Skipped {skipped} documents due to empty text or embedding errors")
print(f"\nIndexing {len(docs)} documents...")
success_count = 0
failed_count = 0

for ok, result in helpers.streaming_bulk(es, docs, raise_on_error=False, chunk_size=10):
    if ok:
        success_count += 1
    else:
        failed_count += 1

print(f"\nIndexed: {success_count} | Failed: {failed_count}")
print("\nDone! Run: python search_query.py")
