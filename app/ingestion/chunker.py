from app.config import CHUNK_SIZE, CHUNK_OVERLAP

def chunk_pages(pages: list[dict]) -> list[dict]:

    chunks = []

    for page in pages:
        page_chunks = split_text(page['text'])

        for idx, chunk_text in enumerate(page_chunks):
            chunks.append(
                {
                    'text': chunk_text,
                    'book_title': page['book_title'],
                    'page': page['page'],
                    'chapter': page['chapter'],
                    'chunk_idx': idx
                }
            )

    return chunks

def split_text(text: str) -> list[dict]:

    words = text.split()
    
    if not words:
        return []
    
    chunks = []
    start = 0

    # Accumulate the words until we hit CHUNK_SIZE characters (500)
    while start < len(words):
        end = start
        length = 0

        while end < len(words) and length + len(words[end]) + 1 <= CHUNK_SIZE:
            length += len(words[end]) + 1
            end += 1

        if end == start:
            end = start + 1 # So that the chunk always moves forward at least one word

        chunks.append(" ".join(words[start:end]))

        # Making sure CHUNK_OVERLAP characters aren't hit while creating the overlap 
        overlap_chars = 0
        overlap_end = end

        while overlap_end > start and overlap_chars < CHUNK_OVERLAP:
            overlap_end -= 1
            overlap_chars += len(words[overlap_end]) + 1

        start = max(start + 1, overlap_end)

    return chunks