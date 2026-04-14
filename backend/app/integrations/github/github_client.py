from app.services.github_service import GitHubService


def get_github_client(token: str) -> GitHubService:
    """Factory to create a GitHubService with the given token."""
    return GitHubService(token=token)
