# 0002: Book is a shared catalog entry

- Status: accepted
- Date: 2026-10-22

## Context

Books are identified by ISBN, and from stage 4 their details are fetched from Open Library. From stage 3 there are many users, each with their own shelf. A book could be modeled either as one row per user (unique per user and ISBN) or as one shared row for everyone.

## Decision

`Book` is a shared catalog entry: one row per book for all users, identified by a globally unique ISBN. The ISBN is immutable; `PATCH /books/{id}` does not accept it. Creating a book with an existing ISBN returns 409.

## Consequences

Book details are stored once, not repeated on every shelf. Reading status, rating and review describe a user's relation to a book, not the book itself. They live on `Book` only while there is a single implicit user (stages 1–2). Stage 3 moves them to per-user tables, starting with a shelf table linking users to books; the design of those tables, including whether reviews get their own table, is decided in stage 3 in its own ADR. An overall rating of a book is computed from users' ratings, not stored on `Book`.
