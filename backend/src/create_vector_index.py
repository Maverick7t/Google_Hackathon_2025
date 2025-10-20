from elasticsearch import Elasticsearch
from dotenv import load_dotenv
import os

load_dotenv()

# --- Elastic connection ---
es = Elasticsearch(
    cloud_id=os.getenv("YOUR_CLOUD_ID"),
    basic_auth=("elastic", os.getenv("YOUR_PASSWORD"))
)

# Index name
INDEX_NAME = os.getenv("ELASTIC_INDEX", "github_issues")

# Mapping for enriched documents + dense vector embeddings
# ✅ Updated to match new BigQuery schema (now includes contributor info)
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
            # Dense vector for embeddings
            "embedding": {"type": "dense_vector", "dims": 3072, "index": True, "similarity": "cosine"}
        }
    }
}

# Recreate the index if it doesn't exist
if es.indices.exists(index=INDEX_NAME):
    print(f"Index '{INDEX_NAME}' already exists.")
else:
    es.indices.create(index=INDEX_NAME, body=mapping)
    print(f"✅ Created index '{INDEX_NAME}' with enriched fields + dense_vector embedding")
