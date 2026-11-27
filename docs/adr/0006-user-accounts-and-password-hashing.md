# 0006: User accounts and password hashing

- Status: accepted
- Date: 2026-11-25

## Context

Stage 3 adds user accounts identified by email and protected by a password. A few choices shape how logins behave later: how emails are compared, how passwords are stored, and how much registration reveals about existing accounts.

## Decision

The whole email address, local part included, is lowercased before validation and stored that way. A plain `UNIQUE` constraint then rejects the same address in another case, and lookups at login need no `lower()`. RFC 5321 allows case-sensitive local parts, but no mainstream provider uses them, and two accounts differing only in case would confuse users.

Passwords are 8–128 characters, not stripped, normalized to NFKC (NIST SP 800-63B), and hashed with Argon2id through `pwdlib` using its recommended parameters. Argon2id is memory-hard and has no 72-byte input limit like bcrypt. The 128-character cap bounds the hashing work a single request can force. No composition rules are imposed.

Registering an address that already has an account returns 409, which reveals that the account exists. Hiding it would need an email confirmation flow, which is out of scope.

## Consequences

Login (#26) must lowercase the submitted email and use `verify_password`, which applies the same normalization. Changing the hashing parameters later is possible because each hash embeds its algorithm and parameters; `pwdlib` can rehash on successful login. Account enumeration through registration is accepted; revisit if email confirmation is added.
