from __future__ import annotations

from dataclasses import dataclass
from copy import deepcopy
from typing import Any


@dataclass
class FakeResult:
    data: list[dict[str, Any]]
    count: int | None = None


class FakeTableQuery:
    def __init__(self, db: "FakeSupabase", table_name: str) -> None:
        self._db = db
        self._table_name = table_name
        self._op = "select"
        self._payload: dict[str, Any] | None = None
        self._filters: list[tuple[str, Any]] = []
        self._limit: int | None = None
        self._count_mode: str | None = None

    def select(self, _fields: str = "*", count: str | None = None) -> "FakeTableQuery":
        self._op = "select"
        self._count_mode = count
        return self

    def insert(self, payload: dict[str, Any]) -> "FakeTableQuery":
        self._op = "insert"
        self._payload = payload
        return self

    def update(self, payload: dict[str, Any]) -> "FakeTableQuery":
        self._op = "update"
        self._payload = payload
        return self

    def delete(self) -> "FakeTableQuery":
        self._op = "delete"
        return self

    def eq(self, key: str, value: Any) -> "FakeTableQuery":
        self._filters.append((key, value))
        return self

    def limit(self, value: int) -> "FakeTableQuery":
        self._limit = value
        return self

    def execute(self) -> FakeResult:
        table = self._db._storage[self._table_name]

        def matches(row: dict[str, Any]) -> bool:
            return all(row.get(key) == value for key, value in self._filters)

        if self._op == "insert":
            payload = deepcopy(self._payload or {})
            if "id" not in payload:
                payload["id"] = self._db.next_id(self._table_name)
            table.append(payload)
            return FakeResult([deepcopy(payload)])

        matched = [row for row in table if matches(row)]

        if self._op == "select":
            result = matched
            if self._limit is not None:
                result = result[: self._limit]
            count = len(matched) if self._count_mode == "exact" else None
            return FakeResult(deepcopy(result), count=count)

        if self._op == "update":
            updated: list[dict[str, Any]] = []
            for row in matched:
                row.update(deepcopy(self._payload or {}))
                updated.append(deepcopy(row))
            return FakeResult(updated)

        if self._op == "delete":
            deleted = [deepcopy(row) for row in matched]
            self._db._storage[self._table_name] = [row for row in table if not matches(row)]
            return FakeResult(deleted)

        return FakeResult([])


class FakeSupabase:
    def __init__(self) -> None:
        self._storage: dict[str, list[dict[str, Any]]] = {
            "users": [],
            "feeds": [],
            "alerts": [],
        }
        self._ids: dict[str, int] = {
            "users": 1,
            "feeds": 1,
            "alerts": 1,
        }

    @property
    def users(self) -> list[dict[str, Any]]:
        return self._storage["users"]

    @property
    def feeds(self) -> list[dict[str, Any]]:
        return self._storage["feeds"]

    @property
    def alerts(self) -> list[dict[str, Any]]:
        return self._storage["alerts"]

    def seed(self, table_name: str, rows: list[dict[str, Any]]) -> None:
        self._storage[table_name] = [deepcopy(row) for row in rows]
        if rows:
            self._ids[table_name] = max(int(row.get("id", 0)) for row in rows) + 1

    def next_id(self, table_name: str) -> int:
        next_value = self._ids[table_name]
        self._ids[table_name] += 1
        return next_value

    def table(self, table_name: str) -> FakeTableQuery:
        return FakeTableQuery(self, table_name)
