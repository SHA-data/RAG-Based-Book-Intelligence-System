import logging
from dataclasses import dataclass, field

from groq import Groq

from app.config import GROQ_API_KEY, GROQ_MODEL, TOP_K_RESULTS
from app.ingestion.vector_store import search

logger = logging.getLogger(__name__)

client = Groq(api_key = GROQ_API_KEY)

# One source citation that is to be attached to an answer
@dataclass
class Source:
    book_title: str
    page: str
    chapter: str
    excerpt: str

# Everything returned from a RAG Query
@dataclass
class QueryResult:
    answer: str
    sources: list[Source] = field(default_factory = list)
    success: bool = True
    error: str | None = None

# Main query function
def query(question: str, book_ids: list[str] | None = None) -> QueryResult:

    # Retrive relevant chunks from ChromaDB
    hits = search(question, book_ids = book_ids, top_k = TOP_K_RESULTS)

    if not hits:
        answer = QueryResult(
            answer = ('I could not find any relevant passages in the uploaded books to answer your question. Try uploading more books or rephrasing.'),
            sources = []
        )

        return answer
    
    # Build the prompt
    context_blocks = []

    for i, hit in enumerate(hits, start = 1):
        context_blocks.append(
            f"[SOURCE {i}]\n"
            f"Book: {hit['book_title']}\n"
            f"Chapter: {hit['chapter']}\n"
            f"Page: {hit['page']}\n"
            f"---\n"
            f"{hit['text']}"
        )

    context = '\n\n'.join(context_blocks)

    system_prompt = """
        You are a knowledgeable assistant that answers questions based strictly on the book excerpts provided to you.
        
        Rules you must follow:
            - Only use information from the provided excerpts
            - Always cite your sources using [SOURCE 1], [SOURCE 2] etc.
            - If the excerpts don't contain enough information, say so clearly
            - Never make up information that isn't in the excerpts
            - Be concise but thorough
    """
    
    user_message = f"""
        Here are relevant excerpts from the books:

        {context}

        Question: {question}

        Answer the question using only the excerpts above. Reference sources with [SOURCE N] inline as you use them.
    """

    # Calls Groq
    try:
        response = client.chat.completions.create(
            model = GROQ_MODEL,
            messages = [
                {
                    'role': 'system',
                    'content': system_prompt
                },

                {
                    'role': 'user',
                    'content': user_message
                }
            ]
        )

        answer = response.choices[0].message.content

    except Exception as exc:
        logger.exception('Groq API call failed')
        return QueryResult(answer = '', success = False, error = str(exc))
    
    #Builds source citations
    sources = [
        Source(
            book_title = h['book_title'],
            page = h['page'],
            chapter = h['chapter'],
            excerpt = h['text'][:300]
        )
        for h in hits
    ]

    return QueryResult(answer = answer, sources = sources, success = True)

