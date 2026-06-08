import tempfile
from pathlib import Path
import pytest

from app.ingestion.parser import looks_like_chapter, _parse_text

# Tests for the chapters heading heuristic
class TestChapterDetection:
    def test_detects_chapter_number(self):
        assert looks_like_chapter("Chapter 1: The Beginning") is True

    def test_detects_chapter_lowercase(self):
        assert looks_like_chapter("chapter 3") is True

    def test_detects_part(self):
        assert looks_like_chapter("Part 2: The Middle") is True

    def test_detects_section(self):
        assert looks_like_chapter("Section 4: Advanced Topics") is True

    def test_detects_prologue(self):
        assert looks_like_chapter("Prologue") is True

    def test_detects_epilogue(self):
        assert looks_like_chapter("Epilogue") is True

    def test_ignores_normal_sentence(self):
        assert looks_like_chapter("The quick brown fox jumped.") is False

    def test_ignores_empty_string(self):
        assert looks_like_chapter("") is False

    def test_ignores_very_long_lines(self):
        # Chapter headings are never 80+ characters
        assert looks_like_chapter("Chapter 1: " + "x" * 80) is False

    def test_ignores_numbers_mid_sentence(self):
        assert looks_like_chapter("There are 3 reasons why this works.") is False

class TestTextParser:
    def write_tmp(self, content: str) -> Path:
        f = tempfile.NamedTemporaryFile(
            suffix = '.txt', mode = 'w', encoding = 'utf-8', delete = False
        )

        f.write(content)
        f.close()

        return Path(f.name)
    
    def test_returns_list_of_dicts(self):
        path = self.write_tmp('Hello world. This is some content')
        pages = list(_parse_text(path, 'Test Book'))
        path.unlink()

        assert isinstance(pages, list)
        assert len(pages) >= 1

    def test_page_dict_has_required_keys(self):
        path = self.write_tmp("Some content here for testing purposes.")
        pages = list(_parse_text(path, "My Book"))
        path.unlink()
        page = pages[0]

        assert "text" in page
        assert "page" in page
        assert "chapter" in page
        assert "book_title" in page

    def test_book_title_preserved(self):
        path = self.write_tmp('Content of the book')
        pages = list(_parse_text(path, 'Special Title'))
        path.unlink()

        assert all(p['book_title'] == 'Special Title' for p in pages)

    def test_chapter_headings_detected(self):
        content = "Chapter 1: Start\nSome text here.\n\nChapter 2: End\nMore text."
        path = self.write_tmp(content)
        pages = list(_parse_text(path, 'Chaptered Book'))
        path.unlink()
        chapters = [p['chapter'] for p in pages]

        # At least one page should have Chapter 2 detected
        assert any('Chapter 2' in ch for ch in chapters)

    def test_empty_file_returns_empty_list(self):
        path = self.write_tmp("")
        pages = list(_parse_text(path, 'Empty Book'))
        path.unlink()

        assert pages == []

    # Make content long enough to create multiple pages
    def test_page_numbers_increment(self):
        content = ("Word " * 100 + '\n') * 10
        
        path = self.write_tmp(content)
        pages = list(_parse_text(path, 'Long Book'))
        path.unlink()

        if len(pages) > 1:
            page_nums = [p['page'] for p in pages]

            assert page_nums == sorted(page_nums)
            assert page_nums[0] == 1