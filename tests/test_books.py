from typing import Any

import pytest
from fastapi.testclient import TestClient


def book_data(**overrides: Any) -> dict[str, Any]:
    return {
        "isbn": "9780306406157",
        "title": "Effective Java",
        "author": "Joshua Bloch",
    } | overrides


# POST /books


def test_create_book_returns_201_with_id_and_sent_fields(client: TestClient) -> None:
    payload = book_data(pages=412, status="reading", rating=5, review="Great.")

    response = client.post("/books", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert isinstance(body["id"], int)
    assert body.items() >= payload.items()
    assert "created_at" in body


def test_create_book_minimal_applies_defaults(client: TestClient) -> None:
    response = client.post("/books", json=book_data())

    body = response.json()
    assert body["status"] == "want_to_read"
    assert (body["pages"], body["rating"], body["review"]) == (None, None, None)


def test_create_book_is_persisted(client: TestClient) -> None:
    book_id = client.post("/books", json=book_data()).json()["id"]

    response = client.get(f"/books/{book_id}")

    assert response.status_code == 200
    assert response.json()["isbn"] == "9780306406157"


def test_create_book_duplicate_isbn_returns_409(client: TestClient) -> None:
    client.post("/books", json=book_data())

    response = client.post("/books", json=book_data(title="Another title"))

    assert response.status_code == 409
    assert response.json() == {"detail": "Book with ISBN 9780306406157 already exists"}


def test_create_book_after_duplicate_still_works(client: TestClient) -> None:
    client.post("/books", json=book_data())
    client.post("/books", json=book_data())

    response = client.post("/books", json=book_data(isbn="0306406152"))

    assert response.status_code == 201
    assert len(client.get("/books").json()) == 2


@pytest.mark.parametrize(
    "overrides",
    [{"rating": 7}, {"isbn": "123"}, {"title": ""}, {"status": "finished"}, {"id": 1}],
)
def test_create_book_invalid_body_returns_422(
    client: TestClient, overrides: dict[str, Any]
) -> None:
    response = client.post("/books", json=book_data(**overrides))

    assert response.status_code == 422


def test_create_book_missing_body_returns_422(client: TestClient) -> None:
    response = client.post("/books")

    assert response.status_code == 422


# GET /books


def test_list_books_empty_returns_empty_list(client: TestClient) -> None:
    response = client.get("/books")

    assert response.status_code == 200
    assert response.json() == []


def test_list_books_returns_all_ordered_by_id(client: TestClient) -> None:
    # On SQLite the id is the rowid, so a table scan returns id order even without
    # ORDER BY; this test documents the contract, the order_by matters for PostgreSQL.
    first = client.post("/books", json=book_data(isbn="0306406152")).json()
    second = client.post("/books", json=book_data(isbn="9780306406157")).json()

    response = client.get("/books")

    assert response.status_code == 200
    assert [book["id"] for book in response.json()] == [first["id"], second["id"]]


def test_list_books_filters_by_status(client: TestClient) -> None:
    client.post("/books", json=book_data(isbn="0306406152", status="reading"))
    client.post("/books", json=book_data(isbn="9780306406157", status="read"))

    response = client.get("/books", params={"status": "reading"})

    assert response.status_code == 200
    books = response.json()
    assert [book["isbn"] for book in books] == ["0306406152"]


def test_list_books_status_without_matches_returns_empty_list(client: TestClient) -> None:
    client.post("/books", json=book_data(status="reading"))

    response = client.get("/books", params={"status": "read"})

    assert response.json() == []


def test_list_books_unknown_status_returns_422(client: TestClient) -> None:
    response = client.get("/books", params={"status": "foo"})

    assert response.status_code == 422


# GET /books/{book_id}


def test_get_book_returns_book(client: TestClient) -> None:
    created = client.post("/books", json=book_data()).json()

    response = client.get(f"/books/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_get_book_missing_returns_404(client: TestClient) -> None:
    response = client.get("/books/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Book not found"}


def test_get_book_non_integer_id_returns_422(client: TestClient) -> None:
    response = client.get("/books/abc")

    assert response.status_code == 422


@pytest.mark.parametrize("book_id", [0, -(2**63) - 1, 2**63])
def test_get_book_id_out_of_range_returns_422(client: TestClient, book_id: int) -> None:
    response = client.get(f"/books/{book_id}")

    assert response.status_code == 422


# PATCH /books/{book_id}


def test_update_book_changes_sent_field_and_keeps_others(client: TestClient) -> None:
    created = client.post("/books", json=book_data(pages=412, review="Great.")).json()

    response = client.patch(f"/books/{created['id']}", json={"rating": 4})

    assert response.status_code == 200
    assert response.json() == created | {"rating": 4}


def test_update_book_is_persisted(client: TestClient) -> None:
    book_id = client.post("/books", json=book_data()).json()["id"]
    patched = client.patch(f"/books/{book_id}", json={"status": "read", "title": "New title"})
    assert patched.status_code == 200

    response = client.get(f"/books/{book_id}")

    body = response.json()
    assert (body["status"], body["title"]) == ("read", "New title")


@pytest.mark.parametrize("field", ["pages", "rating", "review"])
def test_update_book_null_clears_nullable_field(client: TestClient, field: str) -> None:
    payload = book_data(pages=412, rating=5, review="Great.")
    book_id = client.post("/books", json=payload).json()["id"]

    response = client.patch(f"/books/{book_id}", json={field: None})

    assert response.status_code == 200
    assert response.json()[field] is None
    assert client.get(f"/books/{book_id}").json()[field] is None


def test_update_book_empty_body_leaves_book_unchanged(client: TestClient) -> None:
    created = client.post("/books", json=book_data(rating=3)).json()

    response = client.patch(f"/books/{created['id']}", json={})

    assert response.status_code == 200
    assert response.json() == created


@pytest.mark.parametrize(
    "payload",
    [
        {"title": None},
        {"title": "   "},
        {"author": None},
        {"review": " "},
        {"status": None},
        {"rating": 0},
        {"isbn": "0306406152"},
    ],
)
def test_update_book_invalid_body_returns_422(client: TestClient, payload: dict[str, Any]) -> None:
    created = client.post("/books", json=book_data()).json()

    response = client.patch(f"/books/{created['id']}", json=payload)

    assert response.status_code == 422
    assert client.get(f"/books/{created['id']}").json() == created


def test_update_book_strips_whitespace(client: TestClient) -> None:
    book_id = client.post("/books", json=book_data()).json()["id"]

    response = client.patch(f"/books/{book_id}", json={"title": "  New title  "})

    assert response.json()["title"] == "New title"


def test_update_book_missing_returns_404(client: TestClient) -> None:
    response = client.patch("/books/999", json={"rating": 4})

    assert response.status_code == 404
    assert response.json() == {"detail": "Book not found"}


@pytest.mark.parametrize("book_id", [0, -(2**63) - 1, 2**63])
def test_update_book_id_out_of_range_returns_422(client: TestClient, book_id: int) -> None:
    response = client.patch(f"/books/{book_id}", json={"rating": 4})

    assert response.status_code == 422


# DELETE /books/{book_id}


def test_delete_book_returns_204_without_body(client: TestClient) -> None:
    book_id = client.post("/books", json=book_data()).json()["id"]

    response = client.delete(f"/books/{book_id}")

    assert response.status_code == 204
    assert response.content == b""


def test_delete_book_then_get_returns_404(client: TestClient) -> None:
    book_id = client.post("/books", json=book_data()).json()["id"]
    client.delete(f"/books/{book_id}")

    response = client.get(f"/books/{book_id}")

    assert response.status_code == 404


def test_delete_book_frees_isbn_for_new_book(client: TestClient) -> None:
    book_id = client.post("/books", json=book_data()).json()["id"]
    client.delete(f"/books/{book_id}")

    response = client.post("/books", json=book_data())

    assert response.status_code == 201


def test_delete_book_missing_returns_404(client: TestClient) -> None:
    response = client.delete("/books/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Book not found"}


@pytest.mark.parametrize("book_id", [0, -(2**63) - 1, 2**63])
def test_delete_book_id_out_of_range_returns_422(client: TestClient, book_id: int) -> None:
    response = client.delete(f"/books/{book_id}")

    assert response.status_code == 422
