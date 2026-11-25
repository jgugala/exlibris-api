# 0005: Integer primary keys for all tables

- Status: accepted
- Date: 2026-11-25

## Context

Stage 3 adds the `users` and `shelf_entries` tables next to `books`, so the primary key type should be settled before they exist. The options were auto-increment integers, as `books` uses today, or UUIDv7. UUIDs are not enumerable, so they hide other users' resources and the size of the user base. UUIDv7 is also time-ordered, so pagination by id still works. Integers are smaller and simpler. On SQLite an `INTEGER PRIMARY KEY` is an alias for the `rowid`, while SQLAlchemy's `Uuid` type is stored as `CHAR(32)` with a separate index and wider foreign keys.

## Decision

All tables use auto-increment integer primary keys. The enumeration risk is small in this API. Books are a public catalog. Shelf entries are addressed by book (`/me/shelf/{book_id}`), so their own id is never exposed. Users are read only through `/me`, and `/admin/users` is restricted to admins. UUIDv7 was rejected because it protects nothing that is exposed here, and it adds cost: wider keys and indexes on SQLite, and a helper or library for generation, since `uuid.uuid7()` arrives only in Python 3.14.

## Consequences

Ids stay compact, ordered by insertion and validated as bounded integers in paths (a malformed id fails with 422). The user id returned by registration and carried in the JWT `sub` reveals the approximate number of users, which is accepted here. Revisit this decision when a per-user resource is addressed by its own id, most likely reviews becoming a separate resource for moderation and the live feed. Prefer adding a public UUID column next to the integer key for that resource over changing the primary key of every table.
