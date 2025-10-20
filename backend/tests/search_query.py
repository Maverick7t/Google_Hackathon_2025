# search_query.py - Hybrid Contributor-aware search using Elasticsearch + Vertex AI embeddings
import os
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv

from elasticsearch import Elasticsearch
from vertexai.language_models import TextEmbeddingModel
from vertexai.generative_models import GenerativeModel

load_dotenv()

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "hackathon-github-ai")
LOCATION = "us-central1"
INDEX_NAME = os.getenv("ELASTIC_INDEX", "github_issues")

# Initialize Vertex AI
embedding_model = TextEmbeddingModel.from_pretrained("gemini-embedding-001")
gemini_model = GenerativeModel("gemini-2.5-flash")

# Initialize Elasticsearch
es = Elasticsearch(
    cloud_id=os.getenv("YOUR_CLOUD_ID"),
    basic_auth=("elastic", os.getenv("YOUR_PASSWORD")),
    request_timeout=300
)

# ------------------- Helper functions -------------------

def detect_query_type(user_query):
    query_lower = user_query.lower()
    date_keywords = ["most recent", "latest", "last month", "this week", "this month", "when", "recently closed"]
    for keyword in date_keywords:
        if keyword in query_lower:
            return "date_query"
    return "semantic_query"


def get_date_ranges(user_query):
    today = datetime.now().astimezone()

    if "last month" in user_query.lower():
        first_day_this_month = today.replace(day=1)
        last_day_last_month = first_day_this_month - timedelta(days=1)
        first_day_last_month = last_day_last_month.replace(day=1)
        return first_day_last_month.strftime("%Y-%m-%d"), last_day_last_month.strftime("%Y-%m-%d")

    elif "this week" in user_query.lower():
        start_of_week = today - timedelta(days=today.weekday())
        return start_of_week.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")

    elif "this month" in user_query.lower():
        first_day = today.replace(day=1)
        return first_day.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")

    return None, None


def generate_query_embedding(query_text):
    embeddings = embedding_model.get_embeddings([query_text])
    return embeddings[0].values


def extract_contributor_name(user_query):
    """
    Extract explicit contributor name from query like "by alice" or "from bob".
    Returns contributor name or None if not found.
    """
    query_lower = user_query.lower()
    
    # Match patterns like "by <name>" or "from <name>"
    by_match = re.search(r'\bby\s+([a-z][a-z0-9_-]*)\b', query_lower)
    if by_match:
        return by_match.group(1)
    
    from_match = re.search(r'\bfrom\s+([a-z][a-z0-9_-]*)\b', query_lower)
    if from_match:
        return from_match.group(1)
    
    return None


# ------------------- Hybrid Search -------------------

def hybrid_search(query_text, top_k=10, date_start=None, date_end=None, sort_by_date=False):
    """
    Hybrid search in Elasticsearch using:
    - Dense vector embeddings (cosine similarity via kNN)
    - Keyword matching for issue title, body, labels
    - Date filters
    - Optional contributor filter (only if explicitly specified with "by" or "from")
    """
    # --- Extract explicit contributor name ---
    contributor_name = extract_contributor_name(query_text)
    if contributor_name:
        print(f"🎯 Detected explicit contributor filter: {contributor_name}")

    # --- Build filters ---
    must_filters = []

    if contributor_name:
        must_filters.append({"term": {"contributor_login": contributor_name}})

    if date_start and date_end:
        must_filters.append({
            "range": {
                "created_at": {
                    "gte": f"{date_start}T00:00:00Z",
                    "lte": f"{date_end}T23:59:59Z"
                }
            }
        })

    # --- Generate query embedding ---
    query_emb = generate_query_embedding(query_text)

    # --- Build Elasticsearch query with kNN vector search ---
    es_query = {
        "size": top_k,
        "query": {
            "bool": {
                "must": must_filters if must_filters else [{"match_all": {}}],
                "should": [
                    {
                        "knn": {
                            "embedding": {
                                "vector": query_emb,
                                "k": top_k,
                                "boost": 2
                            }
                        }
                    },
                    {"match": {"title": {"query": query_text, "boost": 3}}},
                    {"match": {"body": {"query": query_text, "boost": 2}}},
                    {"match": {"labels": {"query": query_text, "boost": 2}}},
                    {"match": {"state": {"query": "closed", "boost": 1}}},
                ],
                "minimum_should_match": 1
            }
        }
    }

    if sort_by_date:
        es_query["sort"] = [{"created_at": {"order": "desc"}}]

    response = es.search(index=INDEX_NAME, body=es_query)
    return [hit["_source"] for hit in response["hits"]["hits"]]


# ------------------- Build context for Gemini -------------------

def build_context(issues):
    context_lines = []
    # Sort issues by commit_count descending to prioritize top contributors
    sorted_issues = sorted(issues, key=lambda i: i.get('commit_count') or 0, reverse=True)
    for idx, issue in enumerate(sorted_issues, 1):
        context_lines.append(f"""
Issue #{idx}:
- Title: {issue.get('title')}
- Repo: {issue.get('repo_name')}
- State: {issue.get('state')}
- Created: {issue.get('created_at')}
- Closed: {issue.get('closed_at')}
- Contributor: {issue.get('contributor_login')}
- Commit Count: {issue.get('commit_count')}
- Labels: {', '.join(issue.get('labels') or [])}
- Body: {issue.get('body','')[:200]}
        """)
    return "\n".join(context_lines)


def answer_query_with_gemini(user_query, context):
    today = datetime.now().astimezone().strftime("%Y-%m-%d")
    prompt = f"""Today's date is {today}.

User Question: {user_query}

Retrieved Issues Data:
{context}

Instructions:
1. Answer the user's question DIRECTLY based on the data provided.
2. ALWAYS include exact titles, contributors, and dates in your answer.
3. If asking for "most recent", show the issue with the LATEST created_at date.
4. If asking "who has most commit", analyze the commit_count field and identify the top contributor.
5. If NO relevant data, say "No matching issues found".
6. Be concise and factual.

Answer:"""

    response = gemini_model.generate_content(prompt)
    return response.text


# ------------------- Main -------------------

if __name__ == "__main__":
    print("\n🔍 Ask a question about your GitHub issues.\n")
    user_query = input("Your question: ")

    query_type = detect_query_type(user_query)
    print(f"🎯 Query type detected: {query_type}")

    date_start, date_end = get_date_ranges(user_query)
    if date_start:
        print(f"📅 Date filter: {date_start} to {date_end}")

    print("\n🔎 Searching in Elasticsearch...")
    sort_by_date = (query_type == "date_query")
    retrieved_issues = hybrid_search(
        user_query,
        top_k=10,
        date_start=date_start,
        date_end=date_end,
        sort_by_date=sort_by_date
    )

    if not retrieved_issues:
        print("❌ No issues found matching your criteria.")
    else:
        print(f"✅ Found {len(retrieved_issues)} relevant issues.")

        print("\n📊 DEBUG - Top 3 issues with contributors:")
        for i, issue in enumerate(retrieved_issues[:3], 1):
            print(f"  Issue {i}: closed_at={issue.get('closed_at')} | title={issue.get('title')[:50]} | contributor={issue.get('contributor_login')}")

        context = build_context(retrieved_issues)
        print("\n🤖 Asking Gemini...\n")
        answer = answer_query_with_gemini(user_query, context)

        print("=" * 60)
        print("💡 Answer:")
        print("=" * 60)
        print(answer)