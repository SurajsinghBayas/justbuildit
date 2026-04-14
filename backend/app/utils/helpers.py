import re
import uuid
from typing import Any


def generate_id() -> str:
    return str(uuid.uuid4())


def slugify(text: str) -> str:
    """Convert a string to a URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text


def paginate(query, page: int = 1, page_size: int = 20) -> dict[str, Any]:
    """Helper for consistent pagination metadata."""
    return {
        "page": page,
        "page_size": page_size,
        "offset": (page - 1) * page_size,
    }
