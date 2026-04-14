"""
GitHub service — handles sync between GitHub Issues/PRs and tasks.
"""
import httpx

from app.core.config import settings


class GitHubService:
    BASE_URL = "https://api.github.com"

    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def get_repo(self, owner: str, repo: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.BASE_URL}/repos/{owner}/{repo}", headers=self.headers)
            resp.raise_for_status()
            return resp.json()

    async def list_issues(self, owner: str, repo: str, state: str = "open") -> list:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}/issues",
                headers=self.headers,
                params={"state": state, "per_page": 100},
            )
            resp.raise_for_status()
            return resp.json()

    async def create_issue(self, owner: str, repo: str, title: str, body: str = "") -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.BASE_URL}/repos/{owner}/{repo}/issues",
                headers=self.headers,
                json={"title": title, "body": body},
            )
            resp.raise_for_status()
            return resp.json()
