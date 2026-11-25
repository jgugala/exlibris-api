import unicodedata

from pwdlib import PasswordHash

# Argon2id with pwdlib's recommended parameters. Stateless, so a module-level instance
# is safe; nothing in a request needs to replace it.
_password_hash = PasswordHash.recommended()


def _normalize(password: str) -> str:
    # NFKC (NIST SP 800-63B): "é" typed as one code point or as "e" + a combining accent
    # is the same password, whatever keyboard or OS the client uses.
    return unicodedata.normalize("NFKC", password)


def hash_password(password: str) -> str:
    """Hash with a random salt; the result embeds the algorithm, parameters and salt."""
    return _password_hash.hash(_normalize(password))


def verify_password(password: str, password_hash: str) -> bool:
    return _password_hash.verify(_normalize(password), password_hash)
