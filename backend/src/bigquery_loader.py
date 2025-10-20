import os
import time
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()

# --- BigQuery configuration ---
SERVICE_ACCOUNT_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "hackathon-github-ai")
DATASET_ID = "github_analytics"
TABLE_ID = f"{PROJECT_ID}.{DATASET_ID}.github_issues"

# Authenticate BigQuery client
client = bigquery.Client.from_service_account_json(SERVICE_ACCOUNT_PATH)

# --- Extended unified schema for issues + contributor data ---
schema = [
    bigquery.SchemaField("issue_id", "INTEGER", mode="REQUIRED"),
    bigquery.SchemaField("number", "INTEGER"),
    bigquery.SchemaField("title", "STRING"),
    bigquery.SchemaField("body", "STRING"),
    bigquery.SchemaField("created_at", "TIMESTAMP"),
    bigquery.SchemaField("updated_at", "TIMESTAMP"),
    bigquery.SchemaField("closed_at", "TIMESTAMP"),
    bigquery.SchemaField("state", "STRING"),
    bigquery.SchemaField("repo_name", "STRING"),
    bigquery.SchemaField("creator", "STRING"),
    bigquery.SchemaField("creator_type", "STRING"),
    bigquery.SchemaField("is_pr", "BOOLEAN"),
    bigquery.SchemaField("pr_url", "STRING"),
    bigquery.SchemaField("labels", "STRING", mode="REPEATED"),
    bigquery.SchemaField("assignees", "STRING", mode="REPEATED"),
    bigquery.SchemaField("comments_count", "INTEGER"),
    bigquery.SchemaField("comments_url", "STRING"),
    bigquery.SchemaField("html_url", "STRING"),
    # Contributor-related fields
    bigquery.SchemaField("contributor_login", "STRING"),
    bigquery.SchemaField("contributor_role", "STRING"),
    bigquery.SchemaField("contributions", "INTEGER"),
    bigquery.SchemaField("commit_count", "INTEGER"),
]

# --- Create dataset and table if not exist ---
def create_table_if_not_exists(force_recreate=False):
    dataset_ref = f"{PROJECT_ID}.{DATASET_ID}"
    try:
        client.get_dataset(dataset_ref)
    except Exception:
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = "US"
        client.create_dataset(dataset)
        print(f"✓ Created dataset {dataset_ref}")

    try:
        client.get_table(TABLE_ID)
        if force_recreate:
            print(f"⚠ Deleting existing table {TABLE_ID}...")
            client.delete_table(TABLE_ID)
            print(f"✓ Deleted old table")
        else:
            print(f"✓ Table {TABLE_ID} already exists.")
            return
    except Exception:
        pass

    table = bigquery.Table(TABLE_ID, schema=schema)
    client.create_table(table)
    print(f"✓ Created table {TABLE_ID} with updated schema.")


# --- Safe batched insert ---
def insert_rows_to_bigquery(rows_to_insert, batch_size=500):
    """
    Insert rows into BigQuery in batches to prevent timeout or payload errors.
    """
    if not rows_to_insert:
        print("No rows to insert.")
        return

    create_table_if_not_exists(force_recreate=False)

    total_rows = len(rows_to_insert)
    print(f"📦 Preparing to insert {total_rows} rows into BigQuery (batch size: {batch_size})...")

    for start in range(0, total_rows, batch_size):
        end = min(start + batch_size, total_rows)
        batch = rows_to_insert[start:end]

        formatted_rows = []
        for issue in batch:
            row = {
                "issue_id": issue.get("issue_id"),
                "number": issue.get("number"),
                "title": issue.get("title", ""),
                "body": issue.get("body", ""),
                "created_at": issue.get("created_at"),
                "updated_at": issue.get("updated_at"),
                "closed_at": issue.get("closed_at"),
                "state": issue.get("state", ""),
                "repo_name": issue.get("repo_name", ""),
                "creator": issue.get("creator", ""),
                "creator_type": issue.get("creator_type", ""),
                "is_pr": issue.get("is_pr", False),
                "pr_url": issue.get("pr_url"),
                "labels": issue.get("labels", []),
                "assignees": issue.get("assignees", []),
                "comments_count": issue.get("comments_count", 0),
                "comments_url": issue.get("comments_url"),
                "html_url": issue.get("html_url"),
                "contributor_login": issue.get("contributor_login"),
                "contributor_role": issue.get("contributor_role"),
                "contributions": issue.get("contributions"),
                "commit_count": issue.get("commit_count"),
            }
            formatted_rows.append(row)

        errors = client.insert_rows_json(TABLE_ID, formatted_rows)
        if errors:
            print(f"❌ Errors inserting batch {start // batch_size + 1}: {errors}")
        else:
            print(f"✅ Successfully inserted rows {start + 1}-{end}/{total_rows}")
        time.sleep(1)  # small delay to avoid API throttling


# --- Example test block ---
if __name__ == "__main__":
    from github_connector import fetch_github_issues, fetch_repo_contributors, merge_contributor_stats_into_issues
    token = os.getenv("GITHUB_TOKEN")
    repo = "facebookresearch/fairseq"

    print(f"📡 Fetching issues from {repo}...")
    issues = fetch_github_issues(repo, token)

    print(f"\n📡 Fetching contributors for {repo}...")
    contributors = fetch_repo_contributors(repo, token)

    print("\n🔗 Merging contributor stats into issues...")
    merged_issues = merge_contributor_stats_into_issues(issues, contributors)

    print(f"📊 Inserting {len(merged_issues)} issues into BigQuery (batched)...")
    insert_rows_to_bigquery(merged_issues, batch_size=300)
