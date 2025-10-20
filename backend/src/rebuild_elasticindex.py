"""
Rebuild Elasticsearch index with proper dense_vector mapping.
Run this BEFORE generate_embedding.py
"""
import os
from dotenv import load_dotenv
from elasticsearch import Elasticsearch

load_dotenv()

INDEX_NAME = os.getenv("ELASTIC_INDEX", "github_issues")

es = Elasticsearch(
    cloud_id=os.getenv("YOUR_CLOUD_ID"),
    basic_auth=("elastic", os.getenv("YOUR_PASSWORD")),
    request_timeout=300
)

print(f"Connecting to Elasticsearch...")

# Delete old index
if es.indices.exists(index=INDEX_NAME):
    print(f"Deleting old index: {INDEX_NAME}")
    es.indices.delete(index=INDEX_NAME)
    print("✓ Deleted")

# Create index with correct mapping
mapping = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0
    },
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
            "contributor_login": {"type": "keyword"},
            "contributor_role": {"type": "keyword"},
            "contributions": {"type": "integer"},
            "commit_count": {"type": "integer"},
            "embedding": {
                "type": "dense_vector",
                "dims": 3072,
                "index": True,
                "similarity": "cosine"
            }
        }
    }
}

print(f"Creating index: {INDEX_NAME}")
es.indices.create(index=INDEX_NAME, body=mapping)
print("✓ Index created with proper dense_vector mapping")

# Verify
index_info = es.indices.get(index=INDEX_NAME)
print(f"\n✓ Index info:")
print(f"  Shards: {index_info[INDEX_NAME]['settings']['index']['number_of_shards']}")
print(f"  Embedding field type: {index_info[INDEX_NAME]['mappings']['properties']['embedding']['type']}")
print(f"  Embedding dims: {index_info[INDEX_NAME]['mappings']['properties']['embedding']['dims']}")
print(f"\n✅ Ready! Now run: python generate_embedding.py")