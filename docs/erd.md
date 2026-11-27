# Entity-relationship diagram

`Book` is a shared catalog entry (ADR 0002); `status`, `rating` and `review` move to per-user tables later in stage 3. `users` is not yet related to `books`; the shelf table will link them.

```mermaid
erDiagram
    books {
        int id PK
        string isbn UK "13 chars max, indexed"
        string title "255 chars max"
        string author "255 chars max"
        int pages "nullable"
        string status "want_to_read | reading | read, default want_to_read"
        int rating "nullable, 1-5 validated by the API"
        text review "nullable"
        datetime created_at "UTC"
    }
    users {
        int id PK
        string email UK "320 chars max, stored lowercase, indexed"
        string password_hash "Argon2id, 255 chars max"
        bool is_admin "default false"
        datetime created_at "UTC"
    }
```
