from __future__ import annotations

from app import database


class _RaisingSupabase:
    def table(self, _name: str):
        raise RuntimeError("boom")


def test_enterprise_organization_crud(monkeypatch, fake_supabase):
    monkeypatch.setattr(database, "supabase", fake_supabase)
    fake_supabase.seed("users", [{"id": 1, "username": "owner", "is_active": True, "plan": "enterprise"}])

    organization = database.create_enterprise_organization(1, "Acme", seats_purchased=5)
    assert organization is not None
    assert organization["seats_purchased"] == 5

    fetched = database.get_enterprise_organization(organization["id"])
    assert fetched is not None
    assert fetched["name"] == "Acme"

    assert database.update_enterprise_organization(organization["id"], seats_purchased=8) is True
    assert database.get_enterprise_organization(organization["id"])["seats_purchased"] == 8

    membership = database.get_enterprise_membership(1)
    assert membership is not None
    assert membership["role"] == "OWNER"


def test_create_enterprise_organization_rejects_duplicate_owner(monkeypatch, fake_supabase):
    monkeypatch.setattr(database, "supabase", fake_supabase)
    fake_supabase.seed("users", [{"id": 1, "username": "owner", "is_active": True, "plan": "enterprise"}])

    first = database.create_enterprise_organization(1, "Acme", seats_purchased=5)
    second = database.create_enterprise_organization(1, "Acme 2", seats_purchased=5)

    assert first is not None
    assert second is None


def test_enterprise_members_crud(monkeypatch, fake_supabase):
    monkeypatch.setattr(database, "supabase", fake_supabase)
    fake_supabase.seed("users", [{"id": 1, "username": "owner"}, {"id": 2, "username": "emp"}])
    organization = database.create_enterprise_organization(1, "Acme", seats_purchased=5)

    membership = database.create_enterprise_membership(organization["id"], 2, 1, "EMPLOYEE")
    assert membership is not None

    members = database.list_enterprise_members(organization["id"])
    assert len(members) == 2

    assert database.update_enterprise_membership(organization["id"], 2, status="deactivated") is True
    assert database.get_enterprise_membership(2)["status"] == "deactivated"


def test_enterprise_invitations_crud(monkeypatch, fake_supabase):
    monkeypatch.setattr(database, "supabase", fake_supabase)
    fake_supabase.seed("users", [{"id": 1, "username": "owner"}])
    organization = database.create_enterprise_organization(1, "Acme", seats_purchased=5)

    invitation = database.create_enterprise_invitation(
        organization_id=organization["id"],
        invited_by_user_id=1,
        parent_user_id=1,
        role="EMPLOYEE",
        token="tok-123",
        expires_at="2030-01-01T00:00:00",
    )
    assert invitation is not None

    fetched = database.get_enterprise_invitation_by_token("tok-123")
    assert fetched is not None

    pending = database.list_pending_enterprise_invitations(organization["id"])
    assert len(pending) == 1

    assert database.update_enterprise_invitation(invitation["id"], status="accepted") is True
    assert database.get_enterprise_invitation_by_token("tok-123")["status"] == "accepted"


def test_list_helpers_filter_by_requested_users(monkeypatch, fake_supabase):
    monkeypatch.setattr(database, "supabase", fake_supabase)
    fake_supabase.seed("users", [{"id": 1, "username": "a"}, {"id": 2, "username": "b"}])
    fake_supabase.seed(
        "feeds",
        [
            {"id": 1, "user_id": 1, "url": "https://rss.local/1", "is_active": True},
            {"id": 2, "user_id": 2, "url": "https://rss.local/2", "is_active": True},
        ],
    )
    fake_supabase.seed(
        "alerts",
        [
            {"id": 1, "user_id": 1, "feed_id": 1, "post_title": "t1"},
            {"id": 2, "user_id": 2, "feed_id": 2, "post_title": "t2"},
        ],
    )

    assert [row["id"] for row in database.list_users_by_ids([1])] == [1]
    assert [row["id"] for row in database.list_feeds_for_users([1])] == [1]
    assert [row["id"] for row in database.list_alerts_for_users([1])] == [1]
    assert database.list_users_by_ids([]) == []
    assert database.list_feeds_for_users([]) == []
    assert database.list_alerts_for_users([]) == []


def test_enterprise_functions_handle_supabase_errors(monkeypatch):
    monkeypatch.setattr(database, "supabase", _RaisingSupabase())

    assert database.create_enterprise_organization(1, "Acme", 5) is None
    assert database.get_enterprise_organization(1) is None
    assert database.update_enterprise_organization(1, seats_purchased=2) is False
    assert database.create_enterprise_membership(1, 2, 1, "EMPLOYEE") is None
    assert database.get_enterprise_membership(2) is None
    assert database.list_enterprise_members(1) == []
    assert database.update_enterprise_membership(1, 2, status="deactivated") is False
    assert database.create_enterprise_invitation(1, 1, 1, "EMPLOYEE", "tok", "2030-01-01") is None
    assert database.get_enterprise_invitation_by_token("tok") is None
    assert database.list_pending_enterprise_invitations(1) == []
    assert database.update_enterprise_invitation(1, status="accepted") is False
    assert database.list_alerts_for_users([1]) == []
    assert database.list_feeds_for_users([1]) == []
    assert database.list_users_by_ids([1]) == []
