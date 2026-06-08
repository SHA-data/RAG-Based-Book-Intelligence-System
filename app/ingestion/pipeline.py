import logging 
from dataclasses import dataclass
from pathlib import Path

from app.ingestion.parser import parse_file
from app.ingestion.chunker import chunk_pages
from app.ingestion.vector_store import store_chunks

logger = logging.getLogger(__name__)

@dataclass
class IngestResult:
    book_title: str
    pages_parsed: int
    chunks_stored: int
    concepts: list[str]
    success: bool
    error: str | None = None

# The concept ingestion pipeline for one book file
def ingest_file(file_path: Path, book_title: str) -> IngestResult:

    try:
        logger.info("Parsing %s", file_path.name)
        pages = parse_file(file_path, book_title)

        logger.info('Chunking %d Pages', len(pages))
        chunks = chunk_pages(pages)

        logger.info('Embedding and storing %d chunks', len(chunks))
        stored = store_chunks(chunks)

        # Concept extraction will run after storage so search works immediately
        logger.info("Extracting concepts from '%s'", book_title)

        # Imported inside the function to avoid the circular import chain at startup
        from app.automation.concept_extractor import extract_concepts
        concepts = extract_concepts(book_title)

        ingested_result = IngestResult(
            book_title = book_title, 
            pages_parsed = len(pages), 
            chunks_stored = stored,
            concepts = concepts,
            success = True
        )

        return ingested_result
    
    except Exception as exc:
        logger.exception('Ingestion failed for %s', file_path.name)

        ingested_result = IngestResult(book_title = book_title, pages_parsed = 0, chunks_stored = 0, concepts = [], success = False, error = str(exc))

        return ingested_result