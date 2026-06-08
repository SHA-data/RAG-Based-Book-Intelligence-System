import json
import logging 

from pathlib import Path
from groq import Groq

from app.config import GROQ_MODEL, GROQ_API_KEY
from app.ingestion.vector_store import search

logger = logging.getLogger(__name__)

client = Groq(api_key = GROQ_API_KEY)

# Stores the concepts in a simple JSON file
concepts_file = Path('data/concepts.json')

# Loads the concepts
def load_concepts() -> dict:
    if concepts_file.exists():
        return json.loads(concepts_file.read_text(encoding = 'utf-8'))
    
    return {}

# Saves the concepts
def save_concepts(concepts: dict) -> None:
    concepts_file.parent.mkdir(parents = True, exist_ok = True)
    concepts_file.write_text(
        json.dumps(concepts, indent = 2, ensure_ascii = False),
        encoding = "utf-8"
    )

# Uses Groq to extract the core concepts from a book
def extract_concepts(book_title: str) -> list[str]:
    logger.info("Extracting concepts from '%s'...", book_title)

    # Gets a sample by searching with some general queries
    sample_queries = [
        'main ideas and key concepts',
        'introduction and overview',
        'conclusions and findings'
    ]

    seen_texts = set()
    all_chunks = []

    for q in sample_queries:
        hits = search(q, book_ids = [book_title], top_k = 3)

        for hit in hits:
            if hit['text'] not in seen_texts:
                seen_texts.add(hit['text'])
                all_chunks.append(hit['text'])

    if not all_chunks:
        logger.warning("No chunks found for '%s'. Skipping concept extraction", book_title)
        return []
    
    sample = "\n\n \n\n".join(all_chunks)[:2000]

    prompt = f"""
        Here is a sample from the book "{book_title}":

        {sample}

        Based on this content, identify the 8 to 10 most important core concepts, themes, or topics covered in this book.

        Respond with ONLY a JSON array of short concept strings. No explanation.
        Example format: ["Concept 1", "Concept 2", "Concept 3"]
    """

    try:
        response = client.chat.completions.create(
            model = GROQ_MODEL,
            messages = [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature = 0.1,
            max_tokens = 256
        )

        raw = response.choices[0].message.content.strip()

        # Strips markdown code fence if the model wraps the JSON
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            
            if raw.startswith('json'):
                raw = raw[4:]

        raw = raw.strip()

        concepts = json.loads(raw)

        if not isinstance(concepts, list):
            raise ValueError('Expected a list')
        
    except Exception as exc:
        logger.error("Concept extraction failed for '%s': %s", book_title, exc)
        return []
    
    # Saves to disk
    all_concepts = load_concepts()
    all_concepts[book_title] = concepts
    save_concepts(all_concepts)

    logger.info("Extracted %d concepts from '%s'", len(concepts), book_title)
    return concepts

# Retrieves the stored concepts for a book
def get_concepts(book_title: str) -> list[str]:
    all_concepts = load_concepts()
    return all_concepts.get(book_title, [])

# Retrieve concepts for all books
def get_all_concepts() -> dict:
    return load_concepts()