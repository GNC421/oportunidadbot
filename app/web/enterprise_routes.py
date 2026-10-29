from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel

from .auth import require_authenticated_user, require_pro_web_user
from app.services.enterprise_service import EnterpriseError, get_enterprise_service

router = APIRouter(prefix="/api/web/enterprise", tags=["enterprise"])
WebUser = Annotated[dict, Depends(require_pro_web_user)]
AuthenticatedUser = Annotated[dict, Depends(require_authenticated_user)]


class OrganizationResponse(BaseModel):
    id: int
    name: str
    seats_purchased: int
    seats_used: int
    seats_available: int


class MemberResponse(BaseModel):
    user_id: int
    parent_user_id: Optional[int]
    role: str
    status: str
    username: str


class TreeResponse(BaseModel):
    organization: OrganizationResponse
    viewer_role: str
    members: list[MemberResponse]


class CreateInvitationRequest(BaseModel):
    role: str
    parent_user_id: Optional[int] = None
    telegram_username: Optional[str] = None


class InvitationResponse(BaseModel):
    id: int
    organization_id: int
    role: str
    token: str
    status: str
    expires_at: str


class AcceptInvitationRequest(BaseModel):
    token: str


class ChangeParentRequest(BaseModel):
    parent_user_id: int


class MemberStatsResponse(BaseModel):
    user_id: int
    username: str
    role: str
    alerts_received: int
    active_sources: int


class TopSourceResponse(BaseModel):
    url: str
    alerts: int


class StatsResponse(BaseModel):
    period_days: int
    has_data: bool
    total_alerts: int
    alerts_in_period: int
    active_sources: int
    total_sources: int
    top_sources: list[TopSourceResponse]
    members: list[MemberStatsResponse]


def _raise(exc: EnterpriseError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=str(exc))


@router.get("/organization", response_model=OrganizationResponse)
async def get_organization(user: WebUser) -> OrganizationResponse:
    service = get_enterprise_service()
    try:
        membership = service.require_context(int(user["id"]))
        organization = service.get_organization(membership.organization_id)
    except EnterpriseError as exc:
        _raise(exc)

    return OrganizationResponse(
        id=organization["id"],
        name=organization["name"],
        seats_purchased=organization["seats_purchased"],
        seats_used=service.seats_used(organization["id"]),
        seats_available=service.seats_available(organization),
    )


@router.get("/tree", response_model=TreeResponse)
async def get_tree(user: WebUser) -> TreeResponse:
    service = get_enterprise_service()
    try:
        tree = service.get_tree(int(user["id"]))
    except EnterpriseError as exc:
        _raise(exc)
    return TreeResponse(**tree)


@router.post("/invitations", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED)
async def create_invitation(payload: CreateInvitationRequest, user: WebUser) -> InvitationResponse:
    service = get_enterprise_service()
    try:
        invitation = service.create_invitation(
            actor_user_id=int(user["id"]),
            role=payload.role,
            parent_user_id=payload.parent_user_id,
            telegram_username=payload.telegram_username,
        )
    except EnterpriseError as exc:
        _raise(exc)
    return InvitationResponse(**invitation)


@router.post("/invitations/accept", response_model=MemberResponse)
async def accept_invitation(payload: AcceptInvitationRequest, user: AuthenticatedUser) -> MemberResponse:
    service = get_enterprise_service()
    try:
        membership = service.accept_invitation(payload.token, int(user["id"]))
    except EnterpriseError as exc:
        _raise(exc)
    return MemberResponse(
        user_id=membership["user_id"],
        parent_user_id=membership.get("parent_user_id"),
        role=membership["role"],
        status=membership["status"],
        username=user.get("username", ""),
    )


@router.patch("/members/{target_user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def change_member_parent(target_user_id: int, payload: ChangeParentRequest, user: WebUser) -> Response:
    service = get_enterprise_service()
    try:
        service.change_parent(int(user["id"]), target_user_id, payload.parent_user_id)
    except EnterpriseError as exc:
        _raise(exc)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/members/{target_user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_member(target_user_id: int, user: WebUser) -> Response:
    service = get_enterprise_service()
    try:
        service.deactivate_member(int(user["id"]), target_user_id)
    except EnterpriseError as exc:
        _raise(exc)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/stats", response_model=StatsResponse)
async def get_stats(user: WebUser, period_days: int = 30) -> StatsResponse:
    service = get_enterprise_service()
    try:
        stats = service.get_stats(int(user["id"]), period_days)
    except EnterpriseError as exc:
        _raise(exc)
    return StatsResponse(**stats)
