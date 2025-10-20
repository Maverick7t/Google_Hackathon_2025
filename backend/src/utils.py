"""
Utility functions for DevInsight backend
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Optional
import json

logger = logging.getLogger(__name__)


def load_env_vars() -> dict:
    """Load and validate required environment variables"""
    required_vars = [
        "GCP_PROJECT_ID",
        "ELASTICSEARCH_URL",
    ]
    
    optional_vars = [
        "GITHUB_TOKEN",
        "BIGQUERY_DATASET",
        "VERTEX_AI_LOCATION",
    ]
    
    config = {}
    missing = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing.append(var)
        config[var] = value
    
    for var in optional_vars:
        config[var] = os.getenv(var)
    
    if missing:
        logger.warning(f"Missing required environment variables: {', '.join(missing)}")
    
    return config


def parse_datetime(dt_string: str) -> Optional[datetime]:
    """Parse ISO format datetime string"""
    if not dt_string:
        return None
    
    try:
        return datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
    except ValueError:
        logger.error(f"Invalid datetime format: {dt_string}")
        return None


def get_last_week_start() -> datetime:
    """Get datetime for start of last week"""
    today = datetime.now()
    last_week = today - timedelta(days=7)
    return last_week.replace(hour=0, minute=0, second=0, microsecond=0)


def format_issue_summary(issue: dict) -> str:
    """Format a GitHub issue for display"""
    return (
        f"#{issue.get('number')}: {issue.get('title')}\n"
        f"State: {issue.get('state')} | "
        f"Created: {issue.get('created_at')}\n"
        f"Labels: {', '.join(issue.get('labels', []))}\n"
    )


def calculate_pr_review_time(pr: dict) -> Optional[int]:
    """
    Calculate PR review time in hours
    
    Returns:
        Hours between PR creation and merge, or None if not merged
    """
    if not pr.get('merged_at'):
        return None
    
    created = parse_datetime(pr.get('created_at'))
    merged = parse_datetime(pr.get('merged_at'))
    
    if created and merged:
        delta = merged - created
        return int(delta.total_seconds() / 3600)
    
    return None


def sanitize_query(query: str) -> str:
    """Sanitize user input query"""
    # Remove potentially harmful characters
    sanitized = query.strip()
    sanitized = sanitized[:500]  # Limit length
    return sanitized


def log_api_call(endpoint: str, params: dict, duration_ms: float):
    """Log API call metrics"""
    logger.info(
        f"API Call: {endpoint} | "
        f"Params: {json.dumps(params)} | "
        f"Duration: {duration_ms:.2f}ms"
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    config = load_env_vars()
    print(f"Config loaded: {config}")
