import pytest
from src.build_kg import extract_triples
from unittest.mock import patch

@patch('src.build_kg.extractor.invoke')
def test_extract_triples(mock_invoke):
    mock_invoke.return_value = "Aspirin, treats, headache;"
    text = "Aspirin treats headache."
    triples = extract_triples(text)
    assert len(triples) == 1
    assert triples[0] == ("Aspirin", " treats", " headache")