from __future__ import annotations

import pytest


class UserBuilder:
    def __init__(self) -> None:
        self._id = 101
        self._username = "test_user"
        self._first_name = "Tester"

    def with_id(self, user_id: int) -> "UserBuilder":
        self._id = user_id
        return self

    def with_username(self, username: str) -> "UserBuilder":
        self._username = username
        return self

    def build(self) -> dict:
        return {
            "id": self._id,
            "username": self._username,
            "first_name": self._first_name,
            "is_active": True,
        }


@pytest.fixture
def user_builder() -> UserBuilder:
    return UserBuilder()


@pytest.fixture
def sample_user(user_builder: UserBuilder) -> dict:
    return user_builder.build()
