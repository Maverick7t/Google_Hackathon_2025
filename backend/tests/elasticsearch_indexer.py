from elasticsearch import Elasticsearch, helpers 
from google.cloud import bigquery
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Elastic connection ---
es = Elasticsearch(
    cloud_id=os.getenv("YOUR_CLOUD_ID"),
    basic_auth=("elastic", os.getenv("YOUR_PASSWORD"))
)

# --- BigQuery connection ---
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
client = bigquery.Client(project="hackathon-github-ai")

query = "SELECT * FROM `hackathon-github-ai.github_data.github_issues` LIMIT 100"
df = client.query(query).to_dataframe()

# --- Insert data into existing index ---
index_name = "github_issues"
print(f"Indexing {len(df)} documents into '{index_name}'...")

actions = [
    {"_index": index_name, "_source": row.to_dict()}
    for _, row in df.iterrows()
]
helpers.bulk(es, actions)
print(f"✅ Successfully indexed {len(df)} documents!")

# --- Test search ---
result = es.search(index="github_issues", query={"match": {"title": "bug"}})
print(f"\n🔍 Test search for 'bug': Found {result['hits']['total']['value']} results")
