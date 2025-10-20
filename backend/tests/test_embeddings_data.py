from elasticsearch import Elasticsearch
import os

# Load credentials
from dotenv import load_dotenv
load_dotenv()

es = Elasticsearch(
    cloud_id=os.getenv("YOUR_CLOUD_ID"),
    basic_auth=("elastic", os.getenv("YOUR_PASSWORD")),
    request_timeout=300
)

INDEX_NAME = "github_issues"
contributor_to_check = "MaigoAkisame"

# Elasticsearch query: filter by contributor_login
query = {
    "size": 100,  # adjust if needed
    "_source": ["contributor_login", "commit_count", "title", "repo_name"],
    "query": {
        "term": {
            "contributor_login.keyword": contributor_to_check
        }
    }
}

res = es.search(index=INDEX_NAME, body=query)

if res['hits']['total']['value'] == 0:
    print(f"No contributions found for {contributor_to_check}")
else:
    print(f"Contributions for {contributor_to_check}:")
    for hit in res['hits']['hits']:
        source = hit["_source"]
        print(f"- Repo: {source.get('repo_name')}")
        print(f"  PR/Issue: {source.get('title')}")
        print(f"  Commits: {source.get('commit_count')}\n")
