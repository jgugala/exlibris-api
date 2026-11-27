from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from exlibris.models import User
from exlibris.services.security import verify_password


def user_data(**overrides: Any) -> dict[str, Any]:
    return {"email": "ann@example.com", "password": "correct horse"} | overrides


# POST /auth/register


def test_register_returns_201_with_public_fields(client: TestClient) -> None:
    response = client.post("/auth/register", json=user_data())

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"id", "email", "is_admin", "created_at"}
    assert isinstance(body["id"], int)
    assert body["email"] == "ann@example.com"
    assert body["is_admin"] is False


def test_register_stores_email_lowercase(client: TestClient) -> None:
    response = client.post("/auth/register", json=user_data(email="Ann@Example.COM"))

    assert response.json()["email"] == "ann@example.com"


def test_register_duplicate_email_different_case_returns_409(client: TestClient) -> None:
    client.post("/auth/register", json=user_data(email="Ann@Example.com"))

    response = client.post("/auth/register", json=user_data(email="ann@example.com"))

    assert response.status_code == 409
    assert response.json() == {"detail": "Email already registered"}


def test_register_after_duplicate_still_works(client: TestClient) -> None:
    client.post("/auth/register", json=user_data())
    client.post("/auth/register", json=user_data())

    response = client.post("/auth/register", json=user_data(email="bob@example.com"))

    assert response.status_code == 201


@pytest.mark.parametrize(
    "overrides",
    [
        pytest.param({"password": "x" * 7}, id="password-too-short"),
        pytest.param({"password": "x" * 129}, id="password-too-long"),
        pytest.param({"email": "not-an-email"}, id="invalid-email"),
        pytest.param({"is_admin": True}, id="extra-field-is-admin"),
    ],
)
def test_register_invalid_body_returns_422(client: TestClient, overrides: dict[str, Any]) -> None:
    response = client.post("/auth/register", json=user_data(**overrides))

    assert response.status_code == 422


@pytest.mark.parametrize("length", [8, 128])
def test_register_password_length_bounds_accepted(client: TestClient, length: int) -> None:
    response = client.post("/auth/register", json=user_data(password="x" * length))

    assert response.status_code == 201


def test_register_stores_verifiable_hash_not_plain_password(
    client: TestClient, db_session: Session
) -> None:
    client.post("/auth/register", json=user_data())

    user = db_session.scalars(select(User)).one()

    assert user.password_hash != "correct horse"
    assert verify_password("correct horse", user.password_hash)
