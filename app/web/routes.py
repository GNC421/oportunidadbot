from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from urllib.parse import urlencode

from app import database
from app.config import settings
from app.services.subscription_service import get_subscription_service

from .auth import (
    LOGIN_STATE_COOKIE_NAME,
    SESSION_COOKIE_NAME,
    TELEGRAM_AUTHORIZATION_URL,
    create_login_state,
    create_session_token,
    exchange_telegram_code,
    read_login_state,
    require_pro_web_user,
    verify_telegram_id_token,
)

router = APIRouter(prefix="/api/web", tags=["private-web"])
WebUser = Annotated[dict, Depends(require_pro_web_user)]


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


@router.get("/auth/telegram/start")
async def start_telegram_login() -> RedirectResponse:
    from app.web.auth import _require_oidc_config

    client_id, _, redirect_uri, web_app_origin = _require_oidc_config()
    state_cookie, state, nonce, challenge = create_login_state()
    # include origin so Telegram can correctly handle web flows
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'openid profile',
        'state': state,
        'nonce': nonce,
        'code_challenge': challenge,
        'code_challenge_method': 'S256',
        'origin': web_app_origin,
    }
    authorization_url = f"{TELEGRAM_AUTHORIZATION_URL}?{urlencode(params)}"

    # Try fetching authorization URL server-side to detect a tg:// redirect and convert to t.me web link
    from app.web.auth import get_bot_username
    import httpx

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=False) as client:
            resp = await client.get(authorization_url)
        loc = resp.headers.get('location') or resp.headers.get('Location')
        if loc and loc.startswith('tg://'):
            # extract start token
            import re

            m = re.search(r'(?:startapp|start)=([^&]+)', loc)
            token = m.group(1) if m else None
            bot = await get_bot_username()
            if bot and token:
                web_link = f"https://t.me/{bot}?start={token}"
                response = RedirectResponse(web_link, status_code=status.HTTP_302_FOUND)
            else:
                response = RedirectResponse(authorization_url, status_code=status.HTTP_302_FOUND)
        else:
            response = RedirectResponse(authorization_url, status_code=status.HTTP_302_FOUND)
    except Exception:
        response = RedirectResponse(authorization_url, status_code=status.HTTP_302_FOUND)

    response.set_cookie(key=LOGIN_STATE_COOKIE_NAME, value=state_cookie, max_age=600, httponly=True, secure=settings.WEB_SESSION_COOKIE_SECURE, samesite="lax", path="/api/web/auth/telegram")
    return response


@router.get("/auth/telegram/callback")
async def telegram_login_callback(code: str, state: str, request: Request) -> RedirectResponse:
    from app.web.auth import _require_oidc_config

    _, _, _, web_app_origin = _require_oidc_config()
    nonce, verifier = read_login_state(request.cookies.get(LOGIN_STATE_COOKIE_NAME), state)
    id_token = await exchange_telegram_code(code, verifier)
    user_id = verify_telegram_id_token(id_token, nonce)
    user = database.get_user(user_id)
    if not user or not user.get("is_active", True):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not registered")
    if not get_subscription_service().can_access_web_app(user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Professional plan or higher required")

    response = RedirectResponse(web_app_origin, status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=create_session_token(user_id),
        max_age=settings.WEB_SESSION_MAX_AGE_SECONDS,
        httponly=True,
        secure=settings.WEB_SESSION_COOKIE_SECURE,
        samesite="lax",
        path="/",
    )
    response.delete_cookie(key=LOGIN_STATE_COOKIE_NAME, path="/api/web/auth/telegram")
    return response


@router.post("/auth/telegram/widget")
async def telegram_widget_login(request: Request) -> Response:
    """Accepts Telegram Login Widget data posted from the client, verifies it and sets session cookie."""
    from app.web.auth import verify_telegram_widget_data

    payload = await request.json()
    telegram_id = verify_telegram_widget_data(payload)
    user = database.get_user(telegram_id)
    if not user or not user.get("is_active", True):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not registered")
    if not get_subscription_service().can_access_web_app(telegram_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Professional plan or higher required")

    response = Response(status_code=status.HTTP_200_OK)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=create_session_token(telegram_id),
        max_age=settings.WEB_SESSION_MAX_AGE_SECONDS,
        httponly=True,
        secure=settings.WEB_SESSION_COOKIE_SECURE,
        samesite="lax",
        path="/",
    )
    return response


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