"""
Fivetran Connector for GitHub Data
Pulls issues, commits, and PRs from public GitHub repos
"""

import logging
from datetime import datetime
from typing import Dict, List, Any
import requests
import os

logger = logging.getLogger(__name__)


class GitHubConnector:
    """
    Fivetran-compatible GitHub data connector
    Implements incremental sync for issues, commits, and pull requests
    """
    
    def __init__(self, github_token: str = None):
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        if self.github_token:
            self.headers["Authorization"] = f"token {self.github_token}"
    
    def fetch_issues(self, repo: str, since: datetime = None) -> List[Dict[str, Any]]:
        """
        Fetch issues from a GitHub repository
        
        Args:
            repo: Repository in format 'owner/repo'
            since: Only issues updated after this date
        
        Returns:
            List of issue dictionaries
        """
        endpoint = f"{self.base_url}/repos/{repo}/issues"
        params = {
            "state": "all",
            "per_page": 100,
            "sort": "updated",
            "direction": "desc"
        }
        
        if since:
            params["since"] = since.isoformat()
        
        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            issues = response.json()
            
            logger.info(f"Fetched {len(issues)} issues from {repo}")
            return issues
        except requests.RequestException as e:
            logger.error(f"Failed to fetch issues: {str(e)}")
            raise
    
    def fetch_commits(self, repo: str, since: datetime = None) -> List[Dict[str, Any]]:
        """Fetch commits from a GitHub repository"""
        endpoint = f"{self.base_url}/repos/{repo}/commits"
        params = {"per_page": 100}
        
        if since:
            params["since"] = since.isoformat()
        
        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            commits = response.json()
            
            logger.info(f"Fetched {len(commits)} commits from {repo}")
            return commits
        except requests.RequestException as e:
            logger.error(f"Failed to fetch commits: {str(e)}")
            raise
    
    def fetch_pull_requests(self, repo: str, since: datetime = None) -> List[Dict[str, Any]]:
        """Fetch pull requests from a GitHub repository"""
        endpoint = f"{self.base_url}/repos/{repo}/pulls"
        params = {
            "state": "all",
            "per_page": 100,
            "sort": "updated",
            "direction": "desc"
        }
        
        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            prs = response.json()
            
            logger.info(f"Fetched {len(prs)} pull requests from {repo}")
            return prs
        except requests.RequestException as e:
            logger.error(f"Failed to fetch pull requests: {str(e)}")
            raise


def sync_repository(repo: str, last_sync: datetime = None) -> Dict[str, int]:
    """
    Main sync function for a repository
    
    Returns:
        Dictionary with counts of synced items
    """
    connector = GitHubConnector()
    
    results = {
        "issues": 0,
        "commits": 0,
        "pull_requests": 0
    }
    
    try:
        issues = connector.fetch_issues(repo, since=last_sync)
        commits = connector.fetch_commits(repo, since=last_sync)
        prs = connector.fetch_pull_requests(repo, since=last_sync)
        
        # TODO: Load into BigQuery
        # TODO: Index into Elasticsearch
        
        results["issues"] = len(issues)
        results["commits"] = len(commits)
        results["pull_requests"] = len(prs)
        
        logger.info(f"Sync complete for {repo}: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Repository sync failed: {str(e)}")
        raise


if __name__ == "__main__":
    # Test the connector
    logging.basicConfig(level=logging.INFO)
    test_repo = "torvalds/linux"  # Public repo for testing
    sync_repository(test_repo)
