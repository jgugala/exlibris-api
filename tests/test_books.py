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


def test_list_books_ordered_by_id(client: TestClient) -> None:
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


def create_books(client: TestClient, count: int) -> list[int]:
    """Create ``count`` books with distinct 13-digit ISBNs and return their ids."""
    return [
        client.post("/books", json=book_data(isbn=f"{9780000000000 + n}")).json()["id"]
        for n in range(count)
    ]


def test_list_books_default_page_returns_first_20(client: TestClient) -> None:
    ids = create_books(client, 25)

    response = client.get("/books")

    assert response.status_code == 200
    assert [book["id"] for book in response.json()] == ids[:20]


def test_list_books_skip_and_limit_return_requested_page(client: TestClient) -> None:
    ids = create_books(client, 25)

    response = client.get("/books", params={"skip": 20, "limit": 10})

    assert response.status_code == 200
    assert [book["id"] for book in response.json()] == ids[20:]


def test_list_books_skip_past_end_returns_empty_list(client: TestClient) -> None:
    create_books(client, 3)

    response = client.get("/books", params={"skip": 10})

    assert response.status_code == 200
    assert response.json() == []


def test_list_books_paginates_filtered_results(client: TestClient) -> None:
    client.post("/books", json=book_data(isbn="9780000000001", status="read"))
    second = client.post("/books", json=book_data(isbn="9780000000002", status="read")).json()
    client.post("/books", json=book_data(isbn="9780000000003", status="reading"))

    response = client.get("/books", params={"status": "read", "skip": 1, "limit": 5})

    assert response.status_code == 200
    assert [book["id"] for book in response.json()] == [second["id"]]


@pytest.mark.parametrize(
    "params",
    [{"limit": 0}, {"limit": 101}, {"skip": -1}, {"skip": 2**63}, {"limit": "abc"}],
)
def test_list_books_invalid_pagination_returns_422(
    client: TestClient, params: dict[str, Any]
) -> None:
    response = client.get("/books", params=params)

    assert response.status_code == 422


# GET /books filters


def test_list_books_min_rating_returns_only_rated_at_least(client: TestClient) -> None:
    client.post("/books", json=book_data(isbn="9780000000001", rating=2))
    rated_4 = client.post("/books", json=book_data(isbn="9780000000002", rating=4)).json()
    client.post("/books", json=book_data(isbn="9780000000003"))

    response = client.get("/books", params={"min_rating": 3})

    assert response.status_code == 200
    assert [b["id"] for b in response.json()] == [rated_4["id"]]


def test_list_books_author_matches_case_insensitive_substring(client: TestClient) -> None:
    bloch = client.post("/books", json=book_data(isbn="9780000000001")).json()
    client.post("/books", json=book_data(isbn="9780000000002", author="Martin Fowler"))

    response = client.get("/books", params={"author": "bloch"})

    assert response.status_code == 200
    assert [b["id"] for b in response.json()] == [bloch["id"]]


def test_list_books_status_and_author_combined_with_and(client: TestClient) -> None:
    both = client.post("/books", json=book_data(isbn="9780000000001", status="read")).json()
    client.post("/books", json=book_data(isbn="9780000000002", status="reading"))
    client.post(
        "/books", json=book_data(isbn="9780000000003", status="read", author="Martin Fowler")
    )

    response = client.get("/books", params={"status": "read", "author": "bloch"})

    assert response.status_code == 200
    assert [b["id"] for b in response.json()] == [both["id"]]


def test_list_books_paginates_results_filtered_by_author(client: TestClient) -> None:
    client.post("/books", json=book_data(isbn="9780000000001"))
    client.post("/books", json=book_data(isbn="9780000000002", author="Martin Fowler"))
    second = client.post("/books", json=book_data(isbn="9780000000003")).json()

    response = client.get("/books", params={"author": "bloch", "skip": 1, "limit": 1})

    assert response.status_code == 200
    assert [b["id"] for b in response.json()] == [second["id"]]


@pytest.mark.parametrize(
    "params",
    [
        {"min_rating": 0},
        {"min_rating": 6},
        {"min_rating": "3.5"},
        {"status": "foo"},
        {"author": ""},
        {"author": "   "},
        {"author": "x" * 256},
    ],
)
def test_list_books_invalid_filter_returns_422(client: TestClient, params: dict[str, Any]) -> None:
    response = client.get("/books", params=params)

    assert response.status_code == 422


def test_list_books_filters_documented_as_query_parameters(client: TestClient) -> None:
    parameters = client.get("/openapi.json").json()["paths"]["/books"]["get"]["parameters"]

    query_names = {p["name"] for p in parameters if p["in"] == "query"}

    assert {"status", "min_rating", "author"} <= query_names


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
