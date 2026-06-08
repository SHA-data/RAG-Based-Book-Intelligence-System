from unittest.mock import patch
import pytest

from app.ingestion.chunker import chunk_pages, split_text

# Tests for the main splitting function
class TestSplitText:
    def test_empty_text_returns_empty_list(self):
        assert split_text("") == []

    def test_short_text_stays_as_one_chunk(self):
        with patch('app.ingestion.chunker.CHUNK_SIZE', 500), patch('app.ingestion.chunker.CHUNK_OVERLAP', 0):
            result = split_text('Hello world this is short.')

        assert len(result) == 1
        assert result[0] == 'Hello world this is short.'

    def test_long_text_creates_multiple_chunks(self):
        long_text = "word " * 300

        with patch('app.ingestion.chunker.CHUNK_SIZE', 100), patch('app.ingestion.chunker.CHUNK_OVERLAP', 0):
            result = split_text(long_text)

        assert len(result) > 1

    # No words must be lost during the chunking process
    def test_chunks_cover_all_words(self):
        text = 'apple banana cherry date strawberry fig grape honeydew'

        with patch('app.ingestion.chunker.CHUNK_SIZE', 20), patch('app.ingestion.chunker.CHUNK_OVERLAP', 0):
            chunks = split_text(text)
        
        rejoined = " ".join(chunks)

        for word in text.split():
            assert word in rejoined
        
    # With an overlap, some words will appear in consecutive chunks
    def test_overlap_repeats_words(self):
        text = "word" * 50

        with patch('app.ingestion.chunker.CHUNK_SIZE', 50), patch('app.ingestion.chunker.CHUNK_OVERLAP', 20):
            chunks = split_text(text)

        # Last words of chunk 0 should appear at start of chunk 1 
        if len(chunks) > 1:
            last_words_of_first = set(chunks[0].split()[-3:])
            first_words_of_second = set(chunks[1].split()[:3])

            assert last_words_of_first and first_words_of_second

# Tests for the ful page that goes into the chunks pipeline 
class TestChunkPages:
    # Every chunk must have the souce metadata from its page
    def test_metadata_carried_through(self, sample_pages):
        chunks = chunk_pages(sample_pages)

        for chunk in chunks:
            assert "book_title" in chunk
            assert "page" in chunk
            assert "chapter" in chunk
            assert "chunk_idx" in chunk
            assert "text" in chunk
        
    def test_book_title_preserved(self, sample_pages):
        chunks = chunk_pages(sample_pages)

        assert all(c['book_title'] == 'Test Book' for c in chunks)

    def test_empty_pages_returns_empty(self):
        assert chunk_pages([]) == []

    def test_page_with_empty_text_skipped(self):
        pages = [
            {
                'text': '', 
                'page': 1,
                'chapter': 'Ch1',
                'book_title': 'Book'
            }
        ]

        chunks = chunk_pages(pages)
        assert chunks == []

    def test_chunk_index_starts_at_zero(self, sample_pages):
        chunks = chunk_pages(sample_pages)
        page1_chunks = [c for c in chunks if c['page'] == 1]

        assert page1_chunks[0]['chunk_idx'] == 0

    def test_multiple_pages_produce_chunks(self, sample_pages):
        chunks = chunk_pages(sample_pages)

        # There should be atleast 1 chunk per page
        assert len(chunks) >= 2