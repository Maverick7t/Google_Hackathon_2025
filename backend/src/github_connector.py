# github_connector.py
import requests
import os
import time
from dotenv import load_dotenv
from typing import List, Dict, Optional

load_dotenv()

GITHUB_API = "https://api.github.com"
DEFAULT_PER_PAGE = 100
RATE_LIMIT_SLEEP = 2  # seconds (backoff on secondary retries)


def _headers(token: Optional[str]) -> Dict[str, str]:
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    return headers


def fetch_github_issues(repo: str, token: str = None, state: str = "all", per_page: int = DEFAULT_PER_PAGE) -> List[Dict]:
    """
    Fetch GitHub issues with full metadata for AI analysis.
    Paginated; returns list of issue dicts.
    DOES NOT fetch commit-level info here — that is merged later from contributors endpoint.
    """
    issues_list = []
    page = 1
    headers = _headers(token)

    while True:
        resp = requests.get(
            f"{GITHUB_API}/repos/{repo}/issues",
            headers=headers,
            params={"state": state, "per_page": per_page, "page": page}
        )
        if resp.status_code == 403 and 'rate limit' in resp.text.lower():
            # simple backoff (you can implement more sophisticated handling)
            print("Rate limited; sleeping 10s...")
            time.sleep(10)
            continue

        if resp.status_code != 200:
            raise Exception(f"GitHub API error {resp.status_code}: {resp.text}")

        data = resp.json()
        if not data:
            break

        for issue in data:
            # Some items returned by /issues are pull requests; keep is_pr flag
            issues_list.append({
                "issue_id": issue["id"],
                "number": issue.get("number"),
                "title": issue.get("title", ""),
                "body": issue.get("body", "") or "",
                "created_at": issue.get("created_at"),
                "closed_at": issue.get("closed_at"),
                "state": issue.get("state"),
                "repo_name": repo,
                "creator": issue.get("user", {}).get("login"),
                "creator_type": issue.get("user", {}).get("type"),
                "is_pr": "pull_request" in issue,
                "pr_url": issue.get("pull_request", {}).get("html_url") if "pull_request" in issue else None,
                "labels": [label["name"] for label in issue.get("labels", [])],
                "assignees": [a.get("login") for a in issue.get("assignees", [])] if issue.get("assignees") else [],
                "comments_count": issue.get("comments", 0),
                "comments_url": issue.get("comments_url"),
                "html_url": issue.get("html_url"),
                # contributor fields populated later by merge_contributor_stats()
                "contributor_login": None,
                "contributor_role": None,
                "contributions": None,
                "commit_count": None,
            })

        print(f"Fetched page {page}: {len(data)} issues")
        page += 1

    return issues_list


def fetch_repo_contributors(repo: str, token: str = None, per_page: int = DEFAULT_PER_PAGE) -> List[Dict]:
    """
    Fetch contributors for a repo using the /contributors endpoint.
    Returns list of dicts: {login, contributions}
    Handles pagination and simple rate-limit backoff.
    """
    contributors = []
    page = 1
    headers = _headers(token)

    while True:
        resp = requests.get(
            f"{GITHUB_API}/repos/{repo}/contributors",
            headers=headers,
            params={"per_page": per_page, "page": page, "anon": "false"}
        )

        if resp.status_code == 202:
            # GitHub may return 202 while it generates stats — wait and retry
            print("Contributors stats compiling (202). Sleeping 3s and retrying...")
            time.sleep(3)
            continue

        if resp.status_code == 403 and 'rate limit' in resp.text.lower():
            print("Rate limited on contributors; sleeping 10s...")
            time.sleep(10)
            continue

        if resp.status_code != 200:
            raise Exception(f"GitHub contributors API error {resp.status_code}: {resp.text}")

        page_data = resp.json()
        if not page_data:
            break

        for c in page_data:
            # contributor endpoint returns login + contributions
            login = c.get("login")
            contributions = c.get("contributions", 0)
            contributors.append({
                "login": login,
                "contributions": contributions
            })

        print(f"Fetched contributors page {page}: {len(page_data)}")
        page += 1

    return contributors


def merge_contributor_stats_into_issues(issues: List[Dict], contributors: List[Dict]) -> List[Dict]:
    """
    Attach contributor totals to each issue if the issue creator appears in contributors.
    - For each issue, if issue['creator'] matches a contributor login, set:
      contributor_login, contributor_role='author', contributions, commit_count
    - If not found, leave contributor_* fields as None.
    """
    contrib_map = {c["login"]: c["contributions"] for c in contributors if c.get("login")}
    for issue in issues:
        creator = issue.get("creator")
        if creator and creator in contrib_map:
            issue["contributor_login"] = creator
            issue["contributor_role"] = "author"
            issue["contributions"] = contrib_map[creator]
            issue["commit_count"] = contrib_map[creator]
        else:
            # leave None; caller can choose to set defaults if desired
            issue["contributor_login"] = issue.get("creator")
            issue["contributor_role"] = "author" if issue.get("creator") else None
            # contributions/commit_count left None to indicate unknown
    return issues


# ---------- TEST BLOCK ----------
if __name__ == "__main__":
    token = os.getenv("GITHUB_TOKEN")
    repo = "facebookresearch/fairseq"

    print(f"Fetching all issues from {repo}...")
    issues = fetch_github_issues(repo, token, state="all", per_page=100)
    print(f"✅ Total issues fetched: {len(issues)}")

    print(f"\nFetching contributors for {repo}...")
    contributors = fetch_repo_contributors(repo, token, per_page=100)
    print(f"✅ Contributors fetched: {len(contributors)}")
    if contributors:
        print("Top contributors sample:", contributors[:5])

    print("\nMerging contributor stats into issues (matching by creator)...")
    merged = merge_contributor_stats_into_issues(issues, contributors)
    # print a sample
    sample = merged[0]
    print("\nSample merged issue:\n", {
        "issue_id": sample["issue_id"],
        "creator": sample["creator"],
        "contributor_login": sample["contributor_login"],
        "contributions": sample["contributions"],
        "commit_count": sample["commit_count"]
    })
