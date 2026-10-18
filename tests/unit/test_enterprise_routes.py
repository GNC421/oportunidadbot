from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import database
from app.config import settings
from app.web.enterprise_routes import router


@pytest.fixture(autouse=True)
def _patch_database(monkeypatch, fake_supabase):
    # Runs before every test body so helper seed functions can call database.* directly.
    monkeypatch.setattr(database, "supabase", fake_supabase)
    monkeypatch.setattr(settings, "WEB_SESSION_SECRET", "test-web-session-secret")
    monkeypatch.setattr(settings, "WEB_SESSION_COOKIE_SECURE", False)


def _client(monkeypatch, fake_supabase) -> TestClient:
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def _login(client: TestClient, user_id: int) -> None:
    from app.web.auth import create_session_token
    from app.web.routes import SESSION_COOKIE_NAME

    client.cookies.set(SESSION_COOKIE_NAME, create_session_token(user_id))


def _seed_user(fake_supabase, user_id: int, plan: str = "enterprise", username: str | None = None) -> None:
    fake_supabase.seed(
        "users",
        fake_supabase.users + [{"id": user_id, "username": username or f"user{user_id}", "is_active": True, "plan": plan}],
    )


def _seed_full_hierarchy(fake_supabase) -> int:
    """OWNER(1) -> MANAGER_A(2) -> EMPLOYEE_A1(3), EMPLOYEE_A2(4); OWNER(1) -> MANAGER_B(5) -> EMPLOYEE_B1(6), EMPLOYEE_B2(7)."""
    for uid in [1, 2, 3, 4, 5, 6, 7]:
        _seed_user(fake_supabase, uid)
    organization = database.create_enterprise_organization(1, "Acme", seats_purchased=10)
    org_id = organization["id"]
    database.create_enterprise_membership(org_id, 2, 1, "MANAGER")
    database.create_enterprise_membership(org_id, 3, 2, "EMPLOYEE")
    database.create_enterprise_membership(org_id, 4, 2, "EMPLOYEE")
    database.create_enterprise_membership(org_id, 5, 1, "MANAGER")
    database.create_enterprise_membership(org_id, 6, 5, "EMPLOYEE")
    database.create_enterprise_membership(org_id, 7, 5, "EMPLOYEE")
    return org_id


def test_tree_requires_authentication(monkeypatch, fake_supabase):
    client = _client(monkeypatch, fake_supabase)
    assert client.get("/api/web/enterprise/tree").status_code == 401


def test_professional_user_without_membership_is_rejected(monkeypatch, fake_supabase):
    _seed_user(fake_supabase, 101, plan="professional")
    client = _client(monkeypatch, fake_supabase)
    _login(client, 101)

    assert client.get("/api/web/enterprise/tree").status_code == 403
    assert client.get("/api/web/enterprise/organization").status_code == 403
    assert client.get("/api/web/enterprise/stats").status_code == 403


def test_starter_user_without_membership_is_rejected(monkeypatch, fake_supabase):
    _seed_user(fake_supabase, 101, plan="starter")
    client = _client(monkeypatch, fake_supabase)
    _login(client, 101)

    assert client.get("/api/web/enterprise/tree").status_code == 403


def test_owner_sees_entire_organization_tree(monkeypatch, fake_supabase):
    _seed_full_hierarchy(fake_supabase)
    client = _client(monkeypatch, fake_supabase)
    _login(client, 1)

    response = client.get("/api/web/enterprise/tree")

    assert response.status_code == 200
    visible_ids = {member["user_id"] for member in response.json()["members"]}
    assert visible_ids == {1, 2, 3, 4, 5, 6, 7}
    assert response.json()["viewer_role"] == "OWNER"


def test_manager_a_sees_only_own_branch(monkeypatch, fake_supabase):
    _seed_full_hierarchy(fake_supabase)
    client = _client(monkeypatch, fake_supabase)
    _login(client, 2)

    response = client.get("/api/web/enterprise/tree")

    assert response.status_code == 200
    visible_ids = {member["user_id"] for member in response.json()["members"]}
    assert visible_ids == {2, 3, 4}
    assert 1 not in visible_ids
    assert 5 not in visible_ids
    assert 6 not in visible_ids
    assert 7 not in visible_ids


def test_employee_a1_sees_only_self(monkeypatch, fake_supabase):
    _seed_full_hierarchy(fake_supabase)
    client = _client(monkeypatch, fake_supabase)
    _login(client, 3)

    response = client.get("/api/web/enterprise/tree")

    assert response.status_code == 200
    visible_ids = {member["user_id"] for member in response.json()["members"]}
    assert visible_ids == {3}


def test_organization_endpoint_reports_license_usage(monkeypatch, fake_supabase):
    _seed_full_hierarchy(fake_supabase)
    client = _client(monkeypatch, fake_supabase)
    _login(client, 1)

    response = client.get("/api/web/enterprise/organization")

    assert response.status_code == 200
    body = response.json()
    assert body["seats_purchased"] == 10
    assert body["seats_used"] == 7
    assert body["seats_available"] == 3


def test_owner_can_invite_employee_and_employee_can_accept(monkeypatch, fake_supabase):
    _seed_full_hierarchy(fake_supabase)
    _seed_user(fake_supabase, 8, plan="starter")
    client = _client(monkeypatch, fake_supabase)
    _login(client, 1)

    invite_response = client.post(
        "/api/web/enterprise/invitations",
        json={"role": "EMPLOYEE", "parent_user_id": 2, "telegram_username": "user8"},
    )
    assert invite_response.status_code == 201
    token = invite_response.json()["token"]

    accept_client = _client(monkeypatch, fake_supabase)
    _login(accept_client, 8)
    accept_response = accept_client.post("/api/web/enterprise/invitations/accept", json={"token": token})

    assert accept_response.status_code == 200
    assert accept_response.json()["parent_user_id"] == 2


def test_employee_cannot_create_invitation(monkeypatch, fake_supabase):
    _seed_full_hierarchy(fake_supabase)
    client = _client(monkeypatch, fake_supabase)
    _login(client, 3)

    response = client.post("/api/web/enterprise/invitations", json={"role": "EMPLOYEE"})

    assert response.status_code == 403


def test_manager_cannot_invite_under_other_branch(monkeypatch, fake_supabase):
    _seed_full_hierarchy(fake_supabase)
    client = _client(monkeypatch, fake_supabase)
    _login(client, 2)

    response = client.post("/api/web/enterprise/invitations", json={"role": "EMPLOYEE", "parent_user_id": 5})

    assert response.status_code == 403


def test_invitation_blocked_without_available_seats(monkeypatch, fake_supabase):
    for uid in [1, 2]:
        _seed_user(fake_supabase, uid)
    database.create_enterprise_organization(1, "Acme", seats_purchased=1)
    client = _client(monkeypatch, fake_supabase)
    _login(client, 1)

    response = client.post("/api/web/enterprise/invitations", json={"role": "EMPLOYEE"})

    assert response.status_code == 409
    assert response.json()["detail"] == "No hay licencias Enterprise disponibles."


def test_owner_can_reassign_employee_between_managers(monkeypatch, fake_supabase):
    _seed_full_hierarchy(fake_supabase)
    client = _client(monkeypatch, fake_supabase)
    _login(client, 1)

    response = client.patch("/api/web/enterprise/members/3", json={"parent_user_id": 5})

    assert response.status_code == 204
    assert database.get_enterprise_membership(3)["parent_user_id"] == 5


def test_reassign_rejects_cycles(monkeypatch, fake_supabase):
    _seed_full_hierarchy(fake_supabase)
    client = _client(monkeypatch, fake_supabase)
    _login(client, 1)

    response = client.patch("/api/web/enterprise/members/2", json={"parent_user_id": 3})

    assert response.status_code == 422


def test_manager_cannot_reassign_outside_own_branch(monkeypatch, fake_supabase):
    _seed_full_hierarchy(fake_supabase)
    client = _client(monkeypatch, fake_supabase)
    _login(client, 2)

    response = client.patch("/api/web/enterprise/members/6", json={"parent_user_id": 3})

    assert response.status_code == 403


def test_owner_can_deactivate_leaf_employee(monkeypatch, fake_supabase):
    _seed_full_hierarchy(fake_supabase)
    client = _client(monkeypatch, fake_supabase)
    _login(client, 1)

    response = client.delete("/api/web/enterprise/members/3")

    assert response.status_code == 204
    assert database.get_enterprise_membership(3)["status"] == "deactivated"


def test_cannot_deactivate_manager_with_active_reports(monkeypatch, fake_supabase):
    _seed_full_hierarchy(fake_supabase)
    client = _client(monkeypatch, fake_supabase)
    _login(client, 1)

    response = client.delete("/api/web/enterprise/members/2")

    assert response.status_code == 409


def test_stats_scopes_to_visible_branch(monkeypatch, fake_supabase):
    _seed_full_hierarchy(fake_supabase)
    fake_supabase.seed(
        "feeds",
        [
            {"id": 1, "user_id": 3, "url": "https://rss.local/a.xml", "is_active": True},
            {"id": 2, "user_id": 6, "url": "https://rss.local/b.xml", "is_active": True},
        ],
    )
    client = _client(monkeypatch, fake_supabase)
    _login(client, 2)

    response = client.get("/api/web/enterprise/stats", params={"period_days": 30})

    assert response.status_code == 200
    body = response.json()
    assert body["active_sources"] == 1
    assert body["has_data"] is True


def test_stats_rejects_invalid_period(monkeypatch, fake_supabase):
    _seed_full_hierarchy(fake_supabase)
    client = _client(monkeypatch, fake_supabase)
    _login(client, 1)

    response = client.get("/api/web/enterprise/stats", params={"period_days": 5})

    assert response.status_code == 422
