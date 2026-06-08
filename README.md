# RAG Book Knowledge Base

Turn uploaded books into a searchable AI knowledge base. Upload PDFs, TXTs, or EPUBs and ask questions in plain language. Every answer includes exact source citations (book title, chapter, page).

## Features

- Upload books in PDF, TXT, or EPUB format
- Automatic parsing, chunking, and embedding into a vector database
- Natural language Q&A with grounded answers and source references
- Query across multiple books simultaneously
- Core concepts automatically extracted from incoming books
- File-drop automation — drop a file into `uploads/` and ingestion runs automatically
- OpenAPI docs auto-generated at `/docs`

## Tech Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI + Uvicorn |
| Vector store | ChromaDB (local, persistent) |
| Embeddings | Google Gemini (`models/text-embedding-004`) |
| LLM | Groq (`llama-3.3-70b-versatile`) |
| PDF parsing | PyMuPDF |
| EPUB parsing | ebooklib + BeautifulSoup4 |
| Automation | watchdog (file-drop watcher) |

## Quick Start

We use `uv` for lightning fast dependencies and execution:

```bash
git clone <your-repo-url>
cd rag-book-kb
uv pip install -r requirements.txt
cp .env.example .env   # add your GROQ_API_KEY and GEMINI_API_KEY
uv run python main.py --watch
```

Open http://localhost:8000/docs for interactive API docs.

## Interactive CLI Testing

We also include an interactive testing suite right in your terminal!
```bash
# Keep the main.py server running, and in a separate terminal:
uv run python cli.py
```

## API Reference

### POST /upload
Upload a book file. Returns chunk count and status.

```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@mybook.pdf" \
  -F "book_title=My Great Book"
```

### POST /query
Ask a question. Returns answer + source citations.

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What does the author say about risk?"}'
```

### GET /books
List all indexed books.

### DELETE /books/{book_title}
Remove a book from the knowledge base.

### GET /concepts
Get core concepts extracted from all books.

## Running Tests
```bash
uv run pytest tests/ -v
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| GROQ_API_KEY | — | Required. Your Groq API key |
| GEMINI_API_KEY | — | Required. Your Google Gemini API key |
| GROQ_MODEL | llama-3.3-70b-versatile | Groq LLM model |
| GEMINI_EMBEDDING_MODEL | models/text-embedding-004 | Gemini Embedding model |
| CHROMA_PERSIST_DIR | ./data/chroma | ChromaDB path |
| UPLOAD_DIR | ./uploads | Book upload directory |
| CHUNK_SIZE | 500 | Characters per chunk |
| CHUNK_OVERLAP | 50 | Overlap between chunks |
| TOP_K_RESULTS | 5 | Passages retrieved per query |
