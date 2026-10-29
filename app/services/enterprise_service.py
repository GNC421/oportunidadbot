from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

from app import database

INVITATION_TTL_DAYS = 7
ALLOWED_STATS_PERIODS = (7, 30, 90)


class EnterpriseRole(str, Enum):
    OWNER = "OWNER"
    MANAGER = "MANAGER"
    EMPLOYEE = "EMPLOYEE"


class EnterpriseError(Exception):
    """Raised for any Enterprise authorization/validation failure, carrying its HTTP status."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass(frozen=True)
class Membership:
    organization_id: int
    user_id: int
    parent_user_id: Optional[int]
    role: EnterpriseRole
    status: str

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "Membership":
        return cls(
            organization_id=int(row["organization_id"]),
            user_id=int(row["user_id"]),
            parent_user_id=int(row["parent_user_id"]) if row.get("parent_user_id") is not None else None,
            role=EnterpriseRole(row["role"]),
            status=str(row.get("status", "active")),
        )


class EnterpriseService:
    """Resuelve jerarquía, licencias e invitaciones Enterprise reutilizando users/feeds/alerts existentes."""

    def get_context(self, user_id: int) -> Optional[Membership]:
        """Devuelve la membresía ACTIVA de un usuario, o None si no pertenece (o ya no) a ninguna organización."""
        row = database.get_enterprise_membership(user_id)
        if not row or row.get("status") != "active":
            return None
        return Membership.from_row(row)

    def require_context(self, user_id: int) -> Membership:
        membership = self.get_context(user_id)
        if not membership:
            raise EnterpriseError("No perteneces a ninguna organización Enterprise", 403)
        return membership

    def get_organization(self, organization_id: int) -> dict[str, Any]:
        organization = database.get_enterprise_organization(organization_id)
        if not organization:
            raise EnterpriseError("Organización Enterprise no encontrada", 404)
        return organization

    def _active_members(self, organization_id: int) -> list[dict[str, Any]]:
        return [row for row in database.list_enterprise_members(organization_id) if row.get("status") == "active"]

    def seats_used(self, organization_id: int) -> int:
        return len(self._active_members(organization_id))

    def seats_reserved(self, organization_id: int) -> int:
        """Asientos activos más invitaciones pendientes no expiradas (evita sobre-invitar)."""
        pending = [
            invitation
            for invitation in database.list_pending_enterprise_invitations(organization_id)
            if not self._is_expired(invitation)
        ]
        return self.seats_used(organization_id) + len(pending)

    def seats_available(self, organization: dict[str, Any]) -> int:
        reserved = self.seats_reserved(int(organization["id"]))
        return max(0, int(organization["seats_purchased"]) - reserved)

    @staticmethod
    def _is_expired(invitation: dict[str, Any]) -> bool:
        expires_at = invitation.get("expires_at")
        if not expires_at:
            return False
        try:
            return datetime.fromisoformat(str(expires_at).replace("Z", "+00:00")).replace(tzinfo=None) < datetime.utcnow()
        except ValueError:
            return False

    def get_visible_members(self, membership: Membership) -> list[dict[str, Any]]:
        """Miembros activos visibles para `membership`: él mismo + su subárbol (todo el árbol si es OWNER)."""
        active = self._active_members(membership.organization_id)
        if membership.role == EnterpriseRole.OWNER:
            return active

        by_parent: dict[Optional[int], list[dict[str, Any]]] = {}
        by_user: dict[int, dict[str, Any]] = {}
        for row in active:
            by_user[int(row["user_id"])] = row
            by_parent.setdefault(row.get("parent_user_id"), []).append(row)

        visible: list[dict[str, Any]] = []
        queue = [membership.user_id]
        seen: set[int] = set()
        while queue:
            current = queue.pop(0)
            if current in seen:
                continue
            seen.add(current)
            row = by_user.get(current)
            if row is not None:
                visible.append(row)
            for child in by_parent.get(current, []):
                queue.append(int(child["user_id"]))
        return visible

    def get_tree(self, user_id: int) -> dict[str, Any]:
        membership = self.require_context(user_id)
        organization = self.get_organization(membership.organization_id)
        visible = self.get_visible_members(membership)
        user_ids = [int(row["user_id"]) for row in visible]
        users_by_id = {int(row["id"]): row for row in database.list_users_by_ids(user_ids)}

        members = [
            {
                "user_id": int(row["user_id"]),
                "parent_user_id": row.get("parent_user_id"),
                "role": row["role"],
                "status": row["status"],
                "username": users_by_id.get(int(row["user_id"]), {}).get("username", ""),
            }
            for row in visible
        ]
        return {
            "organization": {
                "id": organization["id"],
                "name": organization["name"],
                "seats_purchased": organization["seats_purchased"],
                "seats_used": self.seats_used(membership.organization_id),
                "seats_available": self.seats_available(organization),
            },
            "viewer_role": membership.role.value,
            "members": members,
        }

    def _member_row(self, organization_id: int, user_id: int) -> Optional[dict[str, Any]]:
        for row in database.list_enterprise_members(organization_id):
            if int(row["user_id"]) == user_id:
                return row
        return None

    def _descendant_ids(self, organization_id: int, user_id: int) -> set[int]:
        active = self._active_members(organization_id)
        by_parent: dict[Optional[int], list[int]] = {}
        for row in active:
            by_parent.setdefault(row.get("parent_user_id"), []).append(int(row["user_id"]))

        descendants: set[int] = set()
        queue = list(by_parent.get(user_id, []))
        while queue:
            current = queue.pop(0)
            if current in descendants:
                continue
            descendants.add(current)
            queue.extend(by_parent.get(current, []))
        return descendants

    def create_invitation(
        self,
        actor_user_id: int,
        role: str,
        parent_user_id: Optional[int] = None,
        telegram_username: Optional[str] = None,
    ) -> dict[str, Any]:
        actor = self.require_context(actor_user_id)
        if actor.role == EnterpriseRole.EMPLOYEE:
            raise EnterpriseError("No tienes permisos para invitar empleados", 403)

        try:
            invitation_role = EnterpriseRole(role)
        except ValueError:
            raise EnterpriseError("El rol indicado no es válido", 422)
        if invitation_role == EnterpriseRole.OWNER:
            raise EnterpriseError("No se puede invitar a un nuevo OWNER", 422)

        effective_parent = parent_user_id or actor.user_id
        visible_ids = {row["user_id"] for row in self.get_visible_members(actor)}
        if effective_parent not in visible_ids:
            raise EnterpriseError("No puedes asignar empleados fuera de tu equipo", 403)

        organization = self.get_organization(actor.organization_id)
        if self.seats_available(organization) <= 0:
            raise EnterpriseError("No hay licencias Enterprise disponibles.", 409)

        token = secrets.token_urlsafe(32)
        expires_at = (datetime.utcnow() + timedelta(days=INVITATION_TTL_DAYS)).isoformat()
        invitation = database.create_enterprise_invitation(
            organization_id=actor.organization_id,
            invited_by_user_id=actor.user_id,
            parent_user_id=effective_parent,
            role=invitation_role.value,
            token=token,
            expires_at=expires_at,
            telegram_username=telegram_username,
        )
        if not invitation:
            raise EnterpriseError("No se pudo crear la invitación en este momento", 500)
        return invitation

    def accept_invitation(self, token: str, accepting_user_id: int) -> dict[str, Any]:
        invitation = database.get_enterprise_invitation_by_token(token)
        if not invitation:
            raise EnterpriseError("Invitación no encontrada", 404)
        if invitation["status"] != "pending":
            raise EnterpriseError("Esta invitación ya no está disponible", 409)
        if self._is_expired(invitation):
            database.update_enterprise_invitation(int(invitation["id"]), status="expired")
            raise EnterpriseError("Esta invitación ha caducado", 410)

        existing_membership = database.get_enterprise_membership(accepting_user_id)
        if existing_membership and existing_membership.get("status") == "active":
            raise EnterpriseError("Ya perteneces a una organización Enterprise", 409)

        organization = self.get_organization(int(invitation["organization_id"]))
        if self.seats_used(organization["id"]) >= int(organization["seats_purchased"]):
            raise EnterpriseError("No hay licencias Enterprise disponibles.", 409)

        membership = database.create_enterprise_membership(
            organization_id=int(invitation["organization_id"]),
            user_id=accepting_user_id,
            parent_user_id=int(invitation["parent_user_id"]),
            role=invitation["role"],
        )
        if not membership:
            raise EnterpriseError("No se pudo aceptar la invitación en este momento", 500)

        database.update_enterprise_invitation(int(invitation["id"]), status="accepted", invited_user_id=accepting_user_id)
        return membership

    def _authorize_target(self, actor: Membership, target_user_id: int) -> dict[str, Any]:
        if actor.role == EnterpriseRole.EMPLOYEE:
            raise EnterpriseError("No tienes permisos para gestionar empleados", 403)
        visible_ids = {row["user_id"] for row in self.get_visible_members(actor)}
        if target_user_id == actor.user_id or target_user_id not in visible_ids:
            raise EnterpriseError("No tienes permisos sobre este miembro", 403)
        target = self._member_row(actor.organization_id, target_user_id)
        if not target:
            raise EnterpriseError("Miembro no encontrado", 404)
        if target["role"] == EnterpriseRole.OWNER.value:
            raise EnterpriseError("No se puede modificar al propietario de la organización", 422)
        return target

    def change_parent(self, actor_user_id: int, target_user_id: int, new_parent_user_id: int) -> None:
        actor = self.require_context(actor_user_id)
        self._authorize_target(actor, target_user_id)

        if new_parent_user_id == target_user_id:
            raise EnterpriseError("Un miembro no puede depender de sí mismo", 422)

        new_parent = self._member_row(actor.organization_id, new_parent_user_id)
        if not new_parent or new_parent.get("status") != "active":
            raise EnterpriseError("El nuevo responsable no pertenece a la organización", 422)

        visible_ids = {row["user_id"] for row in self.get_visible_members(actor)}
        if actor.role == EnterpriseRole.MANAGER and new_parent_user_id not in visible_ids:
            raise EnterpriseError("No puedes asignar responsables fuera de tu equipo", 403)

        descendants = self._descendant_ids(actor.organization_id, target_user_id)
        if new_parent_user_id in descendants:
            raise EnterpriseError("Esta reasignación crearía un ciclo en la jerarquía", 422)

        database.update_enterprise_membership(actor.organization_id, target_user_id, parent_user_id=new_parent_user_id)

    def deactivate_member(self, actor_user_id: int, target_user_id: int) -> None:
        actor = self.require_context(actor_user_id)
        self._authorize_target(actor, target_user_id)

        children = [
            row
            for row in self._active_members(actor.organization_id)
            if row.get("parent_user_id") == target_user_id
        ]
        if children:
            raise EnterpriseError(
                "Reasigna primero a sus empleados a otro responsable antes de eliminarlo",
                409,
            )

        database.update_enterprise_membership(actor.organization_id, target_user_id, status="deactivated")

    def get_stats(self, user_id: int, period_days: int = 30) -> dict[str, Any]:
        if period_days not in ALLOWED_STATS_PERIODS:
            raise EnterpriseError("El periodo debe ser 7, 30 o 90 días", 422)

        actor = self.require_context(user_id)
        visible = self.get_visible_members(actor)
        user_ids = [int(row["user_id"]) for row in visible]
        users_by_id = {int(row["id"]): row for row in database.list_users_by_ids(user_ids)}

        alerts = database.list_alerts_for_users(user_ids)
        feeds = database.list_feeds_for_users(user_ids)

        cutoff = datetime.utcnow() - timedelta(days=period_days)

        def _in_period(alert: dict[str, Any]) -> bool:
            detected_at = alert.get("detected_at")
            if not detected_at:
                return False
            try:
                return datetime.fromisoformat(str(detected_at).replace("Z", "+00:00")).replace(tzinfo=None) >= cutoff
            except ValueError:
                return False

        alerts_in_period = [alert for alert in alerts if _in_period(alert)]
        active_feeds = [feed for feed in feeds if feed.get("is_active")]

        feed_alert_counts: dict[int, int] = {}
        for alert in alerts:
            feed_id = alert.get("feed_id")
            if feed_id is not None:
                feed_alert_counts[feed_id] = feed_alert_counts.get(feed_id, 0) + 1
        feeds_by_id = {int(feed["id"]): feed for feed in feeds}
        top_feeds = sorted(feed_alert_counts.items(), key=lambda item: item[1], reverse=True)[:5]

        per_member = []
        for row in visible:
            member_user_id = int(row["user_id"])
            member_alerts = [a for a in alerts if a.get("user_id") == member_user_id]
            member_feeds = [f for f in feeds if f.get("user_id") == member_user_id]
            per_member.append(
                {
                    "user_id": member_user_id,
                    "username": users_by_id.get(member_user_id, {}).get("username", ""),
                    "role": row["role"],
                    "alerts_received": len(member_alerts),
                    "active_sources": len([f for f in member_feeds if f.get("is_active")]),
                }
            )

        return {
            "period_days": period_days,
            "has_data": bool(alerts or feeds),
            "total_alerts": len(alerts),
            "alerts_in_period": len(alerts_in_period),
            "active_sources": len(active_feeds),
            "total_sources": len(feeds),
            "top_sources": [
                {"url": feeds_by_id.get(feed_id, {}).get("url", "Fuente eliminada"), "alerts": count}
                for feed_id, count in top_feeds
            ],
            "members": per_member,
        }


_enterprise_service: Optional[EnterpriseService] = None


def get_enterprise_service() -> EnterpriseService:
    global _enterprise_service
    if _enterprise_service is None:
        _enterprise_service = EnterpriseService()
    return _enterprise_service
