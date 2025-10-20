"""
Quick test to verify data is in BigQuery
"""
from google.cloud import bigquery
import os
from dotenv import load_dotenv

load_dotenv()

SERVICE_ACCOUNT_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "hackathon-github-ai")

client = bigquery.Client.from_service_account_json(SERVICE_ACCOUNT_PATH)

# Query the data
query = """
SELECT 
    COUNT(*) as total_rows,
    COUNT(DISTINCT issue_id) as unique_issues,
    MIN(created_at) as oldest_issue,
    MAX(created_at) as newest_issue
FROM `hackathon-github-ai.github_data.github_issues`
"""

print("Querying BigQuery...")
result = client.query(query).result()

for row in result:
    print(f"\n✓ Total rows: {row.total_rows}")
    print(f"✓ Unique issues: {row.unique_issues}")
    print(f"✓ Oldest issue: {row.oldest_issue}")
    print(f"✓ Newest issue: {row.newest_issue}")

# Show sample data
print("\n--- Sample Issues ---")
sample_query = """
SELECT issue_id, title, state, created_at
FROM `hackathon-github-ai.github_data.github_issues`
LIMIT 5
"""

sample_result = client.query(sample_query).result()
for row in sample_result:
    print(f"\nID: {row.issue_id}")
    print(f"Title: {row.title}")
    print(f"State: {row.state}")
    print(f"Created: {row.created_at}")
