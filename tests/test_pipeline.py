"""
Tests for the RAG Book Knowledge Base.

Run with:
    pytest tests/ -v
"""
from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.routes import app
from app.ingestion.chunker import chunk_pages
from app.ingestion.parser import looks_like_chapter

client = TestClient(app)


# ── Parser tests ──────────────────────────────────────────────────────────────

class TestChapterDetection:
    def test_detects_chapter_one(self):
        assert looks_like_chapter("Chapter 1: The Beginning") is True

    def test_detects_part(self):
        assert looks_like_chapter("Part 2") is True

    def test_ignores_normal_prose(self):
        assert looks_like_chapter("The quick brown fox jumped over the lazy dog.") is False

    def test_ignores_empty(self):
        assert looks_like_chapter("") is False

    def test_ignores_long_lines(self):
        assert looks_like_chapter("Chapter 1: " + "x" * 80) is False


class TestTxtParser:
    def test_parses_plain_text(self):
        from app.ingestion.parser import _parse_text

        content = "Chapter 1\nSome text here. More words. " * 20
        with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", delete=False) as f:
            f.write(content)
            tmp = Path(f.name)

        pages = list(_parse_text(tmp, "Test Book"))
        tmp.unlink()

        assert len(pages) >= 1
        assert all(p["book_title"] == "Test Book" for p in pages)
        assert all("text" in p for p in pages)
        assert all("page" in p for p in pages)


# ── Chunker tests ─────────────────────────────────────────────────────────────

class TestChunker:
    def _make_page(self, text: str) -> dict:
        return {"text": text, "page": 1, "chapter": "Intro", "book_title": "Book A"}

    def test_short_text_one_chunk(self):
        # Use a text that is definitively shorter than CHUNK_SIZE (500 chars default)
        # by patching the config values used by the chunker
        from unittest.mock import patch
        short_text = "Hello world. This is a short passage."
        page = self._make_page(short_text)
        with patch("app.ingestion.chunker.CHUNK_SIZE", 500), \
             patch("app.ingestion.chunker.CHUNK_OVERLAP", 0):
            chunks = chunk_pages([page])
        assert len(chunks) == 1
        assert chunks[0]["text"] == short_text

    def test_metadata_preserved(self):
        page = self._make_page("Some content here.")
        chunks = chunk_pages([page])
        assert chunks[0]["book_title"] == "Book A"
        assert chunks[0]["page"] == 1
        assert chunks[0]["chapter"] == "Intro"

    def test_long_text_multiple_chunks(self):
        long_text = " ".join(["word"] * 400)
        page = self._make_page(long_text)
        chunks = chunk_pages([page])
        assert len(chunks) > 1

    def test_empty_text_no_chunks(self):
        page = self._make_page("")
        chunks = chunk_pages([page])
        assert chunks == []


# ── API endpoint tests ────────────────────────────────────────────────────────

class TestHealthEndpoint:
    def test_health_ok(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestUploadEndpoint:
    def test_rejects_unsupported_extension(self):
        resp = client.post(
            "/upload",
            files={"file": ("book.docx", b"content", "application/octet-stream")},
            data={"book_title": "Test"},
        )
        assert resp.status_code == 400
        assert "Unsupported" in resp.json()["detail"]

    @patch("app.api.routes.ingest_file")
    def test_successful_upload(self, mock_ingest):
        from app.ingestion.pipeline import IngestResult

        mock_ingest.return_value = IngestResult(
            book_title="My Book",
            pages_parsed=10,
            chunks_stored=42,
            concepts=[],
            success=True,
        )
        resp = client.post(
            "/upload",
            files={"file": ("book.txt", b"Some book content", "text/plain")},
            data={"book_title": "My Book"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["book_title"] == "My Book"
        assert body["chunks_stored"] == 42
        assert body["status"] == "ready"


class TestQueryEndpoint:
    @patch("app.api.routes.rag_query")
    @patch("app.api.routes.list_books")
    def test_successful_query(self, mock_list, mock_query):
        from app.rag.engine import QueryResult, Source

        mock_list.return_value = ["Book A"]
        mock_query.return_value = QueryResult(
            answer="The answer is 42.",
            sources=[
                Source(
                    book_title="Book A",
                    page=7,
                    chapter="Chapter 3",
                    excerpt="...relevant passage...",
                )
            ],
            success=True,
        )

        resp = client.post("/query", json={"question": "What is the answer?"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["answer"] == "The answer is 42."
        assert len(body["sources"]) == 1
        assert body["sources"][0]["page"] == 7

    def test_empty_question_rejected(self):
        resp = client.post("/query", json={"question": "hi"})
        # question must be >= 3 chars — "hi" is 2 chars
        assert resp.status_code == 422

    @patch("app.api.routes.rag_query")
    @patch("app.api.routes.list_books")
    def test_query_failure_returns_502(self, mock_list, mock_query):
        from app.rag.engine import QueryResult

        mock_list.return_value = []
        mock_query.return_value = QueryResult(
            answer="", success=False, error="API timeout"
        )
        resp = client.post("/query", json={"question": "What happened?"})
        assert resp.status_code == 502
