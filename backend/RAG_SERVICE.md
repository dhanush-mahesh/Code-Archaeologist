# RAG Service Documentation

## Overview

The RAG (Retrieval-Augmented Generation) Service enables natural language querying of the code graph using LangChain and Ollama. It translates user questions into Cypher queries, executes them against the KùzuDB graph database, and generates natural language responses.

## Architecture

```
User Question → RAG Service → Cypher Generation → Database Query → Response Generation → User Answer
                    ↓                                    ↓
                 Ollama LLM                         KùzuDB Graph
```

## Features

- **Natural Language to Cypher**: Converts questions like "What classes are in the codebase?" into Cypher queries
- **Few-Shot Learning**: Uses example queries to improve Cypher generation accuracy
- **Retry Logic**: Automatically retries failed queries with enhanced prompting
- **Node ID Extraction**: Identifies and returns relevant code entities from query results
- **Mock Mode**: Supports testing without Ollama for CI/CD environments

## Usage

### Basic Usage

```python
from database import KuzuDB
from rag_service import RAGService

# Initialize services
db = KuzuDB("./data/code_graph")
rag = RAGService(db, model_name="llama3")

# Process a query
result = rag.process_query("What functions are in the Calculator class?")
print(result.response)  # Natural language answer
print(result.node_ids)  # List of relevant node IDs
```

### Mock Mode (for Testing)

```python
# Use mock mode when Ollama is not available
rag = RAGService(db, mock_mode=True)
result = rag.process_query("What classes are in the codebase?")
```

## API

### RAGService Class

#### `__init__(db: KuzuDB, model_name: str = "llama3", mock_mode: bool = False)`

Initialize the RAG service.

**Parameters:**
- `db`: KuzuDB database instance
- `model_name`: Ollama model name (default: "llama3")
- `mock_mode`: If True, use mock responses instead of Ollama

#### `process_query(question: str, max_retries: int = 2) -> QueryResponse`

Process a natural language query end-to-end.

**Parameters:**
- `question`: Natural language question
- `max_retries`: Maximum retry attempts for invalid Cypher

**Returns:**
- `QueryResponse` with:
  - `response`: Natural language answer
  - `node_ids`: List of relevant node IDs
  - `cypher_query`: Generated Cypher query (optional)

#### `generate_cypher(question: str) -> str`

Generate a Cypher query from a natural language question.

#### `execute_cypher(cypher: str) -> Tuple[bool, List[Dict], str]`

Execute a Cypher query against the database.

**Returns:**
- Tuple of (success, results, error_message)

#### `extract_node_ids(results: List[Dict]) -> List[str]`

Extract node IDs from query results.

#### `generate_response(question: str, results: List[Dict]) -> str`

Generate a natural language response from query results.

## Example Queries

The RAG service can handle various types of questions:

### File Queries
- "What files are in the repository?"
- "Show me all Python files"

### Class Queries
- "What classes are in the codebase?"
- "Find the Calculator class"

### Function Queries
- "What functions are defined?"
- "What methods does the Calculator class have?"
- "Show me functions that call the add function"

### Relationship Queries
- "What files contain the Calculator class?"
- "What functions call the multiply method?"

## Few-Shot Examples

The service uses these example patterns to improve Cypher generation:

```cypher
# Find functions in a file
MATCH (f:File {path: 'calculator.py'})-[:CONTAINS_FUNCTION]->(fn:Function) 
RETURN fn.name, fn.args

# Find all classes
MATCH (c:Class) 
RETURN c.name, c.file_path

# Find function callers
MATCH (caller:Function)-[:CALLS]->(callee:Function {name: 'add'}) 
RETURN caller.name, caller.file_path

# Find class methods
MATCH (c:Class {name: 'Calculator'})-[:DEFINES]->(fn:Function) 
RETURN fn.name, fn.args, fn.docstring
```

## Error Handling

The RAG service includes robust error handling:

1. **Invalid Cypher**: Automatically retries with enhanced prompting
2. **Database Errors**: Returns descriptive error messages
3. **Empty Results**: Generates appropriate "not found" responses
4. **Ollama Unavailable**: Falls back to mock mode automatically

## Testing

The service includes comprehensive tests:

- **Unit Tests**: Test individual components (Cypher generation, execution, response generation)
- **Property Tests**: Verify universal properties across many inputs
- **Integration Tests**: Test end-to-end query processing

Run tests:
```bash
pytest tests/test_rag_service.py -v
```

## Requirements

- Python 3.10+
- KùzuDB
- LangChain
- Ollama (optional, falls back to mock mode)

## Configuration

### Ollama Setup

To use the full RAG functionality with Ollama:

1. Install Ollama: https://ollama.ai/
2. Pull the Llama 3 model:
   ```bash
   ollama pull llama3
   ```
3. Start Ollama service:
   ```bash
   ollama serve
   ```

### Mock Mode

When Ollama is not available, the service automatically falls back to mock mode, which:
- Generates simple Cypher queries based on keywords
- Returns basic responses from query results
- Suitable for testing and CI/CD environments

## Performance

- **Cypher Generation**: ~1-2 seconds with Ollama
- **Query Execution**: <100ms for typical queries
- **Response Generation**: ~1-2 seconds with Ollama
- **Total**: ~2-4 seconds per query with Ollama, <1 second in mock mode

## Limitations

- Currently supports Python and JavaScript codebases
- Cypher generation accuracy depends on LLM quality
- Complex queries may require multiple retries
- Mock mode provides simplified responses

## Future Enhancements

- Support for more programming languages
- Improved Cypher generation with fine-tuned models
- Caching for common queries
- Streaming responses for better UX
- Support for follow-up questions with context
