import hashlib
import hmac

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_db
from app.integrations.github.webhook_handler import handle_github_event

router = APIRouter()


@router.post("/webhook")
async def github_webhook(
    request: Request,
    x_hub_signature_256: str = Header(None),
    x_github_event: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    body = await request.body()

    # Verify HMAC signature
    if settings.GITHUB_WEBHOOK_SECRET:
        mac = hmac.new(
            settings.GITHUB_WEBHOOK_SECRET.encode(),
            body,
            hashlib.sha256,
        )
        expected = "sha256=" + mac.hexdigest()
        if not hmac.compare_digest(expected, x_hub_signature_256 or ""):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid webhook signature")

    payload = await request.json()
    await handle_github_event(event=x_github_event, payload=payload, db=db)
    return {"message": "ok"}
