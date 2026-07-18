from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field, field_validator


class Category(BaseModel):
    id: int
    name: str = Field(min_length=1, max_length=50)


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    model_config = {"extra": "forbid"}

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Name must not be empty")
        return value


class Book(BaseModel):
    id: int
    title: str = Field(min_length=1, max_length=100)
    author: str = Field(min_length=1, max_length=100)
    year: int = Field(ge=0, le=2025)
    isbn: str
    price: float = Field(gt=0)
    category_id: Optional[int] = None


class BookCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    author: str = Field(min_length=1, max_length=100)
    year: int = Field(ge=0, le=2025)
    isbn: str
    price: float = Field(gt=0)
    category_id: Optional[int] = None
    model_config = {"extra": "forbid"}

    @field_validator("title", "author")
    @classmethod
    def validate_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Value must not be empty")
        return value

    @field_validator("isbn")
    @classmethod
    def validate_isbn(cls, value: str) -> str:
        if not value.isdigit() or len(value) not in (10, 13):
            raise ValueError("ISBN must contain 10 or 13 digits")
        return value


class BookNotFoundException(HTTPException):
    def __init__(self) -> None:
        super().__init__(status_code=404, detail="Book not found")


class DuplicateIsbnException(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=409,
            detail="Book with this ISBN already exists",
        )


class CategoryNotFoundException(HTTPException):
    def __init__(self) -> None:
        super().__init__(status_code=404, detail="Category not found")


app = FastAPI(title="Bookstore API")

BOOKS: list[dict] = []
CATEGORIES: list[dict] = []


@app.exception_handler(BookNotFoundException)
async def handle_book_not_found(
    request: Request, exc: BookNotFoundException
) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"detail": "Book not found", "code": "NOT_FOUND"},
    )


@app.exception_handler(DuplicateIsbnException)
async def handle_duplicate_isbn(
    request: Request, exc: DuplicateIsbnException
) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={"detail": "Book with this ISBN already exists", "code": "DUPLICATE_ISBN"},
    )


@app.exception_handler(CategoryNotFoundException)
async def handle_category_not_found(
    request: Request, exc: CategoryNotFoundException
) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"detail": "Category not found", "code": "CATEGORY_NOT_FOUND"},
    )


def next_id(items: list[dict]) -> int:
    return max((item["id"] for item in items), default=0) + 1


def find_book(book_id: int) -> dict:
    for book in BOOKS:
        if book["id"] == book_id:
            return book
    raise BookNotFoundException()


def validate_category(category_id: Optional[int]) -> None:
    if category_id is None:
        return
    if not any(category["id"] == category_id for category in CATEGORIES):
        raise CategoryNotFoundException()


@app.get("/categories", response_model=list[Category])
def list_categories() -> list[dict]:
    return CATEGORIES


@app.post("/categories", status_code=201, response_model=Category)
def create_category(category: CategoryCreate) -> dict:
    stored = {"id": next_id(CATEGORIES), **category.model_dump()}
    CATEGORIES.append(stored)
    return stored


@app.get("/books", response_model=list[Book])
def list_books(
    category_id: Optional[int] = None, year: Optional[int] = None
) -> list[dict]:
    result = BOOKS
    if category_id is not None:
        result = [book for book in result if book["category_id"] == category_id]
    if year is not None:
        result = [book for book in result if book["year"] == year]
    return result


@app.get("/books/search", response_model=list[Book])
def search_books(query: str) -> list[dict]:
    normalized = query.casefold()
    return [
        book
        for book in BOOKS
        if normalized in book["title"].casefold()
        or normalized in book["author"].casefold()
    ]


@app.get("/books/{book_id}", response_model=Book)
def get_book(book_id: int) -> dict:
    return find_book(book_id)


@app.post("/books", status_code=201, response_model=Book)
def create_book(book: BookCreate) -> dict:
    if any(existing["isbn"] == book.isbn for existing in BOOKS):
        raise DuplicateIsbnException()
    validate_category(book.category_id)
    stored = {"id": next_id(BOOKS), **book.model_dump()}
    BOOKS.append(stored)
    return stored


@app.put("/books/{book_id}", response_model=Book)
def update_book(book_id: int, book: BookCreate) -> dict:
    existing = find_book(book_id)
    if any(
        item["isbn"] == book.isbn and item["id"] != book_id
        for item in BOOKS
    ):
        raise DuplicateIsbnException()
    validate_category(book.category_id)
    existing.clear()
    existing.update({"id": book_id, **book.model_dump()})
    return existing


@app.delete("/books/{book_id}", status_code=204)
def delete_book(book_id: int) -> Response:
    book = find_book(book_id)
    BOOKS.remove(book)
    return Response(status_code=204)
