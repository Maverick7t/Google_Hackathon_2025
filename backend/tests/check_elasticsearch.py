from elasticsearch import Elasticsearch
import os
from dotenv import load_dotenv

load_dotenv()

es = Elasticsearch(
    cloud_id=os.getenv("YOUR_CLOUD_ID"),
    basic_auth=("elastic", os.getenv("YOUR_PASSWORD")),
    request_timeout=300
)

index_name = os.getenv("ELASTIC_INDEX", "github_issues")

# Check if index exists
if es.indices.exists(index=index_name):
    print(f"✅ Index '{index_name}' exists")
    
    # Count documents
    count = es.count(index=index_name)
    print(f"📊 Document count: {count['count']}")
    
    # Show sample document
    results = es.search(index=index_name, size=1)
    if results['hits']['hits']:
        doc = results['hits']['hits'][0]['_source']
        print(f"\n📄 Sample document:")
        print(f"  Title: {doc.get('title')}")
        print(f"  Contributor: {doc.get('contributor_login')}")
        print(f"  Has embedding: {'embedding' in doc}")
else:
    print(f"❌ Index '{index_name}' does NOT exist")