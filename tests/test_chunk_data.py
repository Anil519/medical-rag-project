import pytest
from src.chunk_data import load_and_chunk
import json
import os

def test_chunking(tmp_path):
    dummy_files = []
    for i in range(3):
        file = tmp_path / f"dummy{i}.json"
        with open(file, "w") as f:
            json.dump([{"title": "Test " * 100}], f)
        dummy_files.append(str(file))
    
    load_and_chunk(dummy_files)
    assert os.path.exists("data_chunks.json")
    with open("data_chunks.json", "r") as f:
        chunks = json.load(f)
    assert len(chunks) > 0