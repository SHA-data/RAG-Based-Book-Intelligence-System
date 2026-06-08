import json
import tempfile

from pathlib import Path

from unittest.mock import patch, MagicMock

import pytest

# Tests for reading and writing the concepts JSON store
class TestConceptStorage:
    def test_load_returns_empty_dict_if_no_file(self, tmp_path, monkeypatch):
        from app.automation import concept_extractor

        monkeypatch.setattr(concept_extractor, 'concepts_file', tmp_path / 'concepts.json')

        from app.automation.concept_extractor import load_concepts

        assert load_concepts() == {}

    def test_save_and_load_roundtrip(self, tmp_path, monkeypatch):
        from app.automation import concept_extractor
        from app.automation.concept_extractor import save_concepts, load_concepts
        
        monkeypatch.setattr(concept_extractor, 'concepts_file', tmp_path / 'concepts.json')
        data = {
            'Book A': ['AI', 'ML', 'Data']
            }
        
        save_concepts(data)
        loaded = load_concepts()

        assert loaded == data

    def test_get_concepts_returns_list(self, tmp_path, monkeypatch):
        from app.automation import concept_extractor

        concepts_file = tmp_path / 'concepts.json'
        concepts_file.write_text(
            json.dumps(
                {
                    'My Book': ['Topic 1', 'Topic 2']
                }
            ),
            encoding = 'utf-8'
        )
        
        monkeypatch.setattr(concept_extractor, 'concepts_file', concepts_file)

        from app.automation.concept_extractor import get_concepts

        result = get_concepts('My Book')
        
        assert result == ['Topic 1', 'Topic 2']

    def test_get_concepts_missing_book_returns_empty(self, tmp_path, monkeypatch):
        from app.automation import concept_extractor

        monkeypatch.setattr(concept_extractor, 'concepts_file', tmp_path / 'concepts.json')

        from app.automation.concept_extractor import get_concepts

        assert get_concepts('Nonexistent Book') == []

# Tests for the LLM powered extraction function
class TestConceptExtraction:
    @patch("app.automation.concept_extractor.search")
    @patch("app.automation.concept_extractor.client")
    def test_returns_list_of_strings(self, mock_client, mock_search, tmp_path, monkeypatch):
        from app.automation import concept_extractor

        monkeypatch.setattr(concept_extractor, 'concepts_file', tmp_path / 'concepts.json')

        mock_search.return_value = [
            {
                'text': 'Some book content about AI.',
                'book_title': 'AI Book'
            }
        ]

        mock_response = MagicMock()
        mock_response.choices[0].message.content = '["AI", "ML", "Deep Learning"]'
        mock_client.chat.completions.create.return_value = mock_response

        from app.automation.concept_extractor import extract_concepts

        result = extract_concepts('AI Book')

        assert isinstance(result, list)
        assert 'AI' in result

    @patch("app.automation.concept_extractor.search", return_value = [])
    def test_returns_empty_when_no_chunks(self, mock_search, tmp_path, monkeypatch):
        from app.automation import concept_extractor

        monkeypatch.setattr(concept_extractor, 'concepts_file', tmp_path / 'concepts.json')

        from app.automation.concept_extractor import extract_concepts

        result = extract_concepts('Empty Book')

        assert result == []

    @patch("app.automation.concept_extractor.search")
    @patch("app.automation.concept_extractor.client")
    def test_handles_json_with_code_fences(self, mock_client, mock_search, tmp_path, monkeypatch):
        from app.automation import concept_extractor

        monkeypatch.setattr(concept_extractor, 'concepts_file', tmp_path / 'concepts.json')

        mock_search.return_value = [
            {
                'text': 'Some content.',
                'book_title': 'Book'
            }
        ]

        mock_response = MagicMock()
        mock_response.choices[0].message.content = '```json\n["Topic A", "Topic B"]\n```'
        mock_client.chat.completions.create.return_value = mock_response

        from app.automation.concept_extractor import extract_concepts

        result = extract_concepts('Book')

        assert result == ['Topic A', 'Topic B']

    # Malformed LLM response should not crash and should return empty list
    @patch("app.automation.concept_extractor.search")
    @patch("app.automation.concept_extractor.client")
    def test_returns_empty_on_bad_json(self, mock_client, mock_search, tmp_path, monkeypatch):
        from app.automation import concept_extractor

        monkeypatch.setattr(concept_extractor, 'concepts_file', tmp_path / 'concepts.json')
        mock_search.return_value = [
            {
                'text': 'Some content.',
                'book_title': 'Book'
            }
        ]

        mock_response = MagicMock()
        mock_response.choices[0].message.content = 'Here are the concepts: AI, ML, DL'
        mock_client.chat.completions.create.return_value = mock_response

        from app.automation.concept_extractor import extract_concepts

        result = extract_concepts('Book')

        assert result == []