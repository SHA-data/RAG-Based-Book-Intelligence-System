from unittest.mock import patch, MagicMock
import pytest

from fastapi.testclient import TestClient

from app.api.routes import app

client = TestClient(app)

class TestHealth_Root:
    def test_health_returns_ok(self):
        resp = client.get('/health')

        assert resp.status_code == 200
        assert resp.json()['status'] == 'ok'

    def test_root_returns_endpoint_map(self):
        resp = client.get('/')

        assert resp.status_code == 200

        body = resp.json()

        assert 'endpoints' in body
        assert 'upload_book' in body['endpoints']
        assert 'query_books' in body['endpoints']

class TestUploadEndpoint:
    def test_rejects_unsupported_extension(self):
        resp = client.post(
            '/upload',
            files = {
                'file': ('book.docx', b'content', 'application/octet-stream')
            },
            data = {
                'book_title': 'Test'
            }
        )

        assert resp.status_code == 400
        assert 'Unsupported' in resp.json()['detail']

    def test_rejets_empty_file(self):
        resp = client.post(
            '/upload',
            files = {
                'file': ('book.txt', b'', 'text/plain')
            },
            data = {
                'book_title': 'Empty'
            }
        )

        assert resp.status_code == 400
        assert 'empty' in resp.json()['detail'].lower()

    @patch('app.api.routes.list_books', return_value = [])
    @patch('app.api.routes.ingest_file')
    def test_successful_txt_upload(self, mock_ingest, mock_list):
        from app.ingestion.pipeline import IngestResult

        mock_ingest.return_value = IngestResult(
            book_title = 'My Book',
            pages_parsed = 5,
            chunks_stored = 20,
            concepts = ['AI', 'ML'],
            success = True
        )

        resp = client.post(
            '/upload',
            files = {
                'file': ('book.txt', b'Some book content here.', 'text/plain')
            },
            data = {
                'book_title': 'My Book'
            }
        )

        assert resp.status_code == 200
        body = resp.json()

        assert body['book_title'] == 'My Book'
        assert body['chunks_stored'] == 20
        assert body['status'] == 'ready'

    @patch('app.api.routes.list_books', return_value = ['Existing Book'])
    def test_rejects_duplicate_book(self, mock_list):
        resp = client.post(
            '/upload',
            files = {
                'file': ('book.txt', b'some content.', 'text/plain')
            },
            data = {
                'book_title': 'Existing Book'
            }
        )

        assert resp.status_code == 409
        assert 'already' in resp.json()['detail'].lower()

    @patch('app.api.routes.list_books', return_value = [])
    @patch('app.api.routes.ingest_file')
    def test_ingestion_failure_returns_500(self, mock_ingest, mock_list):
        from app.ingestion.pipeline import IngestResult

        mock_ingest.return_value = IngestResult(
            book_title = 'Bad Book',
            pages_parsed = 0,
            chunks_stored = 0,
            concepts = [],
            success = False,
            error = 'Parsing Failed' 
        )

        resp = client.post(
            'upload',
            files = {
                'file': ('book.txt', b'content', 'text/plain')
            },
            data = {
                'book_title': 'Bad Book'
            }
        )

        assert resp.status_code == 500

class TestQueryEndpoint:

    @patch('app.api.routes.list_books', return_value = ['Book A'])
    @patch('app.api.routes.rag_query')
    def test_successful_query(self, mock_query, mock_list):
        from app.rag.engine import QueryResult, Source

        mock_query.return_value = QueryResult(
            answer = 'The answer is 42 [SOURCE 1].',
            sources = [
                Source(
                    book_title = 'Book A',
                    page = 7,
                    chapter = 'Chapter 3',
                    excerpt = 'Relevant passage here.'
                )
            ],
            success = True
        )

        resp = client.post(
            '/query',
            json = {
                'question': 'What is the answer?'
            }
        )

        assert resp.status_code == 200
        body = resp.json()

        assert '42' in body['answer']
        assert len(body['sources']) == 1
        assert body['sources'][0]['page'] == 7
        assert body['books_searched'] == 1

    # As minimum character length is 3, anything below it will fail validation
    def test_question_too_short_rejected(self):
        resp = client.post(
            '/query',
            json = {
                'question': 'hi'
            }
        )

        assert resp.status_code == 422
 
    def test_missing_question_rejected(self):
        resp = client.post(
            '/query',
            json = {}
        )

        assert resp.status_code == 422

    @patch("app.api.routes.list_books", return_value = [])
    @patch("app.api.routes.rag_query")
    def test_groq_failure_returns_502(self, mock_query, mock_list):
        from app.rag.engine import QueryResult

        mock_query.return_value = QueryResult(
            answer = '',
            success = False,
            error = 'Groq API Timeout'
        )

        resp = client.post(
            'query',
            json = {
                'question': 'What happened?'
            }
        )

        assert resp.status_code == 502

    @patch("app.api.routes.list_books", return_value = ['Book A', 'Book B'])
    @patch("app.api.routes.rag_query")
    def test_book_ids_filter_respected(self, mock_query, mock_list):
        from app.rag.engine import QueryResult, Source

        mock_query.return_value = QueryResult(
            answer = 'Filtered answer.',
            sources = [
                Source(
                    book_title = 'Book A',
                    page = 1,
                    chapter = 'Ch1',
                    excerpt = 'text'
                )
            ],
            success = True
        )

        resp = client.post(
            '/query',
            json = {
                'question': 'Tell me something',
                'book_ids': ['Book A']
            }
        )

        assert resp.status_code == 200
        assert resp.json()['books_searched'] == 1 # Books searched should be 1 instead of 2

class TestBooksEndpoint:
    @patch("app.api.routes.list_books", return_value = ['Book A', 'Book B'])
    def test_lists_all_books(self, mock_list):
        resp = client.get('/books')
        
        assert resp.status_code == 200
        body = resp.json()

        assert body['total'] == 2
        assert 'Book A' in body['books']

    @patch("app.api.routes.list_books", return_value = [])
    def test_empty_library(self, mock_list):
        resp = client.get('/books')

        assert resp.status_code == 200
        assert resp.json()['total'] == 0

    @patch("app.api.routes.delete_book", return_value = 5)
    def test_delete_existing_book(self, mock_delete):
        resp = client.delete('/books/My Book')

        assert resp.status_code == 200
        assert 'Deleted' in resp.json()['message']

    @patch("app.api.routes.delete_book", return_value = 0)
    def test_delete_nonexistent_book_returns_404(self, mock_delete):
        resp = client.delete('/books/Ghost Book')

        assert resp.status_code == 404