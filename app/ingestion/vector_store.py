import uuid
import google.generativeai as genai
import chromadb

from app.config import GEMINI_API_KEY, GEMINI_EMBEDDING_MODEL, CHROMA_PERSIST_DIR, TOP_K_RESULTS

genai.configure(api_key = GEMINI_API_KEY)

collection = 'books'

# Creating collection of ChromaDB or getting the existing collection 
def get_collection():
    
    client = chromadb.PersistentClient(path = str(CHROMA_PERSIST_DIR))

    collection_created = client.get_or_create_collection(
        name = collection, metadata = {
            'hhsw:space': 'cosine'
        }
    )

    return collection_created

# Calls Gemini to embed the texts 
def embed_texts(texts: list[str]) -> list[list[float]]:

    result = genai.embed_content(
        model = GEMINI_EMBEDDING_MODEL, 
        content = texts, 
        task_type = 'retrieval_document'
    )

    return result['embedding']

# Embeds a single search query
def embed_query(text: str) -> list[float]:

    result = genai.embed_content(
        model = GEMINI_EMBEDDING_MODEL,
        content = text,
        task_type = 'retrieval_query'
    )

    return result['embedding']

# Embed and store chunks in ChromaDB
def store_chunks(chunks: list[dict]) -> int:

    if not chunks:
        return 0
    
    collection = get_collection()

    # Embed all chunk texts in one API call
    texts = [c['text'] for c in chunks]
    embedding = embed_texts(texts)

    metadata = [
        {
            "book_title": c["book_title"],
            "page": str(c["page"]),       # Typecasting into string since ChromaDB requires string metadata
            "chapter": c["chapter"],
            "chunk_index": str(c["chunk_idx"]),
        }
        for c in chunks
    ]

    id = [str(uuid.uuid4()) for _ in chunks]

    collection.upsert(
        documents = texts,
        embeddings = embedding,
        metadatas = metadata,
        ids = id
    )

    return len(chunks)

# Searches for the most relevant chunks for a question and returns the top_k results with text and metadata
def search(query: str, book_ids: list[str] | None = None, top_k: int | None = None) -> list[dict]:

    collection = get_collection()
    k = top_k or TOP_K_RESULTS

    query_embedding = embed_query(query)

    where_filter = None

    if book_ids:
        where_filter = {'book_title': {"$in": book_ids}}

    results = collection.query(
        query_embeddings = [query_embedding],
        n_results = k,
        where = where_filter,
        include = ['documents', 'metadatas', 'distances']
    )

    hits = []

    for doc, meta, dist in zip(results['documents'][0], results['metadatas'][0], results['distances'][0]):
        hits.append(
            {
                "text": doc,
                "book_title": meta.get("book_title", "Unknown"),
                "page": int(meta.get("page", 0)),
                "chapter": meta.get("chapter", ""),
                "distance": round(dist, 4),
            }
        )

    return hits

# Returns all unique book titles in store
def list_books() -> list[str]:
    
    collection = get_collection()
    result = collection.get(include = ['metadatas'])
    
    titles = {m['book_title'] for m in result['metadatas'] if 'book_title' in m}
    return sorted(titles)

# Deletes all chunks of a book and returns the count for the deleted chunks
def delete_book(book_title: str) -> int:
    collection = get_collection()
    existing = collection.get(where = {'book_title': {'$eq': book_title}})
    
    ids_to_delete = existing['ids']
    
    if ids_to_delete:
        collection.delete(ids = ids_to_delete)

    return len(ids_to_delete)