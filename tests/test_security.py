import unicodedata

from exlibris.services.security import hash_password, verify_password


def test_hash_password_uses_argon2id() -> None:
    assert hash_password("correct horse").startswith("$argon2id$")


def test_hash_password_is_salted() -> None:
    assert hash_password("correct horse") != hash_password("correct horse")


def test_verify_password_accepts_correct_password() -> None:
    password_hash = hash_password("correct horse")

    assert verify_password("correct horse", password_hash)


def test_verify_password_rejects_wrong_password() -> None:
    password_hash = hash_password("correct horse")

    assert not verify_password("Correct horse", password_hash)


def test_verify_password_accepts_other_unicode_normalization() -> None:
    # "é" as one code point (NFC) vs "e" plus a combining accent (NFD).
    password_hash = hash_password(unicodedata.normalize("NFC", "café 1234"))

    assert verify_password(unicodedata.normalize("NFD", "café 1234"), password_hash)
