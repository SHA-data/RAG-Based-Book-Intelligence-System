import logging 
import shutil
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel, Field

from app.config import UPLOAD_DIR, ALLOWED_EXTENSIONS
from app.ingestion.pipeline import ingest_file
from app.ingestion.vector_store import list_books, delete_book
from app.rag.engine import query as rag_query

from app.automation.concept_extractor import get_concepts, get_all_concepts

logging.basicConfig(level = logging.INFO)

app = FastAPI(
    title = "RAG Book Knowledge Base",
    description = """
        Upload books in PDF, TXT, or EPUB format and ask questions in plain language.
        Every answer includes exact source citations — book title, chapter, and page number.

        ## Quick start
            1. Upload a book via **POST /upload**
            2. Ask a question via **POST /query**
            3. Get a grounded answer with citations

        ## Multi-book queries
            Pass a list of `book_ids` to scope your question to specific books or omit it to search your entire library.
        """,
    version="1.0.0",
    contact = {
        "name": "RAG Book KB",
    },
    license_info={
        "name": "MIT",
    }
)

# Allow requests from any origin point
app.add_middleware(
    CORSMiddleware,
    allow_origins = ['*'],
    allow_methods = ['*'],
    allow_headers = ['*']
)

# Main Root Endpoint with API information and available endpoints.
@app.get("/", tags=["System"])
async def root():
    return {
        "name": "RAG Book Knowledge Base",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "upload_book": "POST /upload",
            "query_books": "POST /query",
            "list_books": "GET /books",
            "delete_book": "DELETE /books/{book_title}",
            "health": "GET /health",
        }
    }

# The UploadResponse and BookListResponse models define the exactly structures the JSON responses will have
class UploadResponse(BaseModel):
    book_title: str = Field(..., description="The title used to identify this book in the system")
    pages_parsed: int = Field(..., description="Number of pages extracted from the file")
    chunks_stored: int = Field(..., description="Number of text chunks indexed in the vector database")
    status: str = Field(..., description="'ready' if ingestion succeeded, 'error' if it failed")
    message: str = Field(..., description="Human-readable summary of the ingestion result")

class BookListResponse(BaseModel):
    books: list[str]
    total: int

class SourceModel(BaseModel):
    book_title: str
    page: int
    chapter: str
    excerpt: str = Field(..., description = "First 300 characters of the retrieved passage")

class QueryRequest(BaseModel):
    question: str = Field(
        ...,
        min_length = 3,
        max_length = 500,
        description = "Your question in plain language.",
        examples = [
            "What are the main themes of this book?",
            "What does the author say about leadership?"
            ]
    )

    book_ids: list[str] | None = Field(
        default=None,
        description = (
            "Optional list of book titles to restrict the search to. "
            "Leave empty to search across all uploaded books."
        ),
        examples = [None, ["AI Fundamentals"], ["Book A", "Book B"]],
    )

class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceModel]
    books_searched: int

# Endpoints

@app.post(
    '/upload',
    response_model = UploadResponse,
    summary = 'Upload a book for ingestion',
    tags = ['Ingestion']
)

# Upload the file which will then be parsed, chunked, embedded and stored in the vector database automatically
async def upload_book(file: UploadFile = File(..., description = 'PDF, TXT or EPUB file'), book_title: str = Form(default = '', description = 'Display title. Defaults to filename')):

    # Checks the file extension
    suffix = Path(file.filename).suffix.lower()
    
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code = 400, detail = f"Unsupported file type '{suffix}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")
    
    # Confirms that the file is not empty
    if file.size == 0:
        raise HTTPException(status_code = 400, detail = "Uploaded file is empty.")
    
    # Uses filename as title if none provided
    title = book_title.strip() or Path(file.filename).stem

    # Checks if the book is already indexed
    existing = list_books()

    if title in existing:
        raise HTTPException(status_code = 409, detail = f"A book titled '{title}' is already indexed in the knowledge base. Delete it first with DELETE /books/{title} if you want to re-upload.")
    # Saves file to the uploads folder
    dest = UPLOAD_DIR / file.filename

    with dest.open('wb') as f:
        shutil.copyfileobj(file.file, f)

    # Runs the ingestion pipeline
    result = ingest_file(dest, title)

    # Returns error and cleans the saved file if the ingestion fails
    if not result.success:
        dest.unlink(missing_ok = True)
        raise HTTPException(status_code = 500, detail = result.error)
    
    # Otherwise, returns success response
    response = UploadResponse(
        book_title=result.book_title, 
        pages_parsed=result.pages_parsed, 
        chunks_stored=result.chunks_stored, 
        status="ready", 
        message=f"Successfully ingested '{title}' with {result.chunks_stored} chunks indexed."
    )
    
    return response

@app.get(
    '/books',
    response_model = BookListResponse,
    summary = 'List all uploaded books',
    tags = ['Library']
)

# Returns all book titles currently in the vector store
async def get_books():
    books = list_books()
    return BookListResponse(books = books, total = len(books))

@app.post(
        '/query',
        response_model = QueryResponse,
        summary = 'Ask a question across your uploaded books',
        tags = ['Query']
)

# Asks a questions and returns an answer with exact book title, chapter and page number
async def query_books(body: QueryRequest):
    result = rag_query(body.question, book_ids = body.book_ids)

    if not result.success:
        raise HTTPException(status_code = 502, detail = result.error)
    
    sources = [
        SourceModel(
            book_title = s.book_title,
            page = s.page,
            chapter = s.chapter,
            excerpt = s.excerpt
        )
        for s in result.sources
    ]

    all_books = list_books()
    books_searched = len(body.book_ids) if body.book_ids else len(all_books)

    response = QueryResponse(
        answer = result.answer,
        sources = sources,
        books_searched = books_searched 
    )

    return response

@app.get(
        '/query/books',
        response_model = BookListResponse,
        summary = 'List books available for querying',
        tags = ['Query']
)

# Returns all of the book titles that can be passed as book ids.
async def queryable_books():
    books = list_books()
    return BookListResponse(books = books, total = len(books))

@app.delete(
    "/books/{book_title}",
    summary = 'Remove a book from the knowledge base',
    tags = ['Library']
)

# Deletes all of the chunks for a given book title
async def remove_book(book_title: str):
    deleted = delete_book(book_title)

    if deleted == 0:
        raise HTTPException(status_code = 404, detail = f"Book '{book_title}' not found.")
    
    return {"message": f"Deleted {deleted} chunks for '{book_title}'."}

@app.get('/health', tags = ['System'])

# Quick checks that the server is running
async def health():
    return {'status': 'ok'}

@app.get(
    '/books/{book_title}/concepts',
    summary = 'Get core concepts extracted from a book',
    tags = ['Library']
)

# Returns the core concepts that are automatically extracacted from a book during ingestion
async def book_concepts(book_title: str):
    concepts = get_concepts(book_title)

    if not concepts:
        raise HTTPException(status_code = 404, detail = f"No concepts found for '{book_title}'. The book may not exist or the concept extraction may have failed.")
    
    return {'book_title': book_title, 'concepts': concepts}

@app.get(
    '/concepts',
    summary = 'Get concepts from all books',
    tags = ['Library']
)

# Returns the core concepts for every book in the knowledge base which is usefull for getting a broad-level overview of the entire library
async def all_concepts():
    data= get_all_concepts()

    return {"books": data, "total_books": len(data)}