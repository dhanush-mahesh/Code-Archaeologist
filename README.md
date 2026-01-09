# Code Archaeologist

A Graph-RAG (Retrieval Augmented Generation) application that transforms GitHub repositories into interactive, queryable knowledge graphs. Ask questions about any codebase in natural language and get answers grounded in visual graph representations.

## Overview

Code Archaeologist helps developers understand complex codebases by:
- **Parsing** repositories into structured knowledge graphs using tree-sitter
- **Visualizing** code relationships (files, classes, functions, and their connections)
- **Querying** codebases using natural language powered by local LLMs
- **Inspecting** source code with integrated Monaco editor

All processing happens **100% locally** - no cloud services, no data transmission, complete privacy.

## Features

### 🔍 Intelligent Code Analysis
- Automatic parsing of Python and JavaScript codebases
- Extraction of files, classes, functions, and their relationships
- Detection of function call graphs and dependencies

### 🗺️ Interactive Graph Visualization
- Full-screen React Flow canvas with zoom/pan controls
- Custom node styling (squares for files, circles for functions)
- Real-time highlighting of relevant code entities

### 💬 Natural Language Queries
- Ask questions like "How does authentication work?"
- LLM generates Cypher queries to retrieve relevant subgraphs
- Responses include interactive references to code entities

### 📝 Integrated Code Inspector
- Click any node to view its source code
- Syntax highlighting via Monaco Editor
- Automatic line range highlighting for functions and classes

## Tech Stack

### Backend
- **FastAPI** - High-performance Python web framework
- **KùzuDB** - Embedded graph database for code relationships
- **Tree-sitter** - Robust code parsing with AST generation
- **LangChain** - LLM orchestration and graph query generation
- **Ollama** - Local LLM inference (Llama-3-8b)
- **HuggingFace** - Local embeddings generation

### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **Shadcn/UI** - Beautiful component library
- **React Flow** - Interactive graph visualization
- **Monaco Editor** - VS Code-powered code viewing
- **Lucide React** - Icon library

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ React Flow   │  │ Chat Sidebar │  │    Code      │      │
│  │   Canvas     │  │              │  │  Inspector   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                    ┌───────┴───────┐
                    │   FastAPI     │
                    │   Backend     │
                    └───────┬───────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼────────┐  ┌──────▼──────┐  ┌────────▼────────┐
│   Tree-sitter  │  │   KùzuDB    │  │   LangChain     │
│     Parser     │  │  Graph DB   │  │  + Ollama LLM   │
└────────────────┘  └─────────────┘  └─────────────────┘
```

## Getting Started

### Prerequisites

- **Python 3.10+** with pip
- **Node.js 18+** with npm/yarn
- **Ollama** installed locally ([installation guide](https://ollama.ai))
- **Git** for repository cloning

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/dhanush-mahesh/Code-Archaeologist.git
   cd Code-Archaeologist
   ```

2. **Set up the backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set up the frontend**
   ```bash
   cd frontend
   npm install
   ```

4. **Install Ollama and pull the model**
   ```bash
   ollama pull llama3:8b
   ```

### Running the Application

1. **Start the backend server**
   ```bash
   cd backend
   uvicorn main:app --reload --port 8000
   ```

2. **Start the frontend development server**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Open your browser**
   Navigate to `http://localhost:3000`

## Usage

### 1. Ingest a Repository
- Enter a GitHub repository URL in the ingestion interface
- The system will clone and parse the repository
- Wait for the parsing to complete

### 2. Explore the Graph
- View the complete codebase as an interactive graph
- Zoom and pan to navigate large codebases
- Different node shapes represent different entity types

### 3. Ask Questions
- Use the chat sidebar to ask questions in natural language
- Examples:
  - "How does the authentication system work?"
  - "What functions call the database?"
  - "Show me the error handling logic"
- Click on referenced nodes to jump to them in the graph

### 4. Inspect Code
- Click any node to view its source code
- The Monaco editor shows syntax-highlighted code
- Function and class definitions are automatically highlighted

## API Endpoints

### `POST /ingest`
Ingest a GitHub repository into the knowledge graph.

**Request:**
```json
{
  "repo_url": "https://github.com/username/repo"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Repository ingested successfully",
  "job_id": "abc123"
}
```

### `GET /graph`
Retrieve the complete knowledge graph.

**Response:**
```json
{
  "nodes": [
    {
      "id": "file_1",
      "type": "file",
      "data": { "label": "main.py", "path": "src/main.py" },
      "position": { "x": 0, "y": 0 }
    }
  ],
  "edges": [
    {
      "id": "edge_1",
      "source": "file_1",
      "target": "func_1",
      "type": "CONTAINS"
    }
  ]
}
```

### `POST /chat`
Query the codebase using natural language.

**Request:**
```json
{
  "prompt": "How does authentication work?"
}
```

**Response:**
```json
{
  "response": "The authentication system uses JWT tokens...",
  "node_ids": ["func_auth_login", "func_verify_token"]
}
```

## Project Structure

```
Code-Archaeologist/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── ingestion.py         # Repository ingestion service
│   ├── parser.py            # Tree-sitter parsing logic
│   ├── rag.py               # RAG service with LangChain
│   ├── database.py          # KùzuDB wrapper
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── app/
│   │   ├── page.tsx         # Main application page
│   │   └── layout.tsx       # Root layout
│   ├── components/
│   │   ├── GraphCanvas.tsx  # React Flow visualization
│   │   ├── ChatSidebar.tsx  # Chat interface
│   │   └── CodeInspector.tsx # Code viewer
│   ├── lib/
│   │   └── api.ts           # API client utilities
│   └── package.json         # Node dependencies
├── docs/
│   ├── requirements.md      # Detailed requirements
│   ├── design.md            # System design document
│   └── tasks.md             # Implementation plan
└── README.md
```

## Development

### Running Tests

**Backend tests:**
```bash
cd backend
pytest
```

**Frontend tests:**
```bash
cd frontend
npm test
```

### Property-Based Testing

The project uses property-based testing to ensure correctness:
- **Backend**: Hypothesis for Python
- **Frontend**: fast-check for TypeScript

All property tests run with a minimum of 100 iterations.

## Roadmap

- [ ] Support for additional languages (TypeScript, Java, Go, Rust)
- [ ] Advanced graph layout algorithms
- [ ] Semantic search across codebases
- [ ] Code change impact analysis
- [ ] Export graph visualizations
- [ ] Multi-repository analysis
- [ ] Custom query templates

## Contributing

Contributions are welcome! Please read the [design document](docs/design.md) and [requirements](docs/requirements.md) before submitting PRs.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Tree-sitter](https://tree-sitter.github.io/) for robust code parsing
- [KùzuDB](https://kuzudb.com/) for embedded graph database
- [LangChain](https://langchain.com/) for LLM orchestration
- [Ollama](https://ollama.ai) for local LLM inference
- [React Flow](https://reactflow.dev/) for graph visualization

## Contact

Dhanush Mahesh - [@dhanush-mahesh](https://github.com/dhanush-mahesh)

Project Link: [https://github.com/dhanush-mahesh/Code-Archaeologist](https://github.com/dhanush-mahesh/Code-Archaeologist)
