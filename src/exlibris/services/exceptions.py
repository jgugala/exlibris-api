class BookNotFoundError(Exception):
    def __init__(self, book_id: int) -> None:
        super().__init__(f"Book {book_id} not found")
        self.book_id = book_id


class DuplicateIsbnError(Exception):
    def __init__(self, isbn: str) -> None:
        super().__init__(f"Book with ISBN {isbn} already exists")
        self.isbn = isbn


class DuplicateEmailError(Exception):
    def __init__(self, email: str) -> None:
        super().__init__("Email already registered")
        self.email = email
