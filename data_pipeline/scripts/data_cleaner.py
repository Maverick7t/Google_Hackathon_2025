"""
Data Cleaner Script
Processes raw GitHub data for better quality and consistency
"""

import logging
from typing import List, Dict, Any
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clean_issue_text(text: str) -> str:
    """
    Clean and normalize issue text
    - Remove excessive whitespace
    - Normalize line breaks
    - Remove code blocks for summary
    """
    if not text:
        return ""
    
    # Remove code blocks
    text = re.sub(r'```[\s\S]*?```', '[code]', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    # Limit length for indexing
    if len(text) > 2000:
        text = text[:2000] + "..."
    
    return text


def extract_labels(issue: Dict[str, Any]) -> List[str]:
    """Extract and normalize label names"""
    labels = issue.get('labels', [])
    
    if isinstance(labels, list):
        return [
            label.get('name', '').lower() 
            for label in labels 
            if isinstance(label, dict) and label.get('name')
        ]
    
    return []


def normalize_user(user_data: Dict[str, Any]) -> Dict[str, str]:
    """Normalize user information"""
    if not user_data:
        return {"login": "unknown", "type": "unknown"}
    
    return {
        "login": user_data.get("login", "unknown"),
        "type": user_data.get("type", "User"),
    }


def clean_github_issue(issue: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean a single GitHub issue for BigQuery and Elasticsearch
    
    Args:
        issue: Raw GitHub issue data
    
    Returns:
        Cleaned issue dictionary
    """
    return {
        "id": issue["id"],
        "number": issue["number"],
        "title": clean_issue_text(issue.get("title", "")),
        "body": clean_issue_text(issue.get("body", "")),
        "state": issue.get("state", "unknown"),
        "created_at": issue.get("created_at"),
        "updated_at": issue.get("updated_at"),
        "closed_at": issue.get("closed_at"),
        "user": normalize_user(issue.get("user")),
        "labels": extract_labels(issue),
        "comments": issue.get("comments", 0),
    }


def clean_github_commit(commit: Dict[str, Any]) -> Dict[str, Any]:
    """Clean a single GitHub commit"""
    commit_data = commit.get("commit", {})
    author = commit_data.get("author", {})
    committer = commit_data.get("committer", {})
    
    return {
        "sha": commit["sha"],
        "message": clean_issue_text(commit_data.get("message", "")),
        "author_name": author.get("name", "unknown"),
        "author_email": author.get("email", ""),
        "author_date": author.get("date"),
        "committer_name": committer.get("name", "unknown"),
        "committer_date": committer.get("date"),
    }


def clean_github_pr(pr: Dict[str, Any]) -> Dict[str, Any]:
    """Clean a single GitHub pull request"""
    return {
        "id": pr["id"],
        "number": pr["number"],
        "title": clean_issue_text(pr.get("title", "")),
        "body": clean_issue_text(pr.get("body", "")),
        "state": pr.get("state", "unknown"),
        "created_at": pr.get("created_at"),
        "updated_at": pr.get("updated_at"),
        "merged_at": pr.get("merged_at"),
        "user": normalize_user(pr.get("user")),
        "labels": extract_labels(pr),
        "draft": pr.get("draft", False),
    }


def batch_clean_issues(issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Clean a batch of issues"""
    cleaned = []
    errors = 0
    
    for issue in issues:
        try:
            cleaned.append(clean_github_issue(issue))
        except Exception as e:
            logger.error(f"Error cleaning issue {issue.get('id')}: {str(e)}")
            errors += 1
    
    logger.info(f"Cleaned {len(cleaned)} issues, {errors} errors")
    return cleaned


if __name__ == "__main__":
    # Test the cleaner
    test_issue = {
        "id": 123,
        "number": 456,
        "title": "   Test    Issue   ",
        "body": "Some description with ```python\ncode\n``` blocks",
        "state": "open",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-02T00:00:00Z",
        "closed_at": None,
        "user": {"login": "testuser", "type": "User"},
        "labels": [{"name": "bug"}, {"name": "high-priority"}],
        "comments": 5
    }
    
    cleaned = clean_github_issue(test_issue)
    print("Cleaned issue:")
    print(cleaned)
