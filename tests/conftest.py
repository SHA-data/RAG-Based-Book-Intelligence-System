import sys

from unittest.mock import MagicMock, patch
import pytest

def pytest_configure(config):
    mocks = {
        "chromadb": MagicMock(),
        "groq": MagicMock(),
        "google.generativeai": MagicMock(),
        "fitz": MagicMock(),
        "ebooklib": MagicMock(),
        "ebooklib.epub": MagicMock(),
        "bs4": MagicMock(),
        "watchdog": MagicMock(),
        "watchdog.observers": MagicMock(),
        "watchdog.events": MagicMock()
    }
    
    for mod, mock in mocks.items():
        sys.modules[mod] = mock

# Minimal list of page dictionaries for testing chunker and pipeline

@pytest.fixture
def sample_pages():
    pages_sample = [
        {
            "text": "This is the content of page one. " * 10,
            "page": 1,
            "chapter": "Chapter 1: Introduction",
            "book_title": "Test Book"
        },
        {
            "text": "This is the content of page two. " * 10,
            "page": 2,
            "chapter": "Chapter 2: Deep Dive",
            "book_title": "Test Book"
        },
    ]
    return pages_sample

# Returns pre-built chunks for testing the vector store and RAG engine
@pytest.fixture
def sample_chunks():
    chunks_sample = [
        {
            "text": "Machine learning is a subset of artificial intelligence.",
            "book_title": "AI Book",
            "page": 1,
            "chapter": "Chapter 1",
            "chunk_index": 0
        },
        {
            "text": "Neural networks are inspired by the human brain.",
            "book_title": "AI Book",
            "page": 2,
            "chapter": "Chapter 2",
            "chunk_index": 0
        },
    ]
    return chunks_sample