from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field

from app import database
from app.config import settings
from app.services.subscription_service import get_subscription_service

from .auth import SESSION_COOKIE_NAME, create_session_token, require_pro_web_user, verify_telegram_login

router = APIRouter(prefix="/api/web", tags=["private-web"])
WebUser = Annotated[dict, Depends(require_pro_web_user)]


class TelegramLoginPayload(BaseModel):
    id: int = Field(gt=0)
    auth_date: int
    hash: str = Field(min_length=64, max_length=64)
    first_name: str | None = Field(default=None, max_length=255)
    last_name: str | None = Field(default=None, max_length=255)
    username: str | None = Field(default=None, max_length=255)
    photo_url: str | None = Field(default=None, max_length=2048)


class AlertResponse(BaseModel):
    id: int
    title: str
    content: str
    url: str | None
    author: str
    detected_at: str | None
    sent_at: str | None
    source_url: str | None


class FeedResponse(BaseModel):
    id: int
    url: str
    is_active: bool
    created_at: str | None
    last_check: str | None


@router.post("/auth/telegram")
async def login_with_telegram(payload: TelegramLoginPayload, response: Response) -> dict:
    user_id = verify_telegram_login(payload.model_dump())
    user = database.get_user(user_id)
    if not user or not user.get("is_active", True):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not registered")
    if not get_subscription_service().can_access_web_app(user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Professional plan or higher required")

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=create_session_token(user_id),
        max_age=settings.WEB_SESSION_MAX_AGE_SECONDS,
        httponly=True,
        secure=settings.WEB_SESSION_COOKIE_SECURE,
        samesite="lax",
        path="/",
    )
    return {"user": {"id": user_id, "username": user.get("username", ""), "plan": user.get("plan", "starter")}}


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> Response:
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")
    return response


@router.get("/me")
async def get_current_web_user(user: WebUser) -> dict:
    subscription = get_subscription_service().get_current_subscription(int(user["id"]))
    return {"id": user["id"], "username": user.get("username", ""), "plan": subscription.plan.value}


@router.get("/alerts", response_model=list[AlertResponse])
async def list_alerts(user: WebUser, limit: int = 50) -> list[AlertResponse]:
    if not 1 <= limit <= 100:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="limit must be between 1 and 100")

    feeds = {feed["id"]: feed.get("url") for feed in database.get_user_feeds(int(user["id"]))}
    return [
        AlertResponse(
            id=alert["id"],
            title=alert.get("post_title") or "Sin titulo",
            content=alert.get("post_content") or "",
            url=alert.get("post_url"),
            author=alert.get("post_author") or "",
            detected_at=alert.get("detected_at"),
            sent_at=alert.get("sent_at"),
            source_url=feeds.get(alert.get("feed_id")),
        )
        for alert in database.get_user_alerts(int(user["id"]), limit)
    ]


@router.get("/feeds", response_model=list[FeedResponse])
async def list_feeds(user: WebUser) -> list[FeedResponse]:
    return [
        FeedResponse(
            id=feed["id"],
            url=feed["url"],
            is_active=bool(feed.get("is_active", False)),
            created_at=feed.get("created_at"),
            last_check=feed.get("last_check"),
        )
        for feed in database.get_user_feeds(int(user["id"]))
    ]