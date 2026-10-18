from __future__ import annotations

import pytest

from app import database
from app.services.enterprise_service import EnterpriseError, EnterpriseService


@pytest.fixture
def service(monkeypatch, fake_supabase) -> EnterpriseService:
    monkeypatch.setattr(database, "supabase", fake_supabase)
    return EnterpriseService()


def _seed_users(fake_supabase, ids: list[int]) -> None:
    fake_supabase.seed(
        "users",
        [{"id": i, "username": f"user{i}", "is_active": True, "plan": "enterprise"} for i in ids],
    )


def _build_org(fake_supabase, owner_id: int = 1, seats: int = 10) -> int:
    _seed_users(fake_supabase, [owner_id])
    organization = database.create_enterprise_organization(owner_id, "Acme", seats)
    assert organization is not None
    return int(organization["id"])


def _add_member(org_id: int, user_id: int, parent_id: int, role: str) -> None:
    membership = database.create_enterprise_membership(org_id, user_id, parent_id, role)
    assert membership is not None


# ---- context / visibility ----


def test_get_context_returns_none_when_not_a_member(service):
    assert service.get_context(999) is None


def test_require_context_raises_when_not_a_member(service):
    with pytest.raises(EnterpriseError) as exc:
        service.require_context(999)
    assert exc.value.status_code == 403


def test_owner_sees_entire_organization(service, fake_supabase):
    org_id = _build_org(fake_supabase, owner_id=1, seats=10)
    _seed_users(fake_supabase, [1, 2, 3, 4, 5])
    _add_member(org_id, 2, 1, "MANAGER")
    _add_member(org_id, 3, 2, "EMPLOYEE")
    _add_member(org_id, 4, 1, "MANAGER")
    _add_member(org_id, 5, 4, "EMPLOYEE")

    owner_ctx = service.require_context(1)
    visible_ids = {row["user_id"] for row in service.get_visible_members(owner_ctx)}
    assert visible_ids == {1, 2, 3, 4, 5}


def test_manager_sees_only_own_branch(service, fake_supabase):
    org_id = _build_org(fake_supabase, owner_id=1, seats=10)
    _seed_users(fake_supabase, [1, 2, 3, 4, 5])
    _add_member(org_id, 2, 1, "MANAGER")
    _add_member(org_id, 3, 2, "EMPLOYEE")
    _add_member(org_id, 4, 1, "MANAGER")
    _add_member(org_id, 5, 4, "EMPLOYEE")

    manager_ctx = service.require_context(2)
    visible_ids = {row["user_id"] for row in service.get_visible_members(manager_ctx)}
    assert visible_ids == {2, 3}
    assert 1 not in visible_ids
    assert 4 not in visible_ids
    assert 5 not in visible_ids


def test_employee_only_sees_self(service, fake_supabase):
    org_id = _build_org(fake_supabase, owner_id=1, seats=10)
    _seed_users(fake_supabase, [1, 2, 3])
    _add_member(org_id, 2, 1, "MANAGER")
    _add_member(org_id, 3, 2, "EMPLOYEE")

    employee_ctx = service.require_context(3)
    visible_ids = {row["user_id"] for row in service.get_visible_members(employee_ctx)}
    assert visible_ids == {3}


def test_deactivated_member_loses_context(service, fake_supabase):
    org_id = _build_org(fake_supabase, owner_id=1, seats=10)
    _seed_users(fake_supabase, [1, 2])
    _add_member(org_id, 2, 1, "EMPLOYEE")
    database.update_enterprise_membership(org_id, 2, status="deactivated")

    assert service.get_context(2) is None


def test_two_organizations_never_share_visibility(service, fake_supabase):
    org_a = _build_org(fake_supabase, owner_id=1, seats=5)
    _seed_users(fake_supabase, [1, 2, 10, 20])
    database.create_enterprise_organization(10, "Other Co", 5)
    _add_member(org_a, 2, 1, "EMPLOYEE")
    other_org = database.get_enterprise_membership(10)["organization_id"]
    _add_member(other_org, 20, 10, "EMPLOYEE")

    owner_a_ctx = service.require_context(1)
    visible_ids = {row["user_id"] for row in service.get_visible_members(owner_a_ctx)}
    assert 20 not in visible_ids
    assert 10 not in visible_ids


# ---- licenses ----


def test_seats_used_and_available(service, fake_supabase):
    org_id = _build_org(fake_supabase, owner_id=1, seats=3)
    _seed_users(fake_supabase, [1, 2])
    _add_member(org_id, 2, 1, "EMPLOYEE")

    organization = service.get_organization(org_id)
    assert service.seats_used(org_id) == 2
    assert service.seats_available(organization) == 1


def test_create_invitation_fails_without_available_seats(service, fake_supabase):
    org_id = _build_org(fake_supabase, owner_id=1, seats=1)

    with pytest.raises(EnterpriseError) as exc:
        service.create_invitation(actor_user_id=1, role="EMPLOYEE")
    assert exc.value.status_code == 409


# ---- invitations ----


def test_employee_cannot_invite(service, fake_supabase):
    org_id = _build_org(fake_supabase, owner_id=1, seats=10)
    _seed_users(fake_supabase, [1, 2])
    _add_member(org_id, 2, 1, "EMPLOYEE")

    with pytest.raises(EnterpriseError) as exc:
        service.create_invitation(actor_user_id=2, role="EMPLOYEE")
    assert exc.value.status_code == 403


def test_manager_cannot_invite_outside_own_branch(service, fake_supabase):
    org_id = _build_org(fake_supabase, owner_id=1, seats=10)
    _seed_users(fake_supabase, [1, 2, 3])
    _add_member(org_id, 2, 1, "MANAGER")
    _add_member(org_id, 3, 1, "MANAGER")

    with pytest.raises(EnterpriseError) as exc:
        service.create_invitation(actor_user_id=2, role="EMPLOYEE", parent_user_id=3)
    assert exc.value.status_code == 403


def test_owner_can_invite_under_any_manager(service, fake_supabase):
    org_id = _build_org(fake_supabase, owner_id=1, seats=10)
    _seed_users(fake_supabase, [1, 2])
    _add_member(org_id, 2, 1, "MANAGER")

    invitation = service.create_invitation(actor_user_id=1, role="EMPLOYEE", parent_user_id=2)
    assert invitation["parent_user_id"] == 2
    assert invitation["status"] == "pending"


def test_create_invitation_rejects_invalid_role(service, fake_supabase):
    _build_org(fake_supabase, owner_id=1, seats=10)

    with pytest.raises(EnterpriseError) as exc:
        service.create_invitation(actor_user_id=1, role="CEO")
    assert exc.value.status_code == 422


def test_create_invitation_rejects_owner_role(service, fake_supabase):
    _build_org(fake_supabase, owner_id=1, seats=10)

    with pytest.raises(EnterpriseError) as exc:
        service.create_invitation(actor_user_id=1, role="OWNER")
    assert exc.value.status_code == 422


def test_accept_invitation_creates_membership(service, fake_supabase):
    org_id = _build_org(fake_supabase, owner_id=1, seats=10)
    _seed_users(fake_supabase, [1, 2])
    invitation = service.create_invitation(actor_user_id=1, role="EMPLOYEE")

    membership = service.accept_invitation(invitation["token"], accepting_user_id=2)

    assert membership["user_id"] == 2
    assert membership["parent_user_id"] == 1
    stored_invitation = database.get_enterprise_invitation_by_token(invitation["token"])
    assert stored_invitation["status"] == "accepted"
    assert stored_invitation["invited_user_id"] == 2


def test_accept_invitation_rejects_unknown_token(service):
    with pytest.raises(EnterpriseError) as exc:
        service.accept_invitation("unknown-token", accepting_user_id=2)
    assert exc.value.status_code == 404


def test_accept_invitation_rejects_already_accepted(service, fake_supabase):
    _build_org(fake_supabase, owner_id=1, seats=10)
    _seed_users(fake_supabase, [1, 2, 3])
    invitation = service.create_invitation(actor_user_id=1, role="EMPLOYEE")
    service.accept_invitation(invitation["token"], accepting_user_id=2)

    with pytest.raises(EnterpriseError) as exc:
        service.accept_invitation(invitation["token"], accepting_user_id=3)
    assert exc.value.status_code == 409


def test_accept_invitation_rejects_user_already_in_another_org(service, fake_supabase):
    org_id = _build_org(fake_supabase, owner_id=1, seats=10)
    _seed_users(fake_supabase, [1, 2, 10])
    database.create_enterprise_organization(10, "Other Co", 5)
    _add_member(org_id, 2, 1, "EMPLOYEE")
    invitation = service.create_invitation(actor_user_id=1, role="EMPLOYEE")

    with pytest.raises(EnterpriseError) as exc:
        service.accept_invitation(invitation["token"], accepting_user_id=2)
    assert exc.value.status_code == 409


def test_accept_invitation_rejects_when_expired(service, fake_supabase):
    _build_org(fake_supabase, owner_id=1, seats=10)
    _seed_users(fake_supabase, [1, 2])
    invitation = service.create_invitation(actor_user_id=1, role="EMPLOYEE")
    database.update_enterprise_invitation(invitation["id"], expires_at="2000-01-01T00:00:00")

    with pytest.raises(EnterpriseError) as exc:
        service.accept_invitation(invitation["token"], accepting_user_id=2)
    assert exc.value.status_code == 410


# ---- hierarchy mutations ----


def test_change_parent_moves_employee_between_managers(service, fake_supabase):
    org_id = _build_org(fake_supabase, owner_id=1, seats=10)
    _seed_users(fake_supabase, [1, 2, 3, 4])
    _add_member(org_id, 2, 1, "MANAGER")
    _add_member(org_id, 3, 1, "MANAGER")
    _add_member(org_id, 4, 2, "EMPLOYEE")

    service.change_parent(actor_user_id=1, target_user_id=4, new_parent_user_id=3)

    updated = database.get_enterprise_membership(4)
    assert updated["parent_user_id"] == 3


def test_change_parent_rejects_cycles(service, fake_supabase):
    org_id = _build_org(fake_supabase, owner_id=1, seats=10)
    _seed_users(fake_supabase, [1, 2, 3])
    _add_member(org_id, 2, 1, "MANAGER")
    _add_member(org_id, 3, 2, "EMPLOYEE")

    with pytest.raises(EnterpriseError) as exc:
        service.change_parent(actor_user_id=1, target_user_id=2, new_parent_user_id=3)
    assert exc.value.status_code == 422


def test_change_parent_rejects_outside_manager_scope(service, fake_supabase):
    org_id = _build_org(fake_supabase, owner_id=1, seats=10)
    _seed_users(fake_supabase, [1, 2, 3, 4])
    _add_member(org_id, 2, 1, "MANAGER")
    _add_member(org_id, 3, 1, "MANAGER")
    _add_member(org_id, 4, 2, "EMPLOYEE")

    with pytest.raises(EnterpriseError) as exc:
        service.change_parent(actor_user_id=2, target_user_id=4, new_parent_user_id=3)
    assert exc.value.status_code == 403


def test_change_parent_cannot_target_owner(service, fake_supabase):
    org_id = _build_org(fake_supabase, owner_id=1, seats=10)
    _seed_users(fake_supabase, [1, 2])
    _add_member(org_id, 2, 1, "MANAGER")

    with pytest.raises(EnterpriseError) as exc:
        service.change_parent(actor_user_id=2, target_user_id=1, new_parent_user_id=2)
    assert exc.value.status_code == 403


def test_deactivate_member_frees_a_seat(service, fake_supabase):
    org_id = _build_org(fake_supabase, owner_id=1, seats=2)
    _seed_users(fake_supabase, [1, 2])
    _add_member(org_id, 2, 1, "EMPLOYEE")
    organization = service.get_organization(org_id)
    assert service.seats_available(organization) == 0

    service.deactivate_member(actor_user_id=1, target_user_id=2)

    assert service.seats_available(organization) == 1
    assert database.get_enterprise_membership(2)["status"] == "deactivated"


def test_deactivate_member_blocked_when_has_active_reports(service, fake_supabase):
    org_id = _build_org(fake_supabase, owner_id=1, seats=10)
    _seed_users(fake_supabase, [1, 2, 3])
    _add_member(org_id, 2, 1, "MANAGER")
    _add_member(org_id, 3, 2, "EMPLOYEE")

    with pytest.raises(EnterpriseError) as exc:
        service.deactivate_member(actor_user_id=1, target_user_id=2)
    assert exc.value.status_code == 409


def test_employee_cannot_deactivate_anyone(service, fake_supabase):
    org_id = _build_org(fake_supabase, owner_id=1, seats=10)
    _seed_users(fake_supabase, [1, 2, 3])
    _add_member(org_id, 2, 1, "EMPLOYEE")
    _add_member(org_id, 3, 1, "EMPLOYEE")

    with pytest.raises(EnterpriseError) as exc:
        service.deactivate_member(actor_user_id=2, target_user_id=3)
    assert exc.value.status_code == 403


# ---- stats ----


def test_get_stats_rejects_invalid_period(service, fake_supabase):
    _build_org(fake_supabase, owner_id=1, seats=10)

    with pytest.raises(EnterpriseError) as exc:
        service.get_stats(1, period_days=15)
    assert exc.value.status_code == 422


def test_get_stats_scopes_to_visible_members_only(service, fake_supabase):
    org_id = _build_org(fake_supabase, owner_id=1, seats=10)
    _seed_users(fake_supabase, [1, 2, 3, 4])
    _add_member(org_id, 2, 1, "MANAGER")
    _add_member(org_id, 3, 2, "EMPLOYEE")
    _add_member(org_id, 4, 1, "MANAGER")

    fake_supabase.seed(
        "feeds",
        [
            {"id": 1, "user_id": 3, "url": "https://rss.local/a.xml", "is_active": True},
            {"id": 2, "user_id": 4, "url": "https://rss.local/b.xml", "is_active": True},
        ],
    )
    fake_supabase.seed(
        "alerts",
        [
            {"id": 1, "user_id": 3, "feed_id": 1, "post_title": "t1", "detected_at": "2026-09-29T10:00:00"},
            {"id": 2, "user_id": 4, "feed_id": 2, "post_title": "t2", "detected_at": "2026-09-29T10:00:00"},
        ],
    )

    manager_stats = service.get_stats(2, period_days=30)
    assert manager_stats["total_alerts"] == 1
    assert manager_stats["active_sources"] == 1
    assert {member["user_id"] for member in manager_stats["members"]} == {2, 3}


def test_get_stats_reports_no_data_when_empty(service, fake_supabase):
    _build_org(fake_supabase, owner_id=1, seats=10)

    stats = service.get_stats(1, period_days=7)
    assert stats["has_data"] is False
    assert stats["total_alerts"] == 0
