"""FastAPI routes for the debug dashboard.

Provides a richer monitoring view: metrics, timeline, search, export and clear.
"""
from __future__ import annotations
from fastapi import APIRouter, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import os
import base64
from typing import Optional
import json
from datetime import datetime

from .trace_service import get_trace_service
from .trace_models import EventType, EventState

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

trace_service = get_trace_service()


def _serialize(ev):
    return {
        "id": str(ev.id),
        "timestamp": ev.timestamp.isoformat(),
        "type": ev.type.value,
        "name": ev.name,
        "state": ev.state.value,
        "duration": ev.duration,
        "input_payload": ev.input_payload,
        "output_payload": ev.output_payload,
        "error": ev.error,
        "traceback": ev.traceback,
        "metadata": ev.metadata,
    }


def _filter_events(events, state=None, service=None, q=None, date_from=None, date_to=None):
    out = []
    for e in events:
        if state and e.state.value != state:
            continue
        if service and e.type.value != service:
            continue
        if q:
            qlow = q.lower()
            found = False
            for v in (e.name, str(e.input_payload or ""), str(e.output_payload or ""), str(e.metadata or "")):
                if qlow in str(v).lower():
                    found = True
                    break
            if not found:
                continue
        if date_from:
            try:
                df = datetime.fromisoformat(date_from)
                if e.timestamp < df:
                    continue
            except Exception:
                pass
        if date_to:
            try:
                dt = datetime.fromisoformat(date_to)
                if e.timestamp > dt:
                    continue
            except Exception:
                pass
        out.append(e)
    return out


def _require_admin(request: Request) -> None:
    """Simple HTTP Basic auth using ADMIN_USERNAME / ADMIN_PASSWORD env vars.

    Raises 401 if missing or invalid.
    """
    auth = request.headers.get("authorization")
    if not auth:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized", headers={"WWW-Authenticate": "Basic realm=\"Admin Area\""})

    if not auth.lower().startswith("basic "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized", headers={"WWW-Authenticate": "Basic realm=\"Admin Area\""})

    try:
        token = auth.split(" ", 1)[1]
        decoded = base64.b64decode(token).decode("utf-8")
        username, password = decoded.split(":", 1)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized", headers={"WWW-Authenticate": "Basic realm=\"Admin Area\""})

    admin_user = os.getenv("ADMIN_USERNAME")
    admin_pass = os.getenv("ADMIN_PASSWORD")
    if not (admin_user and admin_pass and username == admin_user and password == admin_pass):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized", headers={"WWW-Authenticate": "Basic realm=\"Admin Area\""})


@router.get("/debug", response_class=HTMLResponse)
async def debug_dashboard(request: Request, state: Optional[str] = None, service: Optional[str] = None, q: Optional[str] = None, date_from: Optional[str] = None, date_to: Optional[str] = None, event_id: Optional[str] = None, theme: Optional[str] = None, _auth: None = Depends(_require_admin)):
    """Render the advanced debug dashboard with metrics, timeline and filters."""
    events = await trace_service.get_all()

    # Apply filters
    filtered = _filter_events(events, state=state, service=service, q=q, date_from=date_from, date_to=date_to)

    # Metrics
    total_events = len(events)
    total_errors = sum(1 for e in events if e.state == EventState.ERROR)
    ai_calls = sum(1 for e in events if e.type == EventType.AI)
    feeds_processed = 0
    alerts_sent = sum(1 for e in events if e.type == EventType.TELEGRAM and e.state == EventState.SUCCESS)
    ai_durations = [e.duration for e in events if e.type == EventType.AI and e.duration]
    rss_durations = [e.duration for e in events if e.type == EventType.RSS and e.duration]
    scheduler_feeds = []
    for e in events:
        if e.type == EventType.SCHEDULER and e.output_payload:
            try:
                # output_payload may have feeds_checked or feeds
                if isinstance(e.output_payload, dict) and e.output_payload.get("feeds_checked") is not None:
                    feeds_processed += int(e.output_payload.get("feeds_checked") or 0)
                elif isinstance(e.output_payload, dict) and e.output_payload.get("feeds") is not None:
                    feeds_processed += int(e.output_payload.get("feeds") or 0)
            except Exception:
                pass

    avg_ai = round(sum(ai_durations) / len(ai_durations), 3) if ai_durations else None
    avg_rss = round(sum(rss_durations) / len(rss_durations), 3) if rss_durations else None

    # Timeline: group events by scheduler runs; if none, show recent events as a single group
    timeline = []
    sched_events = [e for e in events if e.type == EventType.SCHEDULER]
    if sched_events:
        # sort scheduler events newest first
        sched_events_sorted = sorted(sched_events, key=lambda x: x.timestamp, reverse=True)
        for idx, s in enumerate(sched_events_sorted):
            # determine window until next scheduler event
            next_ts = sched_events_sorted[idx + 1].timestamp if idx + 1 < len(sched_events_sorted) else None
            group = {"scheduler": _serialize(s), "children": []}
            for e in events:
                if e.timestamp <= s.timestamp and (next_ts is None or e.timestamp > next_ts):
                    if e.id == s.id:
                        continue
                    # only include relevant types in the timeline order
                    if e.type in (EventType.RSS, EventType.AI, EventType.DATABASE, EventType.TELEGRAM):
                        group["children"].append(_serialize(e))
            timeline.append(group)
    else:
        # fallback: single group with recent events
        timeline.append({"scheduler": None, "children": [_serialize(e) for e in events[:50]]})

    # Prepare serializable events for list/table
    events_serial = [_serialize(e) for e in filtered]

    # detail
    detail = None
    if event_id:
        ev = await trace_service.get(event_id)
        if ev:
            detail = {
                "id": str(ev.id),
                "name": ev.name,
                "input_payload": json.dumps(ev.input_payload, indent=2, default=str) if ev.input_payload is not None else "",
                "output_payload": json.dumps(ev.output_payload, indent=2, default=str) if ev.output_payload is not None else "",
                "metadata": json.dumps(ev.metadata, indent=2, default=str) if ev.metadata else "",
                "error": ev.error or "",
                "traceback": ev.traceback or "",
            }

    types = [t.value for t in EventType]
    states = [s.value for s in EventState]

    return templates.TemplateResponse("debug_dashboard.html", {"request": request, "events": events_serial, "types": types, "states": states, "selected_service": service, "selected_state": state, "q": q or "", "date_from": date_from or "", "date_to": date_to or "", "detail": detail, "metrics": {"total": total_events, "errors": total_errors, "ai_calls": ai_calls, "feeds_processed": feeds_processed, "alerts_sent": alerts_sent, "avg_ai": avg_ai, "avg_rss": avg_rss}, "timeline": timeline, "theme": theme})


@router.get("/debug/export")
async def debug_export(_auth: None = Depends(_require_admin)):
    events = await trace_service.get_all()
    data = [_serialize(e) for e in events]
    return JSONResponse(content=data)


@router.post("/debug/clear")
async def debug_clear(_auth: None = Depends(_require_admin)):
    await trace_service.clear()
    return RedirectResponse(url="/debug", status_code=303)
