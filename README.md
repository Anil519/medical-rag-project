# Medical RAG Project
Run scripts in src/ sequentially. Use `uvicorn src.api:app --reload` for API.
Tests: `pytest tests/`

# CI Example (.github/workflows/test.yml)
name: Test Suite
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.12
      - name: Install deps
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/