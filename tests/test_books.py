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


def test_get_book_id_beyond_64_bit_returns_422(client: TestClient) -> None:
    response = client.get(f"/books/{2**63}")

    assert response.status_code == 422
