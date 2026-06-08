import re
from pathlib import Path

import fitz

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

def parse_file(file_path: Path, book_title: str) -> list[dict]:

    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        return _parse_pdf(file_path, book_title)
    
    elif suffix == ".txt":
        return _parse_text(file_path, book_title)
    
    elif suffix == ".epub":
        return parse_epub(file_path, book_title)
    
    else:
        raise ValueError(f"Unsupported File Type: {suffix}")
    
def _parse_pdf(path: Path, book_title: str) -> list[dict]:

    doc = fitz.open(str(path))
    pages = []
    current_chapter = "Introduction"

    for page_num, page in enumerate(doc, start = 1):
        text = page.get_text('text').strip()

        if not text:
            continue

        first_line = text.splitlines()[0].strip()

        if looks_like_chapter(first_line):
            current_chapter = first_line

        pages.append(
            {
                "text": text,
                'page': page_num,
                'chapter': current_chapter,
                'book_title': book_title
            }
        )
    
    doc.close()
    return pages

def _parse_text(path: Path, book_title: str) -> list[dict]:

    content = path.read_text(encoding = "utf-8", errors = 'replace')
    lines = content.splitlines()

    pages = []
    current_chapter = "Introduction"
    current_lines = []
    page_num = 1
    CHARS_PER_PAGE = 2000 # Each 2000 characters will be counted as one page

    for line in lines:
        stripped = line.strip()

        if looks_like_chapter(stripped):
            text = '\n'.join(current_lines).strip()

            if text:
                pages.append(
                    {
                        "text": text,
                        'page': page_num,
                        'chapter': current_chapter,
                        'book_title': book_title
                    }
                )

                page_num += 1

            current_chapter = stripped
            current_lines = []

        else:
            current_lines.append(line)
            
            if sum(len(l) for l in current_lines) >= CHARS_PER_PAGE:
                text = '\n'.join(current_lines).strip()
                if text:
                    pages.append(
                        {
                            "text": text,
                            'page': page_num,
                            'chapter': current_chapter,
                            'book_title': book_title
                        }
                    )

                    page_num += 1

                current_lines = []
    
    text = '\n'.join(current_lines).strip()
    if text:
        pages.append(
            {
                "text": text,
                'page': page_num,
                'chapter': current_chapter,
                'book_title': book_title
            }
        )

    return pages

def parse_epub(path: Path, book_title: str) -> list[dict]:

    book = epub.read_epub(str(path), options = {'ignore_ncx': True})
    pages = []
    page_num = 1

    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        soup = BeautifulSoup(item.get_content(), 'html.parser')

        heading = soup.find(['h1', 'h2', 'h3'])
        chapter = heading.get_text(strip = True) if heading else 'Chapter'

        text = soup.get_text(separator = '\n').strip()

        if not text:
            continue

        pages.append(
            {
                "text": text,
                'page': page_num,
                'chapter': chapter,
                'book_title': book_title
            }
        )

        page_num += 1

    return pages

_CHAPTER_PATTERN = re.compile(
    r"^(chapter\s+\d+|part\s+\d+|section\s+\d+|\d+\.\s+\w|\bprologue\b|\bepilogue\b)",
    re.IGNORECASE,
)

def looks_like_chapter(line: str) -> bool:
    
    if not line or len(line) > 80:
        return False
    
    return bool(_CHAPTER_PATTERN.match(line))