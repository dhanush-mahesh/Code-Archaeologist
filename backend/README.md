# Code Archaeologist Backend

FastAPI backend for the Code Archaeologist Graph-RAG application.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install tree-sitter language grammars:
```bash
# This will be done automatically when needed
```

## Running the Server

```bash
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

## Testing

Run all tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=. --cov-report=html
```

Run property-based tests only:
```bash
pytest -k "test_property"
```

Test database setup:
```bash
python test_db_setup.py
```

## Project Structure

```
backend/
├── main.py              # FastAPI application entry point
├── database.py          # KùzuDB wrapper and schema
├── requirements.txt     # Python dependencies
├── pytest.ini          # Pytest configuration
├── test_db_setup.py    # Manual database test script
└── tests/
    ├── __init__.py
    └── test_database.py # Property-based tests for database
```

## Database Schema

### Node Types

- **File**: Represents a source code file
  - `id`: Unique identifier
  - `path`: File path
  - `language`: Programming language (python, javascript)

- **Class**: Represents a class definition
  - `id`: Unique identifier
  - `name`: Class name
  - `start_line`: Starting line number
  - `end_line`: Ending line number
  - `file_path`: Path to containing file

- **Function**: Represents a function/method definition
  - `id`: Unique identifier
  - `name`: Function name
  - `args`: Function arguments
  - `docstring`: Function documentation
  - `start_line`: Starting line number
  - `end_line`: Ending line number
  - `file_path`: Path to containing file

### Relationship Types

- **CONTAINS**: File → Class, File → Function
- **DEFINES**: Class → Function (methods)
- **CALLS**: Function → Function (function calls)

## API Endpoints

### Health Check
- `GET /` - API status
- `GET /health` - Health check

### Coming Soon
- `POST /ingest` - Ingest a repository
- `GET /graph` - Get the complete graph
- `POST /chat` - Query the codebase

## Development

### Adding New Features

1. Update the database schema in `database.py` if needed
2. Add corresponding tests in `tests/`
3. Implement the feature
4. Run tests to ensure everything works

### Property-Based Testing

We use Hypothesis for property-based testing. Each test runs 100 iterations with randomly generated data to ensure robustness.

Example property test:
```python
@settings(max_examples=100)
@given(file_node=file_node_strategy)
def test_property_file_node_round_trip(file_node):
    # Test that storing and retrieving a node preserves all attributes
    ...
```
